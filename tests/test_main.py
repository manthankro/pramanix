"""Tests for the FastAPI server."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_without_tool() -> None:
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json()["tool_used"] is None


def test_chat_with_tool() -> None:
    response = client.post("/chat", json={"message": "search github"})
    assert response.status_code == 200
    assert response.json()["tool_used"] == "github_search"
