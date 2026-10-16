"""The tools that the assistant is allowed to call."""

import json

from langchain_core.tools import tool

from app.github_search import search_repositories


@tool
async def github_search(query: str) -> str:
    """Search public GitHub repositories for project ideas, libraries, or examples."""
    repositories = await search_repositories(query, limit=5)
    return json.dumps(repositories, ensure_ascii=False)


TOOLS = [github_search]
