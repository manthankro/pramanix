import asyncio
import base64
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx

from . import scoring
from .config import settings

API = "https://api.github.com"
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
LANG_RE = re.compile(r"[^A-Za-z0-9+#.\- ]")
NOISE = ("node_modules/", ".git/", "dist/", "build/", "__pycache__/", "venv/", ".venv/", "vendor/")
BINARY = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".jar", ".pyc", ".db", ".sqlite", ".h5", ".pt", ".ckpt", ".mp4")
TEXT_LIMIT = 6000


class GitHubError(Exception):
    pass


def _dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _check(owner, repo):
    if not (isinstance(owner, str) and isinstance(repo, str) and NAME_RE.match(owner) and NAME_RE.match(repo)):
        raise GitHubError("Invalid owner/repo name.")
    return f"{owner}/{repo}"


class GitHubClient:
    def __init__(self):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self.http = httpx.AsyncClient(base_url=API, headers=headers, timeout=20)
        self._cache = {}

    async def get(self, path, params=None):
        key = (path, tuple(sorted((params or {}).items())))
        hit = self._cache.get(key)
        if hit and hit[0] > time.time():
            return hit[1]
        try:
            r = await self.http.get(path, params=params)
        except httpx.HTTPError as e:
            raise GitHubError(f"GitHub request failed: {type(e).__name__}")
        if r.status_code in (403, 429) and r.headers.get("x-ratelimit-remaining") == "0":
            raise GitHubError("GitHub rate limit reached. Try again later.")
        if r.status_code == 404:
            raise GitHubError("Not found on GitHub.")
        if r.status_code >= 400:
            raise GitHubError(f"GitHub returned status {r.status_code}.")
        data = r.json()
        if len(self._cache) > 2000:
            self._cache.clear()
        self._cache[key] = (time.time() + settings.cache_ttl, data)
        return data


gh = GitHubClient()


class ToolBox:
    """One per chat session. Stores verified facts so scoring cannot be fed fake metadata."""

    def __init__(self):
        self.facts = {}

    async def run(self, name, args):
        fn = getattr(self, f"t_{name}", None)
        if fn is None:
            raise GitHubError(f"Unknown tool: {name}")
        return await fn(**args)

    async def t_search_repositories(self, query, language=None, min_stars=0, limit=8):
        q = f"{str(query)[:200]} archived:false"
        if language:
            q += f" language:{LANG_RE.sub('', str(language))}"
        if min_stars:
            q += f" stars:>={int(min_stars)}"
        data = await gh.get("/search/repositories", {"q": q, "per_page": max(1, min(int(limit), 10))})
        return {
            "total_found": data.get("total_count", 0),
            "results": [{
                "full_name": r["full_name"], "description": r.get("description"),
                "stars": r["stargazers_count"], "language": r.get("language"),
                "last_push": r.get("pushed_at"), "topics": r.get("topics", []),
                "license": (r.get("license") or {}).get("spdx_id"),
            } for r in data.get("items", [])],
        }

    async def t_get_repo_overview(self, owner, repo):
        full = _check(owner, repo)
        r, langs, commits = await asyncio.gather(
            gh.get(f"/repos/{full}"), gh.get(f"/repos/{full}/languages"),
            gh.get(f"/repos/{full}/commits", {"per_page": 30}))
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=90)
        recent = 0
        for c in commits if isinstance(commits, list) else []:
            try:
                if _dt(c["commit"]["committer"]["date"]) >= cutoff:
                    recent += 1
            except (KeyError, TypeError, ValueError):
                pass
        overview = {
            "full_name": r["full_name"], "description": r.get("description"),
            "stars": r["stargazers_count"], "forks": r["forks_count"],
            "open_issues": r["open_issues_count"], "archived": r["archived"],
            "default_branch": r["default_branch"], "topics": r.get("topics", []),
            "languages": langs, "license_spdx": (r.get("license") or {}).get("spdx_id"),
            "days_since_push": (now - _dt(r["pushed_at"])).days,
            "commits_90d": recent, "homepage": r.get("homepage"),
        }
        self.facts.setdefault(full, {})["overview"] = overview
        return overview

    async def t_get_readme(self, owner, repo):
        full = _check(owner, repo)
        data = await gh.get(f"/repos/{full}/readme")
        text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        self.facts.setdefault(full, {})["readme"] = text[:50000]
        return {"readme": text[:TEXT_LIMIT], "truncated": len(text) > TEXT_LIMIT}

    async def t_list_repository_tree(self, owner, repo):
        full = _check(owner, repo)
        f = self.facts.setdefault(full, {})
        branch = (f.get("overview") or {}).get("default_branch") or (await gh.get(f"/repos/{full}"))["default_branch"]
        data = await gh.get(f"/repos/{full}/git/trees/{quote(branch)}", {"recursive": "1"})
        paths = [t["path"] for t in data.get("tree", [])
                 if t["type"] == "blob" and not any(n in "/" + t["path"] + "/" for n in NOISE)]
        f["tree"] = paths
        return {"total_files": len(paths), "files": paths[:200], "truncated": len(paths) > 200}

    async def t_get_file(self, owner, repo, path):
        full = _check(owner, repo)
        if not isinstance(path, str) or ".." in path or path.startswith("/") or len(path) > 200:
            raise GitHubError("Invalid file path.")
        if path.lower().endswith(BINARY):
            raise GitHubError("Binary files are not readable.")
        data = await gh.get(f"/repos/{full}/contents/{quote(path)}")
        if isinstance(data, list):
            raise GitHubError("That path is a directory.")
        if data.get("size", 0) > 200_000:
            raise GitHubError("File too large to read.")
        text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return {"path": path, "content": text[:TEXT_LIMIT], "truncated": len(text) > TEXT_LIMIT}

    async def t_score_repository(self, owner, repo, requirements, judgments):
        full = _check(owner, repo)
        f = self.facts.get(full, {})
        if "overview" not in f or "readme" not in f:
            raise GitHubError("Call get_repo_overview and get_readme for this repository before scoring it.")
        return scoring.score_repository(f["overview"], f["readme"], f.get("tree"), requirements, judgments)
