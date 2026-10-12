"""Gemini model factory (Google AI Studio API key)."""

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from app.config import gemini_model, google_api_key


class MissingConfigError(RuntimeError):
    """Raised when a required server-side setting is absent."""


def build_model() -> ChatGoogleGenerativeAI:
    api_key = google_api_key()
    if not api_key:
        raise MissingConfigError("GOOGLE_API_KEY is not configured")
    return ChatGoogleGenerativeAI(
        model=gemini_model(),
        google_api_key=SecretStr(api_key),
        temperature=0,
        timeout=30,
        max_retries=2,
    )
