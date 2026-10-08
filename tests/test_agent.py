from app.agent import pramanix_app
from langchain_core.messages import HumanMessage
import pytest


@pytest.mark.asyncio
async def test_agent_github_routing():
    initial_state = {
        "messages": [HumanMessage(content="Please check my github repository")],
        "active_tool": None,
    }

    result = await pramanix_app.ainvoke(initial_state)

    assert result is not None
    assert "messages" in result
    tool_messages = [
        m for m in result["messages"] if "[Tool Result]" in str(m.content)
    ]
    assert len(tool_messages) > 0


@pytest.mark.asyncio
async def test_agent_default_routing():
    initial_state = {
        "messages": [HumanMessage(content="Hello world")],
        "active_tool": None,
    }

    result = await pramanix_app.ainvoke(initial_state)
    assert result is not None
    assert result["active_tool"] is None
