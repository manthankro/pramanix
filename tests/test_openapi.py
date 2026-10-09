"""Tests for the LangGraph agent."""

from app.agent import AgentState, pramanix_app
from langchain_core.messages import HumanMessage


async def test_plain_message_uses_no_tool() -> None:
    state: AgentState = {"messages": [HumanMessage(content="hello")], "active_tool": None}
    result = await pramanix_app.ainvoke(state)
    assert result["active_tool"] is None
    assert len(result["messages"]) == 1


async def test_github_message_runs_tool_once() -> None:
    state: AgentState = {
        "messages": [HumanMessage(content="search github")],
        "active_tool": None,
    }
    result = await pramanix_app.ainvoke(state)
    assert len(result["messages"]) == 2
