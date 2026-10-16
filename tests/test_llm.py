"""Model configuration tests that never make a provider request."""

import pytest

from app.llm import MissingConfigError, build_model


def test_model_requires_server_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("app.llm.google_api_key", lambda: None)
    with pytest.raises(MissingConfigError, match="GOOGLE_API_KEY"):
        build_model()


def test_model_uses_configured_gemini_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-never-used-for-network")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")

    model = build_model()
    assert model.model == "gemini-2.5-pro"
    assert model.temperature == 0.2
