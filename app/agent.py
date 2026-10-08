from collections.abc import Sequence
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The conversation history"]
    active_tool: str | None


async def reasoning_node(state: AgentState) -> dict[str, Any]:
    last_message = state["messages"][-1].content if state["messages"] else ""
    if "github" in str(last_message).lower():
        return {"active_tool": "github_search"}
    return {"active_tool": None}


async def tool_node(state: AgentState) -> dict[str, Any]:
    messages = list(state["messages"])
    if state["active_tool"] == "github_search":
        messages.append(
            AIMessage(content="[Tool Result]: Successfully fetched repository details from GitHub.")
        )
    return {"messages": messages}


workflow = StateGraph(AgentState)
workflow.add_node("reason", reasoning_node)
workflow.add_node("act", tool_node)
workflow.set_entry_point("reason")
workflow.add_conditional_edges(
    "reason",
    lambda x: "act" if x["active_tool"] else "end",
    {"act": "act", "end": END},
)
workflow.add_edge("act", "reason")
pramanix_app = workflow.compile()
