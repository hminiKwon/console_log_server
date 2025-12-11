from __future__ import annotations

import json
import sys
from typing import Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from console_log_server.core import get_settings
from console_log_server.core.logging_config import get_logger
from console_log_server.services.langgraph.prompts import DEFAULT_SYSTEM_PROMPT
from console_log_server.services.langgraph.state import ChatState
from console_log_server.services.langgraph import tools
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
        self.logger = get_logger(__name__)

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("prepare", self._inject_system_prompt)
        workflow.add_node("maybe_tools", self._maybe_use_tools)
        workflow.add_node("generate", self._generate_reply)

        workflow.add_edge(START, "prepare")
        workflow.add_edge("prepare", "maybe_tools")
        workflow.add_edge("maybe_tools", "generate")
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
        self.logger.debug("Generating reply via Ollama prompt_len=%d", len(prompt))
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

        self.logger.debug(
            "Invoking graph thread_id=%s messages=%d",
            config["configurable"]["thread_id"],
            len(messages),
        )
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

    def _maybe_use_tools(self, state: ChatState) -> ChatState:
        """
        LLM 판단 기반으로 검색 등 실시간 도구 결과를 히스토리에 주입.

        - 날짜/시간 키워드는 로컬에서 즉시 처리
        - 그 외는 LLM이 검색 필요 여부와 쿼리를 결정하여 Google 검색을 실행
        """

        messages = list(state["messages"])
        last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        if last_user is None:
            return {"messages": messages}

        content_lower = last_user.content.lower()
        tool_outputs: list[str] = []

        if any(keyword in content_lower for keyword in ["날짜", "오늘", "date", "time", "시간", "몇시", "몇 시"]):
            tool_outputs.append(f"[time] {tools.get_current_datetime()}")

        use_search, search_query = self._decide_search_need(last_user.content)
        if use_search:
            query = search_query or last_user.content
            tool_outputs.append(f"[search] {tools.google_search(query)}")

        if tool_outputs:
            self.logger.info(
                "Tool triggers thread_ns=%s time=%s search=%s",
                self.thread_namespace,
                any("time" in t for t in tool_outputs),
                any("search" in t for t in tool_outputs),
            )
            injected = "실시간 도구 결과:\n" + "\n".join(f"- {t}" for t in tool_outputs)
            messages.append(SystemMessage(content=injected))

        return {"messages": messages}

    def _decide_search_need(self, user_message: str) -> tuple[bool, str | None]:
        """
        LLM에게 검색 필요 여부와 쿼리를 판단하게 위임.

        반환: (use_search, query)
        """

        prompt = (
            "You are a routing assistant. Decide if web search is needed to answer "
            "the user's message. Respond ONLY with JSON like "
            '{"use_search":true/false,"query":"search keywords"}. '
            "If the message asks for current events, live data, weather, locations, "
            "news, schedules, or anything you are unsure about, set use_search to true. "
            "If no search is needed, set use_search to false and query to an empty string. "
            f"User message: {user_message!r}"
        )

        try:
            raw = self.llm_client.chat(prompt)
            self.logger.debug("search_router raw=%s", raw)
            data = json.loads(raw)
            use_search = bool(data.get("use_search"))
            query = data.get("query") or None
            return use_search, query
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self.logger.warning("search_router_fallback err=%s", exc)
            return False, None


_shared_orchestrator: LangGraphChatOrchestrator | None = None


def get_shared_orchestrator() -> LangGraphChatOrchestrator:
    """요청 간 대화 메모리를 유지하기 위한 싱글톤 오케스트레이터."""

    global _shared_orchestrator
    if _shared_orchestrator is None:
        _shared_orchestrator = LangGraphChatOrchestrator()
    return _shared_orchestrator
