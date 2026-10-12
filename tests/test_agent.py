"""Offline tests for model routing and structured tool results."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from app.agent import build_agent, run_chat
from app.schemas import Repository


@tool
async def github_search(query: str) -> str:
    """Return one predictable repository for an agent test."""
    return json.dumps(
        [
            {
                "name": "example/library-app",
                "url": "https://github.com/example/library-app",
                "description": "A library project",
                "language": "Python",
                "stars": 7,
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]
    )


class ScriptedBoundModel:
    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = responses

    async def ainvoke(self, messages: list[Any]) -> AIMessage:
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return self.responses[-1]
        if isinstance(last, HumanMessage):
            return self.responses[0]
        return self.responses[-1]


class ScriptedModel:
    def __init__(self, responses: list[AIMessage]) -> None:
        self.bound = ScriptedBoundModel(responses)

    def bind_tools(self, tools: list[Any]) -> ScriptedBoundModel:
        assert tools
        return self.bound


async def test_general_question_uses_model_without_tool() -> None:
    model = ScriptedModel([AIMessage(content="Recursion is a function calling itself.")])
    agent = build_agent(model=model, tools=[github_search])  # type: ignore[arg-type]

    result = await run_chat(agent, "Explain recursion simply")

    assert result["response"] == "Recursion is a function calling itself."
    assert result["tool_used"] is None
    assert result["repositories"] == []


async def test_model_tool_call_returns_real_structured_repository_data() -> None:
    model = ScriptedModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "github_search",
                        "args": {"query": "beginner Python library project"},
                        "id": "call_search_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="This Python project may be a useful starting point."),
        ]
    )
    agent = build_agent(model=model, tools=[github_search])  # type: ignore[arg-type]

    result = await run_chat(agent, "Find a beginner Python library project")

    assert result["response"].startswith("This Python project")
    assert result["tool_used"] == "github_search"
    assert result["repositories"] == [
        Repository(
            name="example/library-app",
            url="https://github.com/example/library-app",
            description="A library project",
            language="Python",
            stars=7,
            updated_at="2026-01-01T00:00:00Z",
        )
    ]
