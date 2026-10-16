"""OpenAI chat model configuration."""

import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class MissingConfigError(RuntimeError):
    """Raised when the server has no configured model API key."""


def build_model() -> ChatOpenAI:
    """Create the OpenAI model using server-side environment configuration."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingConfigError("OPENAI_API_KEY is not configured")
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        api_key=SecretStr(api_key),
        temperature=0,
        timeout=30,
        max_retries=2,
        max_completion_tokens=1024,
    )
