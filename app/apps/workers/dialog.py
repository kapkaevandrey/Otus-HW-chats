from __future__ import annotations

import json
import logging
import os
import socket
from typing import Any, cast

from redis.exceptions import ResponseError

from app.core.containers import Context


class DialogOutboxRelayWorker:
    RELAY_SENT_KEY_PREFIX = "relay:sent:"
    _StreamEntries = list[tuple[str, dict[Any, Any]]]

    def __init__(self, context: Context, logger: logging.Logger | None = None) -> None:
        self.context = context
        self.logger = logger or logging.getLogger(__name__)

    async def run(self, once: bool = False) -> None:
        self.logger.info("%s: Worker started", self.__class__.__name__)
        await self._ensure_consumer_group()
        try:
            while True:
                await self._reclaim_and_publish()
                await self._read_new_and_publish()
                if once:
                    break
        finally:
            self.logger.info("%s: Worker stopped", self.__class__.__name__)

    async def _ensure_consumer_group(self) -> None:
        try:
            await self.context.redis_client.xgroup_create(
                self._stream_name,
                self._consumer_group,
                id="0",
                mkstream=True,
            )
            self.logger.info("Created redis stream consumer group %s for %s", self._consumer_group, self._stream_name)
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise

    async def _reclaim_and_publish(self) -> None:
        _, entries, _ = await self.context.redis_client.xautoclaim(
            name=self._stream_name,
            groupname=self._consumer_group,
            consumername=self._consumer_name,
            min_idle_time=self._reclaim_idle_ms,
            start_id="0-0",
            count=self._read_count,
        )
        await self._publish_entries(cast(DialogOutboxRelayWorker._StreamEntries, entries))

    async def _read_new_and_publish(self) -> None:
        response = await self.context.redis_client.xreadgroup(
            groupname=self._consumer_group,
            consumername=self._consumer_name,
            streams={self._stream_name: ">"},
            count=self._read_count,
            block=self._block_ms,
        )
        if not response:
            return

        for stream_chunk in cast(list[tuple[str, DialogOutboxRelayWorker._StreamEntries]], response):
            await self._publish_entries(stream_chunk[1])

    async def _publish_entries(self, entries: list[tuple[str, dict[Any, Any]]]) -> None:
        for entry_id, fields in entries:
            payload = self._extract_payload(fields)
            event = json.loads(payload)
            event_id = str(event["event_id"])
            relay_sent_key = f"{self.RELAY_SENT_KEY_PREFIX}{event_id}"

            if await self.context.redis_client.exists(relay_sent_key):
                await self.context.redis_client.xack(self._stream_name, self._consumer_group, entry_id)
                self.logger.debug("Skip duplicate relay for event_id=%s entry_id=%s", event_id, entry_id)
                continue

            await self.context.kafka_producer.send_message(
                key=self._kafka_partition_key(event),
                value=event,
                topic=self._topic_name,
                wait_acc=True,
            )
            await self.context.redis_client.set(relay_sent_key, "1", ex=self._relay_sent_ttl_sec)
            await self.context.redis_client.xack(self._stream_name, self._consumer_group, entry_id)
            self.logger.info(
                "Relayed outbox event event_id=%s entry_id=%s to topic=%s",
                event_id,
                entry_id,
                self._topic_name,
            )

    @property
    def _stream_name(self) -> str:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_STREAM

    @property
    def _topic_name(self) -> str:
        return self.context.cfg.kafka.KAFKA_DIALOG_EVENTS_TOPIC

    @property
    def _consumer_group(self) -> str:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_CONSUMER_GROUP

    @property
    def _consumer_name(self) -> str:
        if consumer_name := self.context.cfg.redis.REDIS_DIALOG_OUTBOX_CONSUMER_NAME:
            return consumer_name
        return f"{socket.gethostname()}-{os.getpid()}"

    @property
    def _reclaim_idle_ms(self) -> int:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_RECLAIM_IDLE_MS

    @property
    def _read_count(self) -> int:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_READ_COUNT

    @property
    def _block_ms(self) -> int:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_BLOCK_MS

    @property
    def _relay_sent_ttl_sec(self) -> int:
        return self.context.cfg.redis.REDIS_DIALOG_OUTBOX_RELAY_SENT_TTL_SEC

    @staticmethod
    def _kafka_partition_key(event: dict[str, Any]) -> str:
        return DialogOutboxRelayWorker._counter_owner_id(event)

    @staticmethod
    def _counter_owner_id(event: dict[str, Any]) -> str:
        """Kafka key for all events that mutate unread:{owner_id}.

        message.sent  -> recipient_id (who receives the message)
        dialog.read   -> user_id      (who opened the dialog)

        For the same counter both resolve to the same UUID, e.g. A sends to B:
        sent uses recipient_id=B, read uses user_id=B -> one partition -> ordered processing.
        """
        event_type = event.get("type")
        if event_type == "message.sent":
            return str(event["recipient_id"])
        if event_type == "dialog.read":
            return str(event["user_id"])
        return str(event["event_id"])

    @staticmethod
    def _extract_payload(fields: dict[Any, Any]) -> str:
        raw_payload = fields.get("payload") or fields.get(b"payload")
        if raw_payload is None:
            raise ValueError("Outbox stream entry has no payload field")
        if isinstance(raw_payload, bytes):
            return raw_payload.decode("utf-8")
        return str(raw_payload)
