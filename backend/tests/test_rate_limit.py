from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


def _build_limited_app() -> FastAPI:
    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/ping")
    @limiter.limit("3/minute")
    def ping(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_requests_within_limit_succeed():
    client = TestClient(_build_limited_app())
    for _ in range(3):
        response = client.get("/ping")
        assert response.status_code == 200


def test_requests_beyond_limit_are_rejected():
    client = TestClient(_build_limited_app())
    for _ in range(3):
        assert client.get("/ping").status_code == 200

    response = client.get("/ping")
    assert response.status_code == 429


def test_auth_endpoints_are_not_rate_limited_in_test_suite(client):
    for _ in range(6):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong", "tenant_slug": "nope"},
        )
        assert response.status_code == 401
