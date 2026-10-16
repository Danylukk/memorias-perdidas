"""Contrato do provider da OpenAI, agora exclusivo do backend."""
from types import SimpleNamespace
from unittest.mock import MagicMock
import httpx
import pytest
from openai import APIConnectionError, APITimeoutError, AuthenticationError, InternalServerError
from backend.config import ConfigurationError, Settings
from backend.models import GenerationInput
from backend.providers.openai_provider import AIClientError, OpenAIProvider


@pytest.fixture
def sdk(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("backend.providers.openai_provider.OpenAI", factory)
    monkeypatch.setattr(Settings, "validate", lambda self: None)
    client = factory.return_value.__enter__.return_value
    client.responses.create.return_value = SimpleNamespace(status="completed", output_text="Ainda respiro.")
    return factory, client


def prompt():
    return GenerationInput(instructions="Interprete Darian.", context="Kael ajudou.")


def test_one_sdk_request_and_text_only(sdk):
    factory, client = sdk
    assert OpenAIProvider(Settings(model="modelo-configurado")).generate(prompt()) == "Ainda respiro."
    factory.assert_called_once_with(api_key="", base_url="https://api.openai.com/v1", timeout=25.0, max_retries=0)
    client.responses.create.assert_called_once_with(
        model="modelo-configurado", instructions="Interprete Darian.",
        input="Kael ajudou.", max_output_tokens=512, store=False,
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
        OpenAIProvider(Settings()).generate(prompt())
    assert "detalhe privado" not in str(error.value)
    assert client.responses.create.call_count == 1


@pytest.mark.parametrize("status,text", [("incomplete", "Ainda respiro."), ("completed", ""), ("completed", None)])
def test_incomplete_or_empty_response_is_failure(sdk, status, text):
    _, client = sdk
    client.responses.create.return_value = SimpleNamespace(status=status, output_text=text)
    with pytest.raises(AIClientError):
        OpenAIProvider(Settings()).generate(prompt())


def test_missing_config_does_not_construct_sdk(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("backend.providers.openai_provider.OpenAI", factory)
    with pytest.raises(ConfigurationError):
        OpenAIProvider(Settings()).generate(prompt())
    factory.assert_not_called()


def test_provider_preserves_structured_outputs(sdk):
    _, client = sdk
    schema = {"type": "object", "properties": {"fala": {"type": "string"}}}
    value = prompt().model_copy(update={"response_schema": schema})
    OpenAIProvider(Settings()).generate(value)
    assert client.responses.create.call_args.kwargs["text"]["format"] == {
        "type": "json_schema", "name": "turno_darian", "schema": schema, "strict": True}


def test_env_loading_and_missing_config(monkeypatch, tmp_path):
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "modelo-do-ambiente")
    monkeypatch.setattr("backend.config.BACKEND_ROOT", tmp_path)
    (tmp_path / ".env").write_text("OPENAI_MODEL=modelo-do-arquivo\n", encoding="utf-8")
    settings = Settings.from_env()
    assert settings.model == "modelo-do-ambiente"
    assert settings.api_key == "" and "api_key" not in repr(settings)
    with pytest.raises(ConfigurationError):
        settings.validate()
    monkeypatch.delenv("OPENAI_MODEL")
    assert Settings.from_env().model == "modelo-do-arquivo"
