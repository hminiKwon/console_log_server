from __future__ import annotations

import sys
from typing import Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from console_log_server.core import get_settings
from console_log_server.services.langgraph.prompts import DEFAULT_SYSTEM_PROMPT
from console_log_server.services.langgraph.state import ChatState
from console_log_server.utils.ollama import OllamaClient

# LangChain의 pydantic v1 호환 계층이 3.13+에서 불안정해 명시적으로 막아 둠
# if sys.version_info >= (3, 13):
#     raise RuntimeError(
#         "LangGraph/LangChain stack currently requires Python < 3.13 "
#         "(pydantic v1 compatibility on 3.13+ is not supported)."
#     )


class LangGraphChatOrchestrator:
    """LangGraph 기반 챗봇 워크플로우 오케스트레이터."""

    def __init__(
        self,
        *,
        client: OllamaClient | None = None,
        checkpointer: MemorySaver | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        thread_namespace: str = "ai-chat",
    ) -> None:
        settings = get_settings()
        self.llm_client = client or OllamaClient()
        self.checkpointer = checkpointer or MemorySaver()
        self.system_prompt = system_prompt
        self.thread_namespace = thread_namespace
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("prepare", self._inject_system_prompt)
        workflow.add_node("generate", self._generate_reply)

        workflow.add_edge(START, "prepare")
        workflow.add_edge("prepare", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def _inject_system_prompt(self, state: ChatState) -> ChatState:
        """히스토리에 시스템 프롬프트가 없으면 추가."""

        messages = list(state["messages"])
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages.insert(0, SystemMessage(content=self.system_prompt))
        return {"messages": messages}

    def _generate_reply(self, state: ChatState) -> ChatState:
        """로컬 Ollama 클라이언트를 호출해 답변을 생성."""

        prompt = self._to_prompt(state["messages"])
        content = self.llm_client.chat(prompt)
        ai_msg = AIMessage(content=content)
        messages = list(state["messages"]) + [ai_msg]
        return {"messages": messages}

    def run(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        history: Iterable[BaseMessage] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """단일 턴 실행. thread_id를 고정하면 MemorySaver로 다중 턴 유지."""

        if not message.strip():
            raise ValueError("메시지는 비어 있을 수 없습니다.")

        messages = list(history or [])
        prompt = system_prompt or self.system_prompt
        # system_prompt를 명시적으로 바꾸면 prepare 단계 전에 반영되도록 교체
        if prompt != self.system_prompt:
            messages = [m for m in messages if not isinstance(m, SystemMessage)]
            messages.insert(0, SystemMessage(content=prompt))

        messages.append(HumanMessage(content=message.strip()))

        config = {
            "configurable": {
                "thread_id": thread_id or "default",
                "checkpoint_ns": self.thread_namespace,
            }
        }

        final_state = self.graph.invoke({"messages": messages}, config=config)
        last_message = final_state["messages"][-1]
        return (
            last_message.content
            if isinstance(last_message, AIMessage)
            else str(last_message)
        )

    def _to_prompt(self, messages: list[BaseMessage]) -> str:
        """LangChain 메시지 리스트를 Ollama 프롬프트 문자열로 변환."""

        parts: list[str] = []
        for msg in messages:
            role = "system"
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            parts.append(f"[{role}]\n{msg.content}\n")
        return "\n".join(parts)


_shared_orchestrator: LangGraphChatOrchestrator | None = None


def get_shared_orchestrator() -> LangGraphChatOrchestrator:
    """요청 간 대화 메모리를 유지하기 위한 싱글톤 오케스트레이터."""

    global _shared_orchestrator
    if _shared_orchestrator is None:
        _shared_orchestrator = LangGraphChatOrchestrator()
    return _shared_orchestrator
