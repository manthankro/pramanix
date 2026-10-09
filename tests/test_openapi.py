"""Basic API tests."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_docs_available() -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
