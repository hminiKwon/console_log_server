from __future__ import annotations

import re
from typing import Iterable

from langchain_core.messages import BaseMessage

from console_log_server.core.logging_config import get_logger
from console_log_server.services.langgraph import (
    LangGraphChatOrchestrator,
    get_shared_orchestrator,
)
from console_log_server.utils.ollama import OllamaClient


class AiChatService:
    """로컬 Ollama 또는 LangGraph 워크플로우를 활용한 AI 챗 서비스."""

    def __init__(
        self,
        client: OllamaClient | None = None,
        graph: LangGraphChatOrchestrator | None = None,
        use_langgraph: bool = True,
    ) -> None:
        self.client = client or OllamaClient()
        self.graph = graph or get_shared_orchestrator()
        self.use_langgraph = use_langgraph
        self.logger = get_logger(__name__)

    def chat(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        history: Iterable[BaseMessage] | None = None,
    ) -> str:
        """사용자 메시지에 대한 모델 응답을 반환."""

        clean_message = message.strip()
        if not clean_message:
            raise ValueError("메시지는 비어 있을 수 없습니다.")

        if self.use_langgraph:
            raw_reply = self._chat_via_graph(
                clean_message, thread_id=thread_id, history=history
            )
            via = "langgraph"
            model_name = "langgraph-auto"
        else:
            use_thinking = self.client.should_use_thinking(clean_message)
            model_name = self.client.resolve_model_name(use_thinking=use_thinking)
            raw_reply = (
                self.client.think(clean_message)
                if use_thinking
                else self.client.chat(clean_message)
            )
            via = "ollama_client_thinking" if use_thinking else "ollama_client"

        reply = self._strip_think_block(raw_reply)
        self.logger.info(
            "chat handled via=%s model=%s thread_id=%s len_in=%d len_out=%d",
            via,
            model_name,
            thread_id or "default",
            len(clean_message),
            len(reply),
        )
        return reply

    def _strip_think_block(self, text: str) -> str:
        """<think>...</think> 블록을 제거하여 사용자에겐 모델 답변만 전달."""

        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()

    def _chat_via_graph(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        history: Iterable[BaseMessage] | None = None,
    ) -> str:
        """LangGraph 워크플로우를 통해 챗봇 호출."""

        return self.graph.run(message, thread_id=thread_id, history=history)
