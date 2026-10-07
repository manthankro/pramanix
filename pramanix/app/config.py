import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("PRAMANIX_MODEL", "claude-sonnet-5-5")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    max_steps: int = int(os.getenv("MAX_AGENT_STEPS", "14"))
    cache_ttl: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    allowed_origin: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
    rate_limit_per_min: int = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))


settings = Settings()
