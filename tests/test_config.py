import pytest
from pydantic_ai.models.openai import OpenAIChatModel

from app import config


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
