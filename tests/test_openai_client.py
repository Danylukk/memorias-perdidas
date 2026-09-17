from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, APITimeoutError, AuthenticationError, InternalServerError

from game.config import ConfigurationError, Settings
from game.models.state import new_game
from game.systems.choices import get_choice
from game.systems.openai_client import AIClientError, OpenAIClient
from game.systems.prompt_builder import PromptBuilder


@pytest.fixture
def sdk(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("game.systems.openai_client.OpenAI", factory)
    # Sem chave, inclusive fictícia. Somente testes isolados do adaptador pulam a validação.
    monkeypatch.setattr(Settings, "validate", lambda self: None)
    client = factory.return_value.__enter__.return_value
    client.responses.create.return_value = SimpleNamespace(status="completed", output_text="Ainda respiro.")
    return factory, client


def test_one_sdk_request_and_text_only(sdk):
    factory, sdk_client = sdk
    prompt = PromptBuilder().build(new_game(), get_choice(1))
    assert OpenAIClient(Settings(model="modelo-configurado")).generate(prompt) == "Ainda respiro."
    factory.assert_called_once_with(api_key="", base_url="https://api.openai.com/v1", timeout=25.0, max_retries=0)
    sdk_client.responses.create.assert_called_once_with(
        model="modelo-configurado", instructions=prompt.instructions,
        input=prompt.context, max_output_tokens=512, store=False,
    )


@pytest.mark.parametrize("error_kind", ["connection", "timeout", "authentication", "http", "sdk", "unexpected"])
def test_controlled_errors_without_retries(sdk, error_kind):
    _, client = sdk
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    errors = {
        "connection": APIConnectionError(request=request),
        "timeout": APITimeoutError(request=request),
        "authentication": AuthenticationError("detalhe privado", response=httpx.Response(401, request=request), body=None),
        "http": InternalServerError("detalhe privado", response=httpx.Response(503, request=request), body=None),
        "sdk": ValueError("detalhe privado"),
        "unexpected": AttributeError("detalhe privado"),
    }
    client.responses.create.side_effect = errors[error_kind]
    with pytest.raises(AIClientError) as error:
        OpenAIClient(Settings()).generate(PromptBuilder().build(new_game(), get_choice(1)))
    assert "detalhe privado" not in str(error.value)
    assert client.responses.create.call_count == 1


def test_incomplete_response_is_failure(sdk):
    _, client = sdk
    client.responses.create.return_value.status = "incomplete"
    with pytest.raises(AIClientError, match="não foi concluída"):
        OpenAIClient(Settings()).generate(PromptBuilder().build(new_game(), get_choice(1)))


def test_missing_config_does_not_construct_sdk(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("game.systems.openai_client.OpenAI", factory)
    with pytest.raises(AIClientError, match="Configure"):
        OpenAIClient(Settings()).generate(PromptBuilder().build(new_game(), get_choice(1)))
    factory.assert_not_called()


def test_env_loading_and_missing_config(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "modelo-do-ambiente")
    monkeypatch.setattr("game.config.PROJECT_ROOT", tmp_path)
    (tmp_path / ".env").write_text("OPENAI_MODEL=modelo-do-arquivo\n", encoding="utf-8")
    settings = Settings.from_env()
    assert settings.model == "modelo-do-ambiente"
    assert settings.api_key == ""
    assert "api_key" not in repr(settings)
    with pytest.raises(ConfigurationError):
        settings.validate()
    monkeypatch.delenv("OPENAI_MODEL")
    assert Settings.from_env().model == "modelo-do-arquivo"
