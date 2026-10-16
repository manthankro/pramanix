"""Read-only GitHub repository search with bounded inputs and safe failures."""

import os
from typing import Any

import httpx

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubSearchError(RuntimeError):
    """A safe, user-facing GitHub search failure."""


def _normalize_repo(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "updated_at": repo.get("updated_at"),
    }


async def search_repositories(
    query: str,
    limit: int = 5,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """Search public repositories. An optional client makes this easy to test."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Search query must not be empty")
    if len(normalized_query) > 200:
        raise ValueError("Search query must be 200 characters or fewer")
    per_page = max(1, min(limit, 10))
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params: dict[str, str | int] = {
        "q": normalized_query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=10.0) as owned_client:
                response = await owned_client.get(GITHUB_SEARCH_URL, params=params, headers=headers)
        else:
            response = await client.get(
                GITHUB_SEARCH_URL, params=params, headers=headers, timeout=10.0
            )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        raise GitHubSearchError("GitHub search timed out. Please try again.") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (403, 429):
            raise GitHubSearchError(
                "GitHub search is rate-limited. Please try again later."
            ) from exc
        raise GitHubSearchError("GitHub search is temporarily unavailable.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise GitHubSearchError("GitHub search is temporarily unavailable.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise GitHubSearchError("GitHub returned an unexpected search response.")
    try:
        return [_normalize_repo(repo) for repo in payload["items"][:per_page]]
    except (KeyError, TypeError) as exc:
        raise GitHubSearchError("GitHub returned an unexpected search response.") from exc
