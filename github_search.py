"""Read-only GitHub repository search (fixed host, server-side token)."""

import httpx

from app.config import github_token
from app.schemas import Repository

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
MAX_QUERY_LENGTH = 200


class GitHubSearchError(RuntimeError):
    """A safe, user-presentable GitHub failure."""


async def search_repositories(
    query: str,
    limit: int = 5,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[Repository]:
    query = query.strip()
    if not query:
        return []
    if len(query) > MAX_QUERY_LENGTH:
        raise GitHubSearchError("The search query is too long.")

    params: dict[str, str | int] = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max(1, min(limit, 10)),
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=10.0) as own_client:
                response = await own_client.get(
                    GITHUB_SEARCH_URL, params=params, headers=headers
                )
        else:
            response = await client.get(
                GITHUB_SEARCH_URL, params=params, headers=headers
            )
    except httpx.TimeoutException as exc:
        raise GitHubSearchError("GitHub took too long to respond.") from exc
    except httpx.HTTPError as exc:
        raise GitHubSearchError("Could not reach GitHub.") from exc

    if response.status_code in (403, 429):
        raise GitHubSearchError("GitHub rate limit reached. Try again later.")
    if response.status_code == 401:
        raise GitHubSearchError("The GitHub token is invalid or expired.")
    if response.status_code >= 400:
        raise GitHubSearchError(f"GitHub returned status {response.status_code}.")

    try:
        items = response.json()["items"]
        return [
            Repository(
                name=item["full_name"],
                url=item["html_url"],
                description=item.get("description"),
                language=item.get("language"),
                stars=item.get("stargazers_count", 0),
                updated_at=item.get("updated_at"),
            )
            for item in items
        ]
    except (ValueError, KeyError, TypeError) as exc:
        raise GitHubSearchError("GitHub returned an unexpected response.") from exc
