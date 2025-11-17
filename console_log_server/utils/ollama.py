from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from console_log_server.core import get_settings


class OllamaConfig:
    """Ollama 호출 설정."""

    def __init__(self, *, host: str, model: str) -> None:
        self.host = host
        self.model = model


class OllamaClient:
    """로컬 Ollama HTTP API 클라이언트."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or self._config_from_settings()

    def chat(self, message: str) -> str:
        """주어진 메시지로 챗봇 응답을 요청."""

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }

        request = Request(
            f"{self.config.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError) as exc:  # pragma: no cover - 네트워크 예외 방어
            raise RuntimeError("Ollama 서버에 연결할 수 없습니다.") from exc

        try:
            data = json.loads(raw)
            message_block = data.get("message") or {}
            content = message_block.get("content")
        except Exception as exc:  # pragma: no cover - 파싱 오류 방어
            raise RuntimeError("Ollama 응답을 해석하지 못했습니다.") from exc

        if not content:
            raise RuntimeError("Ollama가 빈 응답을 반환했습니다.")

        return str(content)

    def _config_from_settings(self) -> OllamaConfig:
        settings = get_settings()
        return OllamaConfig(host=settings.ollama_host, model=settings.ollama_model)
