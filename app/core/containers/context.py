from logging import Logger, getLogger

from app.config import app_settings, auth_settings, db_settings, kafka_settings, redis_settings
from app.core.clients import RedisClient, SQLAlchemyAsyncPgClient
from app.core.repositories import UnitOfWork

from .cfg import Config


class Context:
    def __init__(
        self,
        redis_client: RedisClient,
        db_client: SQLAlchemyAsyncPgClient,
        cfg: Config,
        logger: Logger | None = None,
    ) -> None:
        self._redis_client = redis_client
        self._db_client = db_client
        self._logger = logger or getLogger(__name__)
        self._cfg = cfg

    @property
    def redis_client(self) -> RedisClient:
        return self._redis_client

    @property
    def db_client(self) -> SQLAlchemyAsyncPgClient:
        return self._db_client

    @property
    def uow(self):
        return UnitOfWork(db_client=self._db_client)

    @property
    def cfg(self) -> Config:
        return self._cfg

    @property
    def logger(self) -> Logger:
        return self._logger

    async def start_clients(self):
        """Start all clients if that need"""
        await self.db_client.start_client()

    async def stop_clients(self):
        """Stop all clients if that need"""
        await self.db_client.stop_client()


context = Context(
    redis_client=RedisClient.from_settings(redis_settings),
    cfg=Config(app=app_settings, redis=redis_settings, auth=auth_settings, db=db_settings, kafka=kafka_settings),
    db_client=SQLAlchemyAsyncPgClient.from_settings(db_settings),
    logger=getLogger(__name__),
)


def get_context() -> Context:
    return context
