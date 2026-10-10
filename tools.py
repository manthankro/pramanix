"""Tools the model may call. Read-only, fixed endpoints only."""

from typing import Any

from langchain_core.tools import BaseTool, tool

from app.github_search import GitHubSearchError, search_repositories


@tool(response_format="content_and_artifact")
async def github_search(query: str) -> tuple[str, list[dict[str, Any]]]:
    """Search public GitHub repositories. Use when the user asks to find,
    suggest or compare repositories or project ideas. Pass a short search
    query such as "library management system language:Python"."""
    try:
        repos = await search_repositories(query, limit=5)
    except GitHubSearchError as exc:
        return f"GitHub search failed: {exc}", []
    if not repos:
        return "No repositories found for that query.", []
    lines = [
        f"{r.name} | {r.language or 'n/a'} | {r.stars} stars | "
        f"{r.description or 'no description'}"
        for r in repos
    ]
    return "\n".join(lines), [r.model_dump() for r in repos]


TOOLS: list[BaseTool] = [github_search]
