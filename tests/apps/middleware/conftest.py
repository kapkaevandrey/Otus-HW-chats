from collections.abc import AsyncGenerator
from typing import Any

import pytest


@pytest.fixture(scope="session", autouse=True)
async def load_redis_scripts() -> AsyncGenerator[None, Any]:
    yield


@pytest.fixture(scope="session", autouse=True)
async def init_test_db() -> AsyncGenerator[None, Any]:
    yield


@pytest.fixture(scope="function", autouse=True)
async def create_tables() -> AsyncGenerator[None, Any]:
    yield
