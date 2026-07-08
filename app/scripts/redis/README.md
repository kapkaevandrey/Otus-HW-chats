# Redis Procedures

## `send_message_to_user.lua`

This script implements the `send_message_to_user` domain operation in one Redis-side procedure call.

## What it does

1. Gets an existing direct conversation by key or creates it from the passed JSON candidate.
2. Adds sender and receiver to the participants set.
3. Adds message id into the conversation sorted set by `sent_at` score.
4. Stores the message payload by `message:{id}` key.
5. Appends a domain event into the Redis Stream outbox (`XADD`).

Steps 1-5 run atomically inside one Lua script.

The script does not compute business values itself; it only uses keys and values passed from application code.

## KEYS

1. `direct_conversation_key` - `direct:conversation:{low_id}:{high_id}`
2. `participants_key` - `participants:{conversation_id}`
3. `messages_key` - `messages:{conversation_id}`
4. `message_key` - `message:{message_id}`
5. `outbox_stream_key` - `outbox:dialog.events`

## ARGV

1. `conversation_json_candidate` - serialized `ConversationDto`
2. `sender_id`
3. `receiver_id`
4. `message_member` - message id placed into `ZSET`
5. `sent_at_score` - timestamp score for `ZADD`
6. `message_json` - serialized `MessageCreateSchema`
7. `outbox_event_json` - serialized `MessageSentOutboxEventSchema`

## Return value

Array with:

1. `final_conversation_json`
2. `added_participants_count`
3. `zadd_result`
4. `outbox_entry_id`

## `get_dialog_with_users.lua`

Reads dialog messages for one conversation from Redis and appends `dialog.read` into the outbox stream atomically.

## What it does

1. Reads message ids from `ZSET` using pagination params (`offset`, `limit`) and `order`.
2. Fetches message payloads via one `MGET` when ids exist.
3. Appends `dialog.read` outbox event via `XADD` even for an empty dialog.

Steps 1-3 run atomically inside one Lua script.

## KEYS

1. `messages_key` - `messages:{conversation_id}`
2. `message_key_prefix` - `message:`
3. `outbox_stream_key` - `outbox:dialog.events`

## ARGV

1. `offset`
2. `limit`
3. `order` - `desc` or `asc`
4. `outbox_event_json` - serialized `DialogReadOutboxEventSchema`

## Return value

Array of message JSON strings in requested order.
