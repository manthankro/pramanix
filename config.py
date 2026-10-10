"""Environment configuration. Importing this module loads .env once."""

import os

from dotenv import load_dotenv

load_dotenv()


def google_api_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or None


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def github_token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or None


def allowed_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
