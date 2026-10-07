import asyncio
import json

import anthropic

from .config import settings
from .github_tools import GitHubError, ToolBox
from .prompts import SYSTEM_PROMPT

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_repo = {"owner": {"type": "string"}, "repo": {"type": "string"}}
TOOLS = [
    {"name": "search_repositories",
     "description": "Search GitHub repositories. Use several different queries. Returns metadata only.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}, "language": {"type": "string"},
         "min_stars": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["query"]}},
    {"name": "get_repo_overview",
     "description": "Verified metadata: license, languages, topics, activity, archived status.",
     "input_schema": {"type": "object", "properties": _repo, "required": ["owner", "repo"]}},
    {"name": "get_readme",
     "description": "Read the repository README (truncated).",
     "input_schema": {"type": "object", "properties": _repo, "required": ["owner", "repo"]}},
    {"name": "list_repository_tree",
     "description": "List files in the repository to understand structure, tests, and dependency files.",
     "input_schema": {"type": "object", "properties": _repo, "required": ["owner", "repo"]}},
    {"name": "get_file",
     "description": "Read one text file from the repository (truncated).",
     "input_schema": {"type": "object", "properties": {**_repo, "path": {"type": "string"}},
                      "required": ["owner", "repo", "path"]}},
    {"name": "score_repository",
     "description": ("Compute the project-fit score in code. Requires get_repo_overview and get_readme first. "
                     "requirements: {technologies: [str], difficulty: beginner|medium|advanced}. "
                     "judgments: {requirement_match: 0-1, evidence: [short quotes/file names], "
                     "repo_difficulty: beginner|medium|advanced, has_demo: bool, setup_risk: 0-1}."),
     "input_schema": {"type": "object", "properties": {
         **_repo, "requirements": {"type": "object"}, "judgments": {"type": "object"}},
         "required": ["owner", "repo", "requirements", "judgments"]}},
]

MAX_RESULT_CHARS = 14000
MAX_HISTORY = 80


class Session:
    def __init__(self):
        self.history = []
        self.toolbox = ToolBox()
        self.lock = asyncio.Lock()


SESSIONS = {}  # In-memory. Move to PostgreSQL/Redis before multi-instance deployment.


def get_session(session_id):
    if session_id not in SESSIONS:
        if len(SESSIONS) >= 500:
            SESSIONS.pop(next(iter(SESSIONS)))
        SESSIONS[session_id] = Session()
    return SESSIONS[session_id]


async def run_agent(session_id, user_message):
    s = get_session(session_id)
    async with s.lock:
        if len(s.history) > MAX_HISTORY:
            yield {"type": "final", "text": "This conversation is getting long. Please start a new session."}
            return
        s.history.append({"role": "user", "content": user_message})
        for _ in range(settings.max_steps):
            resp = await client.messages.create(
                model=settings.model, max_tokens=2500, system=SYSTEM_PROMPT,
                tools=TOOLS, messages=s.history)
            s.history.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                yield {"type": "final", "text": "".join(b.text for b in resp.content if b.type == "text")}
                return
            results = []
            for b in resp.content:
                if b.type != "tool_use":
                    continue
                yield {"type": "status", "tool": b.name, "input": b.input}
                try:
                    out = await s.toolbox.run(b.name, b.input)
                    payload = {"source": "tool_output", "untrusted_content": out}
                    err = False
                except (GitHubError, TypeError, KeyError, ValueError) as e:
                    payload, err = {"error": str(e)}, True
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": json.dumps(payload, default=str)[:MAX_RESULT_CHARS], "is_error": err})
            s.history.append({"role": "user", "content": results})
        yield {"type": "final", "text": "I reached my step limit for this question. Ask me to continue, or narrow the request."}
