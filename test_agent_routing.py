# tests/test_agent_routing.py - no real Gemini or GitHub calls
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

from app.agent import build_agent, run_chat

FAKE_REPO = {"name": "a/b", "url": "https://github.com/a/b", "stars": 3}


@tool("github_search", response_format="content_and_artifact")
async def fake_search(query: str) -> tuple[str, list[dict[str, Any]]]:
    """Fake search."""
    return "a/b | Python | 3 stars", [FAKE_REPO]


class ScriptedModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedModel":
        return self

    def _generate(
        self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any
    ) -> ChatResult:
        last = messages[-1]
        if isinstance(last, ToolMessage):
            reply = AIMessage(content="Here is one repository.")
        elif isinstance(last, HumanMessage) and "repositor" in str(last.content):
            call = {"name": "github_search", "args": {"query": "x"}, "id": "c1"}
            reply = AIMessage(content="", tool_calls=[call])
        else:
            reply = AIMessage(content="Recursion is a function calling itself.")
        return ChatResult(generations=[ChatGeneration(message=reply)])


async def test_repository_request_uses_tool() -> None:
    agent = build_agent(ScriptedModel(), [fake_search])
    result = await run_chat(agent, "Find Python repositories for a quiz app")
    assert result.tool_used == "github_search"
    assert result.repositories[0].name == "a/b"


async def test_general_question_skips_tool() -> None:
    agent = build_agent(ScriptedModel(), [fake_search])
    result = await run_chat(agent, "Explain recursion simply")
    assert result.tool_used is None
    assert result.repositories == []
