from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_PATH = BASE_DIR / "scripts"
REDIS_SCRIPTS_PATH = SCRIPTS_PATH / "redis"


class EmptyBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow", env_file=".env")


class AppSettings(EmptyBaseSettings):
    SERVICE_NAME: str = "otus-social"
    ROOT_PATH: str = ""
    SERVICE_DESCRIPTION: str = "Otus Homework for social network"
    STAND: str = "dev"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOW_ORIGINS: str | None = None
    ENABLE_JSON_LOG: bool = True
    LOG_DEV: bool = False

    @property
    def allow_origins_list(self) -> list[str]:
        return self.ALLOW_ORIGINS.split(",") if self.ALLOW_ORIGINS else []


class AuthSettings(EmptyBaseSettings):
    JWT_PUB_KEY: str = "secret"
    JWT_PRIVATE_KEY: str = "secret"
    JWT_ALG: Literal["HS256", "RS256", "ES256"] = "HS256"
    JWT_ACCESS_EXP_SECONDS: int = 60 * 60
    JWT_REFRESH_EXP_SECONDS: int = 7 * 24 * 60 * 60
    AUTH_TOKEN_TYPE: str = "Bearer"
    AUTH_HEADER_KEY: str = "Authorization"


class RedisSettings(EmptyBaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_SSL: bool = False
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = ""
    REDIS_POOL_MAX_SIZE: int = 50
    REDIS_TIMEOUT_SEC: int = 30
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_DEFAULT_SETTINGS_TTL: int = 24 * 60 * 60


class KafkaSettings(EmptyBaseSettings):
    KAFKA_BROKERS: str = "kafka:9093"
    KAFKA_GROUP_ID: str = "otus"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SASL_PLAIN_USERNAME: str | None = None
    KAFKA_SASL_PLAIN_PASSWORD: str | None = None
    KAFKA_MAX_REQUEST_SIZE_BYTES: int = 1 * 1024 * 1024
    KAFKA_MAX_POOL_INTERVAL: int = 30000  # 0.5 min

    KAFKA_CUD_USER_EVENT_TOPIC: str = "cud.user"


class DbSettings(EmptyBaseSettings):
    DB_DRIVER: str = "postgresql+asyncpg"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "app_pswd"
    DB_DATABASE: str = "chats"

    DB_POOL_SIZE: int = 15  # pool
    DB_MAX_OVERFLOW: int = 5
    DB_TIMEOUT: float = 30.0
    DB_ECHO: bool = False
    DB_POOL_RECYCLE: int = 3600
    DB_ENABLE_PG_BOUNCER: bool = False

    @property
    def db_dsn(self) -> URL:
        return URL.create(self.DB_DRIVER, self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_DATABASE)

    @property
    def db_url(self) -> URL:
        return URL.create(self.DB_DRIVER, self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT)


app_settings = AppSettings()
auth_settings = AuthSettings()
redis_settings = RedisSettings()
db_settings = DbSettings()
kafka_settings = KafkaSettings()
