from __future__ import annotations

from typing import List, NotRequired, TypedDict
from typing_extensions import Annotated

from langgraph.graph import add_messages

from langchain_core.messages import BaseMessage


class ToolRequest(TypedDict):
    """도구 호출 여부와 검색 쿼리 정보."""

    use_time: bool
    use_search: bool
    search_query: str | None


class ChatState(TypedDict):
    """LangGraph 실행 시 공유되는 상태."""

    messages: Annotated[List[BaseMessage], add_messages]
    tool_request: NotRequired[ToolRequest | None]
    use_thinking: NotRequired[bool]
