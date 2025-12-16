from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastapi import HTTPException, status

from console_log_server.core.logging_config import get_logger


class JanusAdminClient:
    """
    Janus Admin API 래퍼 (간단 버전).

    - 세션 생성 → videoroom 플러그인 attach → room create/destroy 메시지 전송
    - Admin API는 네트워크 엑세스가 필요하므로 실제 호출 실패 시 HTTP 503을 발생시켜 상위에서 처리
    """

    def __init__(
        self,
        base_url: str,
        *,
        admin_secret: str = "",
        api_secret: str = "",
        timeout: float = 5.0,
    ) -> None:
        self.base_url = self._normalize_api_url(base_url)
        self.admin_secret = admin_secret
        self.api_secret = api_secret
        self.timeout = timeout
        self.logger = get_logger(__name__)

    def create_room(
        self,
        *,
        title: str,
        room_number: str,
        pin: str | None = None,
        max_participants: int | None = None,
    ) -> str:
        session_id = self._create_session()
        handle_id = self._attach_plugin(session_id)

        body: dict[str, Any] = {
            "request": "create",
            "room": int(room_number),
            "description": title,
        }
        if pin:
            body["pin"] = pin
        if max_participants:
            body["publishers"] = max_participants

        data = self._message(session_id, handle_id, body)
        room_id = (
            data.get("plugindata", {})
            .get("data", {})
            .get("room")
        )
        if not room_id:
            raise self._http_503("Janus 방 생성 실패: room id 없음")
        return str(room_id)

    def destroy_room(self, room_id: str) -> None:
        session_id = self._create_session()
        handle_id = self._attach_plugin(session_id)
        body = {
            "request": "destroy",
            "room": int(room_id),
        }
        self._message(session_id, handle_id, body)

    # 내부 유틸
    def _create_session(self) -> int:
        payload = {
            "janus": "create",
            "transaction": self._tx(),
            "admin_secret": self.admin_secret,
        }
        resp = self._post(payload)
        session_id = resp.get("data", {}).get("id")
        if session_id is None:
            raise self._http_503("Janus 세션 생성 실패")
        return int(session_id)

    def _attach_plugin(self, session_id: int) -> int:
        payload = {
            "janus": "attach",
            "transaction": self._tx(),
            "admin_secret": self.admin_secret,
            "session_id": session_id,
            "plugin": "janus.plugin.videoroom",
        }
        resp = self._post(payload)
        handle_id = resp.get("data", {}).get("id")
        if handle_id is None:
            raise self._http_503("Janus 플러그인 attach 실패")
        return int(handle_id)

    def _message(self, session_id: int, handle_id: int, body: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "janus": "message",
            "transaction": self._tx(),
            "admin_secret": self.admin_secret,
            "session_id": session_id,
            "handle_id": handle_id,
            "body": body,
        }
        if self.api_secret:
            payload["apisecret"] = self.api_secret
        return self._post(payload)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # nosec B310
                parsed = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            self.logger.error("janus_admin_http_error url=%s err=%s", self.base_url, exc)
            raise self._http_503(f"Janus 호출 실패: {exc}") from exc

        if parsed.get("janus") == "error":
            error = parsed.get("error") or {}
            code = error.get("code")
            reason = error.get("reason") or "unknown error"
            self.logger.error(
                "janus_admin_error action=%s code=%s reason=%s",
                payload.get("janus"),
                code,
                reason,
            )
            raise self._http_503(f"Janus 오류: {reason}")

        self.logger.debug(
            "janus_admin_ok action=%s janus=%s",
            payload.get("janus"),
            parsed.get("janus"),
        )
        return parsed

    @staticmethod
    def _tx() -> str:
        return secrets.token_hex(8)

    @staticmethod
    def _normalize_api_url(url: str) -> str:
        """
        admin URL이 들어와도 자동으로 /janus 경로와 8088 포트로 정규화한다.
        """

        parsed = urllib.parse.urlsplit(url.strip())
        path = parsed.path.rstrip("/")
        if path.endswith("/admin"):
            path = path[: -len("/admin")]
        if not path.endswith("/janus"):
            path = path + "/janus"

        netloc = parsed.netloc
        hostname = parsed.hostname or "127.0.0.1"
        port = parsed.port
        scheme = parsed.scheme or "http"

        if port == 7088:
            port = 8088
        if port:
            netloc = f"{hostname}:{port}"
        else:
            netloc = hostname

        normalized = urllib.parse.urlunsplit(
            (
                scheme,
                netloc,
                path,
                parsed.query,
                parsed.fragment,
            )
        )
        return normalized.rstrip("/")

    @staticmethod
    def _http_503(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
