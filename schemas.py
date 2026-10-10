"""Shared response models."""

from pydantic import BaseModel


class Repository(BaseModel):
    name: str
    url: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    updated_at: str | None = None
