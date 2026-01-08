from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def _register_and_get_token(client: TestClient) -> str:
    payload = {
        "username": "mcp-user",
        "email": "mcp@example.com",
        "password": "password123",
        "session_id": str(uuid4()),
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["tokens"]["access_token"]


def test_mcp_servers_list(client: TestClient) -> None:
    access_token = _register_and_get_token(client)

    response = client.get(
        "/mcp/servers",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["servers"], list)
    assert any(server["name"] == "echo" for server in body["servers"])
