from __future__ import annotations

import re

from console_log_server.utils.ollama import OllamaClient


class AiChatService:
    """로컬 Ollama 모델을 사용한 AI 챗 서비스."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    def chat(self, message: str) -> str:
        """사용자 메시지에 대한 모델 응답을 반환."""

        if not message.strip():
            raise ValueError("메시지는 비어 있을 수 없습니다.")

        raw_reply = self.client.chat(message.strip())
        return self._strip_think_block(raw_reply)

    def _strip_think_block(self, text: str) -> str:
        """<think>...</think> 블록을 제거하여 사용자에겐 모델 답변만 전달."""

        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
