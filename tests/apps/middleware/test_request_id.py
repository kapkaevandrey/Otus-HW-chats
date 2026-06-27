from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.apps.middleware.request_id import RequestIdMiddleware
from app.core.request_context import REQUEST_ID_HEADER


def _build_app() -> FastAPI:
    application = FastAPI()

    @application.get("/ping")
    async def ping():
        from app.core.request_context import get_request_id

        return {"request_id": get_request_id()}

    application.add_middleware(RequestIdMiddleware)
    return application


async def test_request_id_is_generated_when_missing():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER) == response.json()["request_id"]


async def test_request_id_is_propagated_from_client():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ping", headers={REQUEST_ID_HEADER: "trace-777"})

    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER) == "trace-777"
    assert response.json()["request_id"] == "trace-777"
