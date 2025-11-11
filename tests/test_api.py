from uuid import uuid4

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def _register_and_get_token(client: TestClient) -> str:
    payload = {
        "username": "hello-user",
        "email": "hello@example.com",
        "password": "password123",
        "session_id": str(uuid4()),
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    return data["tokens"]["access_token"]


def test_hello_endpoint(client: TestClient) -> None:
    access_token = _register_and_get_token(client)

    response = client.get(
        "/hello",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"message": "Hello, FastAPI!"}


def test_hello_requires_auth(client: TestClient) -> None:
    response = client.get("/hello")

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "인증이 필요합니다."
