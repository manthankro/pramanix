"""Shared data models and schemas for Pramanix AI."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Repository(BaseModel):
    """Normalized repository metadata."""

    name: str
    url: str
    full_name: str | None = None
    description: str | None = None
    language: str | None = None
    stars: int = 0
    forks: int = 0
    topics: list[str] = Field(default_factory=list)
    license: str | None = None
    updated_at: str | None = None


class Turn(BaseModel):
    """A single conversation turn in chat history."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

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
    """Outgoing chat response payload."""

    response: str
    tool_used: str | None = None
    repositories: list[Repository] = Field(default_factory=list)
    model: str | None = None


class SuggestionItem(BaseModel):
    """Starter prompt suggestion for students and developers."""

    category: str
    title: str
    prompt: str
    icon: str


class HealthResponse(BaseModel):
    """System health check and status."""

    status: str
    version: str
    model: str
    tools: list[str]
