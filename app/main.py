"""FastAPI server exposing the Pramanix agent."""

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agent import AgentState, pramanix_app

app = FastAPI(title="Pramanix Agent")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    tool_used: str | None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    state: AgentState = {
        "messages": [HumanMessage(content=request.message)],
        "active_tool": None,
    }
    result = await pramanix_app.ainvoke(state)
    messages = result["messages"]
    if len(messages) > 1:
        return ChatResponse(response=str(messages[-1].content), tool_used="github_search")
    return ChatResponse(response="No tool needed for this message.", tool_used=None)
