"""LangGraph agent: Gemini decides when to call tools to explore GitHub and answer questions."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.llm import build_model
from app.schemas import Repository
from app.tools import TOOLS

SYSTEM_PROMPT = (
    "You are Pramanix, an intelligent and helpful autonomous AI assistant for students and developers.\n"
    "Your mission is to help users learn programming, explore system design, discover quality open-source GitHub repositories, and evaluate tools.\n\n"
    "Guidelines:\n"
    "- Answer conceptual, programming, and general questions directly with clear explanations and structured markdown.\n"
    "- Use 'github_search' when the user wants to find, compare, or explore open-source repositories or project ideas.\n"
    "- Use 'github_repo_details' when the user requests information about a specific repository (e.g. 'tell me about tiangolo/fastapi').\n"
    "- Use 'github_trending' when the user asks for trending projects, starter kits, or student templates.\n"
    "- NEVER invent repository names, fake URLs, or synthetic star counts. Only provide factual data retrieved from tools.\n"
    "- Present repository recommendations cleanly, highlighting what makes each repo useful, its language, and licensing.\n"
    "- Remind students to inspect code quality, tests, and licenses before adopting dependencies."
)


class AgentState(TypedDict):
    """The graph state holding the message stream."""

    messages: Annotated[list[BaseMessage], add_messages]


@dataclass
class AgentResult:
    """The final processed response from the agent."""

    response: str
    tool_used: str | None = None
    repositories: list[Repository] = field(default_factory=list)


def build_agent(
    model: BaseChatModel | None = None,
    tools: Sequence[BaseTool] | None = None,
) -> Any:
    """Build and compile the LangGraph agent state graph."""
    tool_list = list(tools if tools is not None else TOOLS)
    chat_model = model or build_model()
    bound = chat_model.bind_tools(tool_list)

    async def call_model(state: AgentState) -> dict[str, list[BaseMessage]]:
        reply = await bound.ainvoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [reply]}

    def route(state: AgentState) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "__end__"

    graph = StateGraph(AgentState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tool_list))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", route, {"tools": "tools", "__end__": END})
    graph.add_edge("tools", "model")
    return graph.compile()


@lru_cache
def get_agent() -> Any:
    """Cached singleton of the default production agent."""
    return build_agent()


def _text(message: BaseMessage) -> str:
    """Safely extract string content from any BaseMessage."""
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and "text" in p:
                parts.append(str(p["text"]))
        return "".join(parts)
    return str(content)


async def run_chat(
    agent: Any,
    message: str,
    history: Sequence[tuple[str, str]] = (),
) -> AgentResult:
    """Execute a chat turn through the agent graph with historical context."""
    messages: list[BaseMessage] = [
        HumanMessage(text) if role == "user" else AIMessage(text) for role, text in history
    ]
    start = len(messages)
    messages.append(HumanMessage(message))

    state = await agent.ainvoke({"messages": messages}, config={"recursion_limit": 8})
    new_messages: list[BaseMessage] = state["messages"][start:]

    tool_used: str | None = None
    repositories: list[Repository] = []
    for item in new_messages:
        if isinstance(item, ToolMessage) and item.status != "error":
            tool_used = item.name
            if isinstance(item.artifact, list):
                for r in item.artifact:
                    if isinstance(r, dict):
                        repositories.append(Repository.model_validate(r))
                    elif isinstance(r, Repository):
                        repositories.append(r)

    last_ai_messages = [m for m in new_messages if isinstance(m, AIMessage)]
    if last_ai_messages:
        answer = _text(last_ai_messages[-1]).strip()
    else:
        answer = _text(new_messages[-1]).strip() if new_messages else ""

    if not answer:
        answer = "I could not produce an answer. Please try again."

    return AgentResult(answer, tool_used, repositories)
