"""GitHub API tests that use an in-memory HTTP transport."""

import httpx
import pytest

from app.github_search import GitHubSearchError, search_repositories


@pytest.mark.asyncio
async def test_search_normalizes_repository_and_bounds_limit() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "student Python projects"
        assert request.url.params["per_page"] == "10"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "full_name": "example/student-project",
                        "html_url": "https://github.com/example/student-project",
                        "description": "Example app",
                        "language": "Python",
                        "stargazers_count": 9,
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        results = await search_repositories(" student Python projects ", 100, client=client)

    assert results[0]["name"] == "example/student-project"
    assert results[0]["stars"] == 9


@pytest.mark.asyncio
async def test_search_turns_rate_limit_into_safe_error() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(429))
    ) as client:
        with pytest.raises(GitHubSearchError, match="rate-limited"):
            await search_repositories("python", client=client)


@pytest.mark.asyncio
async def test_search_rejects_empty_or_oversized_query() -> None:
    with pytest.raises(ValueError, match="empty"):
        await search_repositories("  ")
    with pytest.raises(ValueError, match="200 characters"):
        await search_repositories("x" * 201)
