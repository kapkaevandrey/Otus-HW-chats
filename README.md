# Otus Chat Service

Микросервис диалогов: отправка и чтение прямых сообщений между пользователями.

- **REST API** — `/api/v1/dialog/{user_id}/send|list`
- **PostgreSQL** — локальный inbox пользователей (синхронизация из монолита)
- **Valkey/Redis** — хранение диалогов и сообщений
- **Kafka** — топик `cud.user` для CUD-событий профилей из outbox монолита

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

## Синхронизация пользователей

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

## Разработка

```shell
make install      # uv sync
make pytest       # тесты в docker
make check_code   # ruff + mypy
make help
```

## Порты по умолчанию

Chat-service использует **8001**, **5433**, **6380**, чтобы не конфликтовать с монолитом на 8000/5432/6379.
