"""Model configuration tests that never make a provider request."""

import pytest

from app.llm import MissingConfigError, build_model


def test_model_requires_server_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingConfigError, match="OPENAI_API_KEY"):
        build_model()


def test_model_uses_configured_name_and_bounded_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-never-used-for-network")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    model = build_model()

    assert model.model_name == "test-model"
    assert model.max_tokens == 1024
    assert model.temperature == 0
