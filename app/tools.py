"""Tools the model may call. Read-only, fixed endpoints only."""

from typing import Any

from langchain_core.tools import BaseTool, tool

from app.github_search import GitHubSearchError, get_repository_details, search_repositories


@tool(response_format="content_and_artifact")
async def github_search(query: str) -> tuple[str, list[dict[str, Any]]]:
    """Search public GitHub repositories. Use when the user asks to find,
    suggest, explore or compare repositories, libraries, or project ideas.
    Pass a concise search query such as "fastapi langgraph template" or
    "student management system language:Python".
    """
    try:
        repos = await search_repositories(query, limit=5)
    except GitHubSearchError as exc:
        return f"GitHub search failed: {exc}", []

    if not repos:
        return "No repositories found for that query.", []

    lines = [
        f"{r.full_name or r.name} | {r.language or 'n/a'} | {r.stars} stars | {r.description or 'no description'}"
        for r in repos
    ]
    return "\n".join(lines), [r.model_dump() for r in repos]


@tool(response_format="content_and_artifact")
async def github_repo_details(owner: str, repo: str) -> tuple[str, list[dict[str, Any]]]:
    """Get detailed information about a specific GitHub repository.
    Use when the user asks about an exact repo, e.g. 'tell me more about tiangolo/fastapi'
    or 'inspect langchain-ai/langgraph'.
    """
    try:
        r = await get_repository_details(owner, repo)
    except GitHubSearchError as exc:
        return f"Failed to retrieve repository {owner}/{repo}: {exc}", []

    summary = (
        f"Repository: {r.full_name or r.name}\n"
        f"URL: {r.url}\n"
        f"Stars: {r.stars} | Forks: {r.forks}\n"
        f"Language: {r.language or 'n/a'} | License: {r.license or 'None specified'}\n"
        f"Topics: {', '.join(r.topics) if r.topics else 'None'}\n"
        f"Description: {r.description or 'No description provided'}"
    )
    return summary, [r.model_dump()]


@tool(response_format="content_and_artifact")
async def github_trending(
    topic: str = "starter", language: str = ""
) -> tuple[str, list[dict[str, Any]]]:
    """Discover popular open-source projects, templates, and learning starters for students.
    Use when the user asks for trending projects, recommended templates, or starter kits.
    """
    query_parts = [topic]
    if language:
        query_parts.append(f"language:{language}")
    query = " ".join(query_parts)

    try:
        repos = await search_repositories(query, limit=5)
    except GitHubSearchError as exc:
        return f"Trending lookup failed: {exc}", []

    if not repos:
        return f"No projects found matching topic '{topic}'.", []

    lines = [
        f"{r.full_name or r.name} | {r.language or 'n/a'} | {r.stars} stars | {r.description or 'no description'}"
        for r in repos
    ]
    return "\n".join(lines), [r.model_dump() for r in repos]


TOOLS: list[BaseTool] = [github_search, github_repo_details, github_trending]
