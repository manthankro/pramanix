"""Tests for the LangGraph agent."""

import asyncio

from app.agent import pramanix_app
from langchain_core.messages import HumanMessage


def test_no_tool_for_plain_message() -> None:
    state = {"messages": [HumanMessage(content="hello")], "active_tool": None}
    result = asyncio.run(pramanix_app.ainvoke(state))
    assert result["active_tool"] is None
    assert len(result["messages"]) == 1
