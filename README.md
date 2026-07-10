# Otus Chat Service

Микросервис диалогов: отправка и чтение прямых сообщений между пользователями.

- **REST API** — `/api/v1/dialog/{user_id}/send|list`
- **PostgreSQL** — локальный inbox пользователей (синхронизация из монолита)
- **Valkey/Redis** — хранение диалогов и сообщений + **outbox событий диалогов** (Redis Stream)
- **Kafka**:
  - топик `cud.user` — CUD-события профилей из outbox монолита (**вход**)
  - топик `social.dialog.messages` — события диалогов `message.sent` / `dialog.read` для сервиса счётчиков (**выход**)

Chat-service — **источник событий** для [counter-service](https://github.com/kapkaevandrey/Otus-HW-counter-service) (сервис счётчиков непрочитанных), реализованного по паттерну **SAGA**. Описание этой части — в [docs/DIALOG_COUNTER_SAGA.md](docs/DIALOG_COUNTER_SAGA.md).

## Для проверяющего

Полная инструкция в репозитории **Otus-HW_01**: `docs/REVIEW.md` (отчёт + запуск + сценарии проверки).

Скопируйте `.env.example` → `.env` перед локальным запуском app.

## Быстрый старт

```shell
make run
```

После запуска:

| Сервис | URL |
|--------|-----|
| API + Swagger | http://127.0.0.1:8001/docs |
| Kafka UI | http://127.0.0.1:8082 |
| PostgreSQL | localhost:5433 |
| Valkey | localhost:6380 |

Остановка:

```shell
make down
```

## Запуск вместе с монолитом

1. Поднять chat-service (этот репозиторий):

```shell
make run
```

2. В монолите (`Otus-HW_01`) указать URL chat-service и общий Kafka:

```env
CHAT_SERVICE_URL=http://host.docker.internal:8001
KAFKA_BROKERS=localhost:9092
```

3. Убедиться, что монолит публикует события пользователей в топик `cud.user` через outbox.

4. JWT-ключи должны совпадать (`JWT_PUB_KEY` / `JWT_PRIVATE_KEY` в `dev.env`).

### Docker-сеть (альтернатива)

```shell
docker network create otus-net
```

В обоих `docker-compose.yaml`:

```yaml
networks:
  default:
    external: true
    name: otus-net
```

Тогда в монолите: `CHAT_SERVICE_URL=http://app:8001` (имя сервиса chat-service).

## Синхронизация пользователей (вход)

Монолит пишет CUD-события в outbox → Kafka → chat-service `UserConsumer`.

Формат сообщения:

```json
{
  "action": "create",
  "data": {
    "id": "uuid",
    "first_name": "...",
    "second_name": "...",
    "birthdate": "1990-01-01",
    "biography": null,
    "city": null
  }
}
```

Действия: `create`, `update`, `delete`.

## API диалогов

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/dialog/{user_id}/send` | Bearer JWT |
| GET | `/api/v1/dialog/{user_id}/list` | Bearer JWT |

## События диалогов → сервис счётчиков (SAGA)

При отправке и чтении сообщений chat-service публикует события в Kafka, из которых counter-service строит счётчики непрочитанных. Используется **transactional outbox** поверх Redis Stream + relay-worker.

| Операция API | Событие | Партиционный ключ Kafka |
|--------------|---------|-------------------------|
| `POST /dialog/{B}/send` | `message.sent` | `recipient_id` (B) |
| `GET /dialog/{A}/list` | `dialog.read` | `user_id` (читающий) |

- Событие пишется в Redis Stream `outbox:dialog.events` **в той же атомарной Lua-операции**, что и само изменение диалога (нет потери событий).
- `DialogOutboxRelayWorker` читает stream (`XREADGROUP` / `XAUTOCLAIM` / `XACK`), публикует в топик `social.dialog.messages`, идемпотентность по `relay:sent:{event_id}`.
- Ключ партиционирования — **владелец счётчика** (тот, чей `unread` меняется), чтобы `message.sent` и `dialog.read` одного пользователя попадали в одну партицию и обрабатывались по порядку (защита от гонок).

Подробнее: [docs/DIALOG_COUNTER_SAGA.md](docs/DIALOG_COUNTER_SAGA.md).

## Разработка

```shell
make install      # uv sync
make pytest       # тесты в docker
make check_code   # ruff + mypy
make help
```

## Порты по умолчанию

Chat-service использует **8001**, **5433**, **6380**, чтобы не конфликтовать с монолитом на 8000/5432/6379.
