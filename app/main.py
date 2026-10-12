"""FastAPI entrypoint: /health and /chat."""

import logging
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.agent import get_agent, run_chat
from app.config import allowed_origins
from app.llm import MissingConfigError
from app.schemas import Repository

logger = logging.getLogger("pramanix")

app = FastAPI(title="Pramanix AI", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ChatResponse(BaseModel):
    response: str
    tool_used: str | None = None
    repositories: list[Repository] = Field(default_factory=list)


def agent_dependency() -> Any:
    try:
        return get_agent()
    except MissingConfigError as exc:
        logger.error("Model not configured: %s", exc)
        raise HTTPException(
            status_code=503, detail="The AI model is not configured on the server."
        ) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: Any = Depends(agent_dependency),  # noqa: B008
) -> ChatResponse:
    history = [(turn.role, turn.content) for turn in request.history]
    try:
        result = await run_chat(agent, request.message, history)
    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502, detail="The AI service failed. Please try again."
        ) from None
    return ChatResponse(
        response=result.response,
        tool_used=result.tool_used,
        repositories=result.repositories,
    )
