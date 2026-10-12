"""FastAPI entrypoint for the Pramanix AI assistant."""

import logging
import os
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.agent import get_agent, run_chat
from app.llm import MissingConfigError
from app.schemas import Repository

load_dotenv()
logger = logging.getLogger("pramanix")

app = FastAPI(title="Pramanix AI", version="0.2.0")
origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be blank")
        return cleaned


class ChatResponse(BaseModel):
    response: str
    tool_used: str | None = None
    repositories: list[Repository] = Field(default_factory=list)


def agent_dependency() -> Any:
    try:
        return get_agent()
    except MissingConfigError as exc:
        logger.error("Model is not configured")
        raise HTTPException(
            status_code=503,
            detail="The AI model is not configured. Set OPENAI_API_KEY on the server.",
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
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not complete this request. Please try again.",
        ) from exc
    return ChatResponse(**result)
