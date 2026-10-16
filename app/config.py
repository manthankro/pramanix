"""Environment configuration. Importing this module loads .env once."""

import os

from dotenv import load_dotenv

load_dotenv()


def google_api_key() -> str | None:
    """Return the Google AI Studio / Gemini API key from environment."""
    return os.getenv("GOOGLE_API_KEY") or None


def gemini_model() -> str:
    """Return the configured Gemini model name."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def github_token() -> str | None:
    """Return optional GitHub personal access token for higher rate limits."""
    return os.getenv("GITHUB_TOKEN") or None


def allowed_origins() -> list[str]:
    """Return allowed CORS origins for the frontend."""
    raw = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def server_host() -> str:
    """Return the server binding host."""
    return os.getenv("HOST", "0.0.0.0")


def server_port() -> int:
    """Return the server binding port."""
    try:
        return int(os.getenv("PORT", "8000"))
    except ValueError:
        return 8000
