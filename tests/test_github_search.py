import httpx
import pytest

from app.github_search import GitHubSearchError, search_repositories

PAYLOAD = {
    "items": [
        {
            "full_name": "example/student-project",
            "html_url": "https://github.com/example/student-project",
            "description": "Example project",
            "language": "Python",
            "stargazers_count": 7,
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ]
}


def client_for(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


async def test_normalizes_repository() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    async with client_for(transport) as client:
        repos = await search_repositories("student project", client=client)
    assert repos[0].name == "example/student-project"
    assert repos[0].stars == 7
    assert repos[0].language == "Python"


async def test_blank_query_returns_nothing() -> None:
    assert await search_repositories("   ") == []


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
