"""FastAPI entrypoint: /health, /chat, and static web app serving."""

import logging
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agent import get_agent, run_chat
from app.config import allowed_origins, gemini_model
from app.llm import MissingConfigError
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SuggestionItem,
)
from app.tools import TOOLS

logger = logging.getLogger("pramanix")

app = FastAPI(
    title="Pramanix AI",
    version="0.3.0",
    description="Autonomous AI Agent built with LangGraph, FastAPI, and Google Gemini.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def agent_dependency() -> Any:
    """Dependency that resolves the LangGraph agent or raises 503 if missing API key."""
    try:
        return get_agent()
    except MissingConfigError as exc:
        logger.error("Model not configured: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The AI model is not configured on the server.",
        ) from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint reporting API status, version, and loaded tools."""
    return HealthResponse(
        status="ok",
        version="0.3.0",
        model=gemini_model(),
        tools=[tool.name for tool in TOOLS],
    )


@app.get("/api/suggestions", response_model=list[SuggestionItem])
def get_suggestions() -> list[SuggestionItem]:
    """Curated suggestions and starter queries for students and developers."""
    return [
        SuggestionItem(
            category="🎓 Student Projects",
            title="Python Starter Kits",
            prompt="Find beginner-friendly Python repositories for a library management system with good documentation.",
            icon="📚",
        ),
        SuggestionItem(
            category="🤖 AI & Agents",
            title="LangGraph & LLMs",
            prompt="Find top open-source repositories demonstrating AI agents built with LangGraph and FastAPI.",
            icon="🧠",
        ),
        SuggestionItem(
            category="⚡ Full Stack",
            title="React + FastAPI Starters",
            prompt="Compare React and Next.js templates for building full-stack web applications with FastAPI.",
            icon="🚀",
        ),
        SuggestionItem(
            category="🔧 Developer Tools",
            title="Top CLI & Utilities",
            prompt="Recommend popular open-source developer CLI tools written in Python or Rust.",
            icon="⚙️",
        ),
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: Any = Depends(agent_dependency),  # noqa: B008
) -> ChatResponse:
    """Handle chat messages, invoke LangGraph agent, and return assistant response with tool artifacts."""
    history = [(turn.role, turn.content) for turn in request.history]
    try:
        result = await run_chat(agent, request.message, history)
    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service encountered an error while processing your request. Please try again.",
        ) from None

    return ChatResponse(
        response=result.response,
        tool_used=result.tool_used,
        repositories=result.repositories,
        model=gemini_model(),
    )


# Mount the production-built frontend static assets if available
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
