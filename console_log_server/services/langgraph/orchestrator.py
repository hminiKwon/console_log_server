from __future__ import annotations

import json
from typing import Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from console_log_server.core.logging_config import get_logger
from console_log_server.services.langgraph.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    SEARCH_ROUTER_PROMPT,
    MCP_ROUTER_PROMPT,
)
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

    TIME_KEYWORDS = ("날짜", "오늘", "date", "time", "시간", "몇시", "몇 시")

    def __init__(
        self,
        *,
        client: OllamaClient | None = None,
        checkpointer: MemorySaver | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        thread_namespace: str = "ai-chat",
    ) -> None:
        self.llm_client = client or OllamaClient()
        self.checkpointer = checkpointer or MemorySaver()
        self.system_prompt = system_prompt
        self.thread_namespace = thread_namespace
        self.graph = self._build_graph()
        self.logger = get_logger(__name__)

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("prepare", self._inject_system_prompt)
        workflow.add_node("plan_tools", self._plan_tool_usage)
        workflow.add_node("apply_tools", self._apply_tools)
        workflow.add_node("generate", self._generate_reply)

        workflow.add_edge(START, "prepare")
        workflow.add_edge("prepare", "plan_tools")
        workflow.add_conditional_edges(
            "plan_tools",
            self._route_from_plan,
            {
                "use_tools": "apply_tools",
                "skip_tools": "generate",
            },
        )
        workflow.add_edge("apply_tools", "generate")
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
        use_thinking = bool(state.get("use_thinking"))
        model_name = self.llm_client.resolve_model_name(use_thinking=use_thinking)
        self.logger.info(
            "Generating reply via=%s model=%s prompt_len=%d",
            "thinking" if use_thinking else "instruct",
            model_name,
            len(prompt),
        )
        content = (
            self.llm_client.think(prompt)
            if use_thinking
            else self.llm_client.chat(prompt)
        )
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

    def _plan_tool_usage(self, state: ChatState) -> ChatState:
        """
        사용자 메시지를 보고 도구 사용 여부만 결정.

        - 날짜/시간 키워드는 즉시 플래그
        - 검색 필요 여부는 LLM에 라우팅을 맡김
        """

        messages = list(state["messages"])
        last_user = self._get_last_user(messages)
        if last_user is None:
            return {"messages": messages, "tool_request": None}

        use_time = self._should_use_time(last_user.content)
        use_search, search_query = self._decide_search_need(last_user.content)
        mcp_catalog = tools.list_mcp_tool_catalog()
        use_mcp, mcp_server, mcp_tool, mcp_arguments = self._decide_mcp_tool_use(
            last_user.content, mcp_catalog
        )
        use_thinking = self.llm_client.should_use_thinking(last_user.content)

        return {
            "messages": messages,
            "tool_request": {
                "use_time": use_time,
                "use_search": use_search,
                "search_query": search_query,
                "use_mcp": use_mcp,
                "mcp_server": mcp_server,
                "mcp_tool": mcp_tool,
                "mcp_arguments": mcp_arguments,
            },
            "use_thinking": use_thinking,
        }

    def _route_from_plan(self, state: ChatState) -> str:
        """도구 플래그에 따라 분기."""

        request = state.get("tool_request")
        if request and (
            request.get("use_time")
            or request.get("use_search")
            or request.get("use_mcp")
        ):
            return "use_tools"
        return "skip_tools"

    def _apply_tools(self, state: ChatState) -> ChatState:
        """결정된 도구만 실행해 메시지에 주입."""

        messages = list(state["messages"])
        request = state.get("tool_request")
        if not request:
            return {
                "messages": messages,
                "tool_request": None,
                "use_thinking": state.get("use_thinking"),
            }

        tool_outputs: list[str] = []

        if request.get("use_time"):
            tool_outputs.append(f"[time] {tools.get_current_datetime()}")

        if request.get("use_search"):
            query = request.get("search_query") or self._get_last_user_content(messages)
            if query:
                tool_outputs.append(f"[search] {tools.google_search(query)}")
            else:
                self.logger.info("Skipping search tool: empty query")
                request["use_search"] = False

        if request.get("use_mcp"):
            server = request.get("mcp_server")
            tool = request.get("mcp_tool")
            arguments = request.get("mcp_arguments") or {}
            if server and tool:
                result = tools.call_mcp_tool(server, tool, arguments=arguments)
                if result is None:
                    tool_outputs.append(f"[mcp:{server}/{tool}] mcp_tool_error")
                else:
                    rendered = self._render_mcp_result(result)
                    tool_outputs.append(f"[mcp:{server}/{tool}] {rendered}")
            else:
                self.logger.info("Skipping mcp tool: missing server/tool")
                request["use_mcp"] = False

        if tool_outputs:
            self.logger.info(
                "Tool triggers thread_ns=%s time=%s search=%s mcp=%s",
                self.thread_namespace,
                any("time" in t for t in tool_outputs),
                any("search" in t for t in tool_outputs),
                any("mcp:" in t for t in tool_outputs),
            )
            injected = "실시간 도구 결과:\n" + "\n".join(f"- {t}" for t in tool_outputs)
            messages.append(SystemMessage(content=injected))

        return {
            "messages": messages,
            "tool_request": None,
            "use_thinking": state.get("use_thinking"),
        }

    def _decide_search_need(self, user_message: str) -> tuple[bool, str | None]:
        """
        LLM에게 검색 필요 여부와 쿼리를 판단하게 위임.

        반환: (use_search, query)
        """

        prompt = SEARCH_ROUTER_PROMPT.format(user_message=repr(user_message))

        try:
            raw = self.llm_client.think(prompt)
            self.logger.debug("search_router raw=%s", raw)
            data = json.loads(raw)
            use_search = bool(data.get("use_search"))
            query = data.get("query") or None
            return use_search, query
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self.logger.warning("search_router_fallback err=%s", exc)
            return False, None

    def _decide_mcp_tool_use(
        self,
        user_message: str,
        tool_catalog: list[dict[str, object]],
    ) -> tuple[bool, str | None, str | None, dict[str, object] | None]:
        if not tool_catalog:
            return False, None, None, None

        prompt = MCP_ROUTER_PROMPT.format(
            user_message=repr(user_message),
            tools_json=json.dumps(tool_catalog),
        )

        try:
            raw = self.llm_client.think(prompt)
            self.logger.debug("mcp_router raw=%s", raw)
            data = json.loads(raw)
            use_mcp = bool(data.get("use_mcp"))
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self.logger.warning("mcp_router_fallback err=%s", exc)
            return False, None, None, None

        if not use_mcp:
            return False, None, None, None

        server = str(data.get("server") or "").strip()
        tool = str(data.get("tool") or "").strip()
        arguments = data.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}

        if not self._is_mcp_tool_available(tool_catalog, server, tool):
            self.logger.info("mcp tool not available server=%s tool=%s", server, tool)
            return False, None, None, None

        return True, server, tool, arguments

    def _get_last_user(self, messages: list[BaseMessage]) -> HumanMessage | None:
        """가장 최근 사용자 메시지 반환."""

        return next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)

    def _get_last_user_content(self, messages: list[BaseMessage]) -> str:
        """검색 쿼리 폴백용 최근 사용자 메시지 내용."""

        last_user = self._get_last_user(messages)
        return last_user.content if last_user else ""

    def _should_use_time(self, content: str) -> bool:
        """시간 관련 키워드 여부만 판단."""

        lowered = content.lower()
        return any(keyword in lowered for keyword in self.TIME_KEYWORDS)

    def _is_mcp_tool_available(
        self,
        tool_catalog: list[dict[str, object]],
        server: str,
        tool: str,
    ) -> bool:
        if not server or not tool:
            return False
        for entry in tool_catalog:
            if entry.get("server") != server:
                continue
            tools_list = entry.get("tools")
            if isinstance(tools_list, list) and any(
                tool == item.get("name") for item in tools_list if isinstance(item, dict)
            ):
                return True
        return False

    def _render_mcp_result(self, result: dict[str, object]) -> str:
        content = result.get("content")
        if not isinstance(content, list):
            content = [content] if content is not None else []
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(json.dumps(item))
        rendered = "\n".join(part for part in parts if part)
        if result.get("is_error"):
            return f"mcp_tool_error: {rendered or 'empty'}"
        return rendered or "empty"


_shared_orchestrator: LangGraphChatOrchestrator | None = None


def get_shared_orchestrator() -> LangGraphChatOrchestrator:
    """요청 간 대화 메모리를 유지하기 위한 싱글톤 오케스트레이터."""

    global _shared_orchestrator
    if _shared_orchestrator is None:
        _shared_orchestrator = LangGraphChatOrchestrator()
    return _shared_orchestrator
