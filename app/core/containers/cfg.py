from app.config import AppSettings, AuthSettings, DbSettings, KafkaSettings, RedisSettings


class Config:
    def __init__(
        self, app: AppSettings, redis: RedisSettings, auth: AuthSettings, db: DbSettings, kafka: KafkaSettings
    ) -> None:
        self._app = app
        self._redis = redis
        self._auth_settings = auth
        self._db = db
        self._kafka = kafka

    @property
    def app(self) -> AppSettings:
        return self._app

    @property
    def kafka(self) -> KafkaSettings:
        return self._kafka

    @property
    def redis(self) -> RedisSettings:
        return self._redis

    @property
    def auth_settings(self) -> AuthSettings:
        return self._auth_settings

    @property
    def db(self) -> DbSettings:
        return self._db
