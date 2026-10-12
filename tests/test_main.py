"""API contract and validation tests without external model calls."""

from typing import Any

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.main import agent_dependency, app


class FakeAgent:
    async def ainvoke(self, state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        del config
        return {"messages": [*state["messages"], AIMessage(content="A mocked helpful answer.")]}


def configured_client() -> TestClient:
    app.dependency_overrides[agent_dependency] = FakeAgent
    return TestClient(app)


def test_health() -> None:
    with configured_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_includes_typed_repository_results() -> None:
    with configured_client() as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/chat" in response.json()["paths"]
    assert "repositories" in str(response.json()["components"]["schemas"])


def test_chat_returns_model_answer_and_empty_repository_list() -> None:
    with configured_client() as client:
        response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {
        "response": "A mocked helpful answer.",
        "tool_used": None,
        "repositories": [],
    }


def test_chat_validates_message_length_and_blank_content() -> None:
    with configured_client() as client:
        blank = client.post("/chat", json={"message": "   "})
        too_long = client.post("/chat", json={"message": "x" * 2001})
    assert blank.status_code == 422
    assert too_long.status_code == 422
