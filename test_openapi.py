"""Basic API tests. Adjust the import and routes to match your app."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_docs_available() -> None:
    """FastAPI serves OpenAPI docs by default."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


# Example for a chat endpoint with the LLM mocked out:
#
# def test_chat(monkeypatch) -> None:
#     monkeypatch.setattr("app.main.run_agent", lambda msg: "mocked reply")
#     response = client.post("/chat", json={"message": "hello"})
#     assert response.status_code == 200
#     assert response.json()["response"] == "mocked reply"
