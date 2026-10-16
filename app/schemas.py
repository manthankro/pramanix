"""Shared API data models."""

from pydantic import BaseModel, HttpUrl


class Repository(BaseModel):
    name: str
    url: HttpUrl
    description: str | None = None
    language: str | None = None
    stars: int = 0
    updated_at: str | None = None
