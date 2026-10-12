# tests/test_api.py
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import main
from app.agent import AgentResult
from app.schemas import Repository

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def fake_agent(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    async def fake_run_chat(agent: object, message: str, history: object = ()) -> AgentResult:
        repo = Repository(name="a/b", url="https://github.com/a/b", stars=3)
        return AgentResult("Found one.", "github_search", [repo])

    monkeypatch.setattr(main, "run_chat", fake_run_chat)
    main.app.dependency_overrides[main.agent_dependency] = lambda: object()
    yield
    main.app.dependency_overrides.clear()


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_schema() -> None:
    body = client.post("/chat", json={"message": "find repos"}).json()
    assert body["tool_used"] == "github_search"
    assert body["repositories"][0]["name"] == "a/b"


@pytest.mark.parametrize("message", ["", "   ", "x" * 2001])
def test_invalid_message_rejected(message: str) -> None:
    assert client.post("/chat", json={"message": message}).status_code == 422


def test_malformed_json_rejected() -> None:
    res = client.post("/chat", content="{oops", headers={"Content-Type": "application/json"})
    assert res.status_code == 422


def test_missing_key_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    main.app.dependency_overrides.clear()
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("app.llm.google_api_key", lambda: None)
    res = client.post("/chat", json={"message": "hi"})
    assert res.status_code == 503
    assert "GOOGLE_API_KEY" not in res.text
