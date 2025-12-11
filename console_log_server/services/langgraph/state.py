from __future__ import annotations

from typing import List, TypedDict
from typing_extensions import Annotated

from langgraph.graph import add_messages

from langchain_core.messages import BaseMessage


class ChatState(TypedDict):
    """LangGraph 실행 시 공유되는 상태."""

    messages: Annotated[List[BaseMessage], add_messages]
