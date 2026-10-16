import httpx
import pytest

from app.github_search import (
    GitHubSearchError,
    get_repository_details,
    search_repositories,
)

PAYLOAD = {
    "items": [
        {
            "full_name": "example/student-project",
            "html_url": "https://github.com/example/student-project",
            "description": "Example project",
            "language": "Python",
            "stargazers_count": 7,
            "forks_count": 2,
            "topics": ["student", "template"],
            "license": {"name": "MIT License"},
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ]
}

REPO_PAYLOAD = {
    "full_name": "example/fastapi-starter",
    "html_url": "https://github.com/example/fastapi-starter",
    "description": "Starter template for FastAPI",
    "language": "Python",
    "stargazers_count": 120,
    "forks_count": 35,
    "topics": ["fastapi", "template"],
    "license": {"name": "Apache-2.0"},
    "updated_at": "2026-02-01T00:00:00Z",
}


def client_for(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


async def test_normalizes_repository() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    async with client_for(transport) as client:
        repos = await search_repositories("student project", client=client)
    assert repos[0].name == "example/student-project"
    assert repos[0].stars == 7
    assert repos[0].forks == 2
    assert repos[0].language == "Python"
    assert repos[0].license == "MIT License"
    assert "student" in repos[0].topics


async def test_blank_query_returns_nothing() -> None:
    assert await search_repositories("   ") == []


async def test_query_too_long() -> None:
    with pytest.raises(GitHubSearchError, match="too long"):
        await search_repositories("a" * 201)


async def test_get_repository_details_success() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=REPO_PAYLOAD))
    async with client_for(transport) as client:
        repo = await get_repository_details("example", "fastapi-starter", client=client)
    assert repo.full_name == "example/fastapi-starter"
    assert repo.stars == 120
    assert repo.language == "Python"
    assert repo.license == "Apache-2.0"


async def test_get_repository_details_not_found() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    async with client_for(transport) as client:
        with pytest.raises(GitHubSearchError, match="not found"):
            await get_repository_details("example", "missing", client=client)


@pytest.mark.parametrize("status", [403, 429])
async def test_rate_limit_is_reported(status: int) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    async with client_for(transport) as client:
        with pytest.raises(GitHubSearchError, match="rate limit"):
            await search_repositories("python", client=client)


async def test_timeout_is_reported() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    async with client_for(httpx.MockTransport(handler)) as client:
        with pytest.raises(GitHubSearchError, match="too long"):
            await search_repositories("python", client=client)


async def test_malformed_json_is_reported() -> None:
    transport = httpx.MockTransport(lambda r: httpx.Response(200, text="not json"))
    async with client_for(transport) as client:
        with pytest.raises(GitHubSearchError, match="unexpected"):
            await search_repositories("python", client=client)
