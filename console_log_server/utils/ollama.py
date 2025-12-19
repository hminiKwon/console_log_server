from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from console_log_server.core import get_settings


THINKING_ROUTER_PROMPT = (
    "You are a routing assistant. Decide if the user's message requires deep, "
    "multi-step reasoning, careful planning, or complex analysis. "
    "Respond ONLY with JSON like {{\"use_thinking\":true/false}}. "
    "Use true for multi-constraint tasks, proofs, debugging, or long-term planning. "
    "Use false for simple Q&A, small talk, or direct factual answers. "
    "User message: {user_message}"
)


class OllamaConfig:
    """Ollama 호출 설정."""

    def __init__(
        self,
        *,
        host: str,
        instruct_model: str,
        thinking_model: str | None = None,
    ) -> None:
        self.host = host
        self.instruct_model = instruct_model
        self.thinking_model = thinking_model


class OllamaClient:
    """로컬 Ollama HTTP API 클라이언트."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or self._config_from_settings()

    def chat(self, message: str, *, model: str | None = None) -> str:
        """주어진 메시지로 챗봇 응답을 요청."""

        model_name = self.resolve_model_name(model=model)

        payload: dict[str, Any] = {
            "model": model_name,
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

    def think(self, message: str) -> str:
        """생각용 모델로 요청(없으면 instruct 모델로 대체)."""

        model_name = self.resolve_model_name(use_thinking=True)
        return self.chat(message, model=model_name)

    def resolve_model_name(
        self,
        *,
        use_thinking: bool = False,
        model: str | None = None,
    ) -> str:
        """사용할 모델 이름을 결정."""

        if model:
            return model
        if use_thinking and self.config.thinking_model:
            return self.config.thinking_model
        return self.config.instruct_model

    def should_use_thinking(self, message: str) -> bool:
        """사용자 메시지에 대해 thinking 모델 필요 여부를 판단."""

        prompt = THINKING_ROUTER_PROMPT.format(user_message=repr(message))
        try:
            raw = self.chat(prompt)
            data = json.loads(raw)
        except Exception:  # pragma: no cover - 라우팅 실패 시 기본값
            return False

        use_thinking = data.get("use_thinking")
        if isinstance(use_thinking, str):
            return use_thinking.strip().lower() == "true"
        return bool(use_thinking)

    def _config_from_settings(self) -> OllamaConfig:
        settings = get_settings()
        return OllamaConfig(
            host=settings.ollama_host,
            instruct_model=settings.ollama_instruct_model,
            thinking_model=settings.ollama_thinking_model,
        )
