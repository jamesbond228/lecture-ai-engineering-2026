import pytest
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel

from app import config


def test_gemini_is_primary_with_openrouter_fallback_when_both_keys_are_set(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-key")

    model = config.build_model()

    assert isinstance(model, FallbackModel)
    assert isinstance(model.models[0], GoogleModel)
    assert model.models[0].model_name == config.DEFAULT_MODEL
    assert isinstance(model.models[1], OpenAIChatModel)
    assert model.models[1].model_name == config.DEFAULT_OPENROUTER_MODEL


def test_gemini_works_without_configuring_optional_fallback(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    assert isinstance(config.build_model(), GoogleModel)


def test_openrouter_provider_builds_openai_compatible_model(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    model = config.build_model("baidu/ernie-5.5-flash-preview:free")

    assert isinstance(model, OpenAIChatModel)
    assert model.model_name == "baidu/ernie-5.5-flash-preview:free"


def test_openrouter_provider_requires_its_api_key(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit, match="OPENROUTER_API_KEY"):
        config.build_model("baidu/ernie-5.5-flash-preview:free")
