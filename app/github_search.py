"""Read-only GitHub repository exploration (fixed host, server-side token)."""

from typing import Any

import httpx

from app.config import github_token
from app.schemas import Repository

GITHUB_API_BASE = "https://api.github.com"
GITHUB_SEARCH_URL = f"{GITHUB_API_BASE}/search/repositories"
MAX_QUERY_LENGTH = 200


class GitHubSearchError(RuntimeError):
    """A safe, user-presentable GitHub failure."""


def _get_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _parse_repo(item: dict[str, Any]) -> Repository:
    license_info = item.get("license")
    license_name = license_info.get("name") if isinstance(license_info, dict) else None
    return Repository(
        name=item.get("name", item.get("full_name", "")),
        full_name=item.get("full_name"),
        url=item.get("html_url", ""),
        description=item.get("description"),
        language=item.get("language"),
        stars=item.get("stargazers_count", 0),
        forks=item.get("forks_count", 0),
        topics=item.get("topics", []) if isinstance(item.get("topics"), list) else [],
        license=license_name,
        updated_at=item.get("updated_at"),
    )


async def search_repositories(
    query: str,
    limit: int = 5,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[Repository]:
    """Search public GitHub repositories by query string with star ordering."""
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
    headers = _get_headers()

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=10.0) as own_client:
                response = await own_client.get(GITHUB_SEARCH_URL, params=params, headers=headers)
        else:
            response = await client.get(GITHUB_SEARCH_URL, params=params, headers=headers)
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
        data = response.json()
        items = data.get("items", [])
        return [_parse_repo(item) for item in items]
    except (ValueError, KeyError, TypeError) as exc:
        raise GitHubSearchError("GitHub returned an unexpected response.") from exc


async def get_repository_details(
    owner: str,
    repo: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> Repository:
    """Fetch metadata for a specific repository by owner and name."""
    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        raise GitHubSearchError("Owner and repo name must be provided.")

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = _get_headers()

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=10.0) as own_client:
                response = await own_client.get(url, headers=headers)
        else:
            response = await client.get(url, headers=headers)
    except httpx.TimeoutException as exc:
        raise GitHubSearchError("GitHub took too long to respond.") from exc
    except httpx.HTTPError as exc:
        raise GitHubSearchError("Could not reach GitHub.") from exc

    if response.status_code == 404:
        raise GitHubSearchError(f"Repository {owner}/{repo} was not found on GitHub.")
    if response.status_code in (403, 429):
        raise GitHubSearchError("GitHub rate limit reached. Try again later.")
    if response.status_code >= 400:
        raise GitHubSearchError(f"GitHub returned status {response.status_code}.")

    try:
        return _parse_repo(response.json())
    except (ValueError, KeyError, TypeError) as exc:
        raise GitHubSearchError("GitHub returned an unexpected response format.") from exc
