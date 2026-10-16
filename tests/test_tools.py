"""Tests for LangChain tool definitions."""

import pytest

from app.schemas import Repository
from app.tools import github_repo_details, github_search, github_trending


@pytest.mark.asyncio
async def test_github_search_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_repo = Repository(
        name="test/repo",
        url="https://github.com/test/repo",
        stars=42,
        language="Python",
        description="A great library",
    )

    async def fake_search(query: str, limit: int = 5) -> list[Repository]:
        return [sample_repo]

    monkeypatch.setattr("app.tools.search_repositories", fake_search)

    # Test the coroutine directly (content, artifact)
    text, artifacts = await github_search.coroutine("python")  # type: ignore[attr-defined]
    assert "test/repo" in text
    assert len(artifacts) == 1
    assert artifacts[0]["name"] == "test/repo"
    assert artifacts[0]["stars"] == 42

    # Test tool invocation returning formatted text
    invoked_text = await github_search.ainvoke({"query": "python"})
    assert "test/repo" in invoked_text


@pytest.mark.asyncio
async def test_github_repo_details_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_repo = Repository(
        name="test/repo",
        full_name="test/repo",
        url="https://github.com/test/repo",
        stars=100,
        forks=20,
        language="TypeScript",
        license="MIT",
        description="Detailed repo",
    )

    async def fake_details(owner: str, repo: str) -> Repository:
        return sample_repo

    monkeypatch.setattr("app.tools.get_repository_details", fake_details)

    text, artifacts = await github_repo_details.coroutine("test", "repo")  # type: ignore[attr-defined]
    assert "test/repo" in text
    assert "Stars: 100" in text
    assert "TypeScript" in text
    assert len(artifacts) == 1

    invoked_text = await github_repo_details.ainvoke({"owner": "test", "repo": "repo"})
    assert "test/repo" in invoked_text


@pytest.mark.asyncio
async def test_github_trending_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_repo = Repository(
        name="starter/template",
        url="https://github.com/starter/template",
        stars=500,
        language="Python",
        description="Starter template",
    )

    async def fake_search(query: str, limit: int = 5) -> list[Repository]:
        return [sample_repo]

    monkeypatch.setattr("app.tools.search_repositories", fake_search)

    text, artifacts = await github_trending.coroutine("starter", "Python")  # type: ignore[attr-defined]
    assert "starter/template" in text
    assert len(artifacts) == 1

    invoked_text = await github_trending.ainvoke({"topic": "starter", "language": "Python"})
    assert "starter/template" in invoked_text
