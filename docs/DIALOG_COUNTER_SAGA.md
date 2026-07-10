# Chat-service как источник событий для сервиса счётчиков (SAGA)

Этот документ описывает **продюсер-сторону** SAGA счётчиков непрочитанных сообщений. Потребитель и модель счётчиков — в репозитории [Otus-HW-counter-service](https://github.com/kapkaevandrey/Otus-HW-counter-service) (`docs/REVIEW.md`).

---

## 1. Роль chat-service

Chat-service владеет диалогами и является **единственным источником правды** о событиях, влияющих на счётчики:

| Операция API | Событие | Смысл |
|--------------|---------|-------|
| `POST /api/v1/dialog/{B}/send` | `message.sent` | пользователь A отправил сообщение B → у B +1 непрочитанное от A |
| `GET /api/v1/dialog/{A}/list` | `dialog.read` | пользователь B открыл диалог с A → непрочитанные B от A обнуляются |

counter-service подписан на эти события и поддерживает счётчик `unread:{user}` в своём Redis. Прямых синхронных вызовов между сервисами нет — только асинхронные события через Kafka (choreography SAGA, eventual consistency).

---

## 2. Transactional outbox поверх Redis Stream

Диалоги хранятся в Redis. Чтобы событие не потерялось и не разошлось с реальным состоянием диалога, оно записывается **в той же атомарной Lua-операции**, что и изменение диалога:

| Lua-скрипт | Что делает атомарно |
|------------|---------------------|
| `app/scripts/redis/send_message_to_user.lua` | пишет сообщение в диалог **и** `XADD` события `message.sent` в outbox |
| `app/scripts/redis/get_dialog_with_users.lua` | читает сообщения диалога **и** `XADD` события `dialog.read` в outbox |

Outbox — один Redis Stream: `outbox:dialog.events`. Так как Lua в Redis выполняется атомарно и однопоточно, не бывает состояния «диалог изменён, событие не записано» и наоборот.

---

## 3. Relay-worker

`app/apps/workers/dialog.py` → `DialogOutboxRelayWorker` — фоновый воркер, публикующий события из outbox в Kafka. Запускается в `app/server.py` рядом с `UserConsumer`.

Цикл работы:

1. `XAUTOCLAIM` — забрать «зависшие» сообщения от упавших воркеров (min-idle-time) и допубликовать.
2. `XREADGROUP` — прочитать новые сообщения группой (`>`).
3. Для каждого события:
   - идемпотентность: если `relay:sent:{event_id}` уже есть — только `XACK`, publish пропускается;
   - иначе `send_message` в топик `social.dialog.messages`, затем `SET relay:sent:{event_id}` (TTL) и `XACK`.

Это даёт доставку **at-least-once** с защитой от дублей на стороне relay; окончательная идемпотентность — в counter-service по `event_id`.

---

## 4. Ключ партиционирования Kafka — защита от гонок

Один и тот же счётчик `unread:{B}[A]` меняют **два** типа событий: `message.sent` (A→B) и `dialog.read` (B прочитал A). При параллельной обработке возможна гонка (инкремент и обнуление в неверном порядке).

Решение — партиционировать по **владельцу счётчика** (тому, чей `unread` мутируется):

```python
# app/apps/workers/dialog.py
def _counter_owner_id(event):
    if event["type"] == "message.sent":
        return str(event["recipient_id"])   # B
    if event["type"] == "dialog.read":
        return str(event["user_id"])         # B
```

Для сценария A→B оба события дают **один и тот же UUID (B)** → одна партиция Kafka → строго последовательная обработка одним consumer → гонки исключены.

Почему не `conversation_id`: ключ должен совпадать с **агрегатом, чьё состояние меняется** (`unread:{user}`). Владелец счётчика корректен и в 1-на-1, и обобщается на групповые чаты / «прочитать всё», не создавая горячих партиций на активный диалог.

---

## 5. Схема

```
POST /dialog/{B}/send                 GET /dialog/{A}/list
        │                                     │
        ▼ (Lua, атомарно)                     ▼ (Lua, атомарно)
  сообщение + XADD ──┐               чтение + XADD ──┐
                     ▼                                ▼
            Redis Stream: outbox:dialog.events
                     │
                     ▼
          DialogOutboxRelayWorker
        XAUTOCLAIM / XREADGROUP / XACK
        idem: relay:sent:{event_id}
                     │ key = counter_owner_id(event)
                     ▼
      Kafka topic: social.dialog.messages
                     │
                     ▼
             counter-service (consumer → unread:{user})
```

---

## 6. Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `app/scripts/redis/send_message_to_user.lua` | запись сообщения + outbox `message.sent` |
| `app/scripts/redis/get_dialog_with_users.lua` | чтение диалога + outbox `dialog.read` |
| `app/schemas/dto/dialog_outbox.py` | схемы событий `MessageSentOutboxEventSchema`, `DialogReadOutboxEventSchema` |
| `app/apps/workers/dialog.py` | relay-worker, партиционный ключ |
| `app/server.py` | запуск relay-воркера в lifespan |
