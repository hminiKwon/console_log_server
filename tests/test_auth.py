from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from console_log_server.core.settings import get_settings
from console_log_server.utils.token import decode_token


def test_register_and_login_flow(client: TestClient) -> None:
    session_id = str(uuid4())
    register_payload = {
        "username": "tester",
        "email": "tester@example.com",
        "password": "password123",
        "session_id": session_id,
    }

    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["username"] == register_payload["username"]
    assert body["user"]["email"] == register_payload["email"]
    assert "id" in body["user"]
    assert body["tokens"]["token_type"] == "bearer"

    access_token = body["tokens"]["access_token"]

    settings = get_settings()
    refresh_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    session_cookie = client.cookies.get(settings.jwt_session_cookie_name)
    assert refresh_cookie is not None
    assert session_cookie == session_id

    decoded_access = decode_token(access_token, expected_type="access")
    assert decoded_access["sub"] == str(body["user"]["id"])

    login_payload = {
        "username": "tester",
        "password": "password123",
    }

    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    login_body = response.json()
    assert login_body["user"]["username"] == register_payload["username"]
    assert login_body["user"]["email"] == register_payload["email"]
    assert login_body["tokens"]["access_token"]

    new_refresh_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    new_session_cookie = client.cookies.get(settings.jwt_session_cookie_name)
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_cookie
    assert new_session_cookie == session_cookie


def test_register_duplicate_username(client: TestClient) -> None:
    payload = {
        "username": "duplicated",
        "email": "user1@example.com",
        "password": "password123",
    }

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    payload["email"] = "user2@example.com"
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "이미 사용 중인 사용자명입니다."


def test_login_with_wrong_password(client: TestClient) -> None:
    payload = {
        "username": "user",
        "email": "user@example.com",
        "password": "password123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": "user", "password": "invalidpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "잘못된 인증 정보입니다."


def test_refresh_token_flow(client: TestClient) -> None:
    payload = {
        "username": "refresh",
        "email": "refresh@example.com",
        "password": "password123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()

    settings = get_settings()
    refresh_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    session_cookie = client.cookies.get(settings.jwt_session_cookie_name)
    assert refresh_cookie is not None
    assert session_cookie is not None

    response = client.post("/auth/refresh", headers={"User-Agent": "pytest"})
    assert response.status_code == 200
    tokens = response.json()
    assert tokens["token_type"] == "bearer"

    decoded_access = decode_token(tokens["access_token"], expected_type="access")
    assert decoded_access["sub"] == str(body["user"]["id"])

    refreshed_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    refreshed_session = client.cookies.get(settings.jwt_session_cookie_name)
    assert refreshed_cookie is not None
    assert refreshed_cookie != refresh_cookie
    assert refreshed_session == session_cookie


def test_refresh_token_cannot_be_reused(client: TestClient) -> None:
    payload = {
        "username": "reuse",
        "email": "reuse@example.com",
        "password": "password123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    settings = get_settings()
    original_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    assert original_cookie is not None

    response = client.post("/auth/refresh")
    assert response.status_code == 200

    # Reuse old refresh token should fail
    client.cookies.set(settings.jwt_refresh_cookie_name, original_cookie)
    response = client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "리프레시 토큰이 유효하지 않습니다."


def test_logout_revokes_session(client: TestClient) -> None:
    payload = {
        "username": "logout-user",
        "email": "logout@example.com",
        "password": "password123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    tokens = response.json()["tokens"]

    settings = get_settings()
    refresh_cookie = client.cookies.get(settings.jwt_refresh_cookie_name)
    session_cookie = client.cookies.get(settings.jwt_session_cookie_name)
    assert refresh_cookie and session_cookie

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 204

    assert client.cookies.get(settings.jwt_refresh_cookie_name) is None
    assert client.cookies.get(settings.jwt_session_cookie_name) is None

    # old refresh token should now be invalid
    client.cookies.set(settings.jwt_refresh_cookie_name, refresh_cookie)
    client.cookies.set(settings.jwt_session_cookie_name, session_cookie)
    response = client.post("/auth/refresh")
    assert response.status_code == 401
