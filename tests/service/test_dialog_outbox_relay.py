import asyncio
from uuid import uuid4

from app.apps.workers import DialogOutboxRelayWorker
from app.config import kafka_settings, redis_settings
from app.core.enums import DialogEventType
from app.schemas.dto import DialogReadOutboxEventSchema, MessageSentOutboxEventSchema


async def _create_consumer_group(redis, stream_name: str, group_name: str) -> None:
    try:
        await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except Exception as error:
        if "BUSYGROUP" not in str(error):
            raise


async def test_dialog_outbox_relay_publishes_event_and_acks(context, kafka_producer_mock_client, monkeypatch):
    monkeypatch.setattr(redis_settings, "REDIS_DIALOG_OUTBOX_CONSUMER_NAME", "test-worker")
    monkeypatch.setattr(redis_settings, "REDIS_DIALOG_OUTBOX_BLOCK_MS", 1)

    relay = DialogOutboxRelayWorker(context)
    redis = context.redis_client
    stream_name = redis_settings.REDIS_DIALOG_OUTBOX_STREAM
    group_name = redis_settings.REDIS_DIALOG_OUTBOX_CONSUMER_GROUP
    topic_name = kafka_settings.KAFKA_DIALOG_EVENTS_TOPIC
    await _create_consumer_group(redis, stream_name, group_name)

    event = MessageSentOutboxEventSchema(
        recipient_id=uuid4(),
        sender_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
    )
    entry_id = await redis.xadd(stream_name, {"payload": event.model_dump_json()})

    await relay.run(once=True)

    assert len(kafka_producer_mock_client.messages[topic_name]) == 1
    key, value = kafka_producer_mock_client.messages[topic_name][0]
    assert key == str(event.recipient_id).encode()
    assert value["type"] == DialogEventType.MESSAGE_SENT
    assert value["event_id"] == str(event.event_id)

    pending = await redis.xpending_range(stream_name, group_name, "-", "+", 10)
    assert pending == []

    relay_sent_key = f"{DialogOutboxRelayWorker.RELAY_SENT_KEY_PREFIX}{event.event_id}"
    assert await redis.exists(relay_sent_key) == 1

    entries = await redis.xrange(stream_name, entry_id, entry_id)
    assert len(entries) == 1


async def test_dialog_outbox_relay_skips_duplicate_kafka_publish_on_reclaim(
    context,
    kafka_producer_mock_client,
    monkeypatch,
):
    monkeypatch.setattr(redis_settings, "REDIS_DIALOG_OUTBOX_CONSUMER_NAME", "test-worker")
    monkeypatch.setattr(redis_settings, "REDIS_DIALOG_OUTBOX_BLOCK_MS", 1)
    monkeypatch.setattr(redis_settings, "REDIS_DIALOG_OUTBOX_RECLAIM_IDLE_MS", 1)

    relay = DialogOutboxRelayWorker(context)
    redis = context.redis_client
    stream_name = redis_settings.REDIS_DIALOG_OUTBOX_STREAM
    group_name = redis_settings.REDIS_DIALOG_OUTBOX_CONSUMER_GROUP
    topic_name = kafka_settings.KAFKA_DIALOG_EVENTS_TOPIC
    await _create_consumer_group(redis, stream_name, group_name)

    event = MessageSentOutboxEventSchema(
        recipient_id=uuid4(),
        sender_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
    )
    await redis.xadd(stream_name, {"payload": event.model_dump_json()})
    relay_sent_key = f"{DialogOutboxRelayWorker.RELAY_SENT_KEY_PREFIX}{event.event_id}"
    await redis.set(relay_sent_key, "1")

    await redis.xreadgroup(
        groupname=group_name,
        consumername="other-worker",
        streams={stream_name: ">"},
        count=1,
    )

    await asyncio.sleep(0.01)
    await relay.run(once=True)

    assert kafka_producer_mock_client.messages[topic_name] == []

    pending = await redis.xpending_range(stream_name, group_name, "-", "+", 10)
    assert pending == []


def test_counter_owner_partition_key_matches_for_sent_and_read():
    user_b = uuid4()
    user_a = uuid4()

    sent_event = MessageSentOutboxEventSchema(
        recipient_id=user_b,
        sender_id=user_a,
        conversation_id=uuid4(),
        message_id=uuid4(),
    ).model_dump(mode="json")
    read_event = DialogReadOutboxEventSchema(
        user_id=user_b,
        peer_id=user_a,
        conversation_id=sent_event["conversation_id"],
    ).model_dump(mode="json")

    sent_key = DialogOutboxRelayWorker._counter_owner_id(sent_event)
    read_key = DialogOutboxRelayWorker._counter_owner_id(read_event)

    assert sent_key == read_key == str(user_b)
