"""Verifica autenticação, contrato e o consumo do FastAPI pelo cliente real do jogo."""
import json
from unittest.mock import MagicMock
import pytest
import requests
from fastapi.testclient import TestClient
from backend.config import Settings as BackendSettings, ConfigurationError
from backend.main import create_app
from backend.providers.openai_provider import AIClientError as ProviderError
from game.config import Settings
from game.models.state import new_game
from game.systems.api_client import AIClientError, NarrativeAPIClient
from game.systems.choices import get_choice
from game.systems.dialogue import DialogueService
from game.systems.prompt_builder import PromptBuilder

KEY = "credencial-apenas-de-teste"
PATH = "/v1/ia-generativa/texto"
PAYLOAD = {"instructions": "Interprete Darian.", "context": "Kael ajudou."}


@pytest.fixture
def api():
    app = create_app(BackendSettings(access_key=KEY, cors_origins=("http://localhost:8501",)))
    app.state.provider = MagicMock()
    app.state.provider.generate.return_value = "Ainda respiro."
    with TestClient(app) as client:
        yield app, client


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "errada"}])
def test_unauthorized_never_calls_provider(api, headers):
    app, client = api
    assert client.post(PATH, json=PAYLOAD, headers=headers).status_code == 401
    app.state.provider.generate.assert_not_called()


def test_unconfigured_access_key_fails_closed():
    app = create_app(BackendSettings())
    app.state.provider = MagicMock()
    with TestClient(app) as client:
        assert client.post(PATH, json=PAYLOAD, headers={"X-API-Key": KEY}).status_code == 503
    app.state.provider.generate.assert_not_called()


def test_authenticated_generation_and_swagger(api):
    app, client = api
    response = client.post(PATH, json=PAYLOAD, headers={"X-API-Key": KEY})
    assert response.status_code == 200 and response.json() == {"texto": "Ainda respiro."}
    assert app.state.provider.generate.call_args.args[0].context == PAYLOAD["context"]
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    assert spec["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "X-API-Key"
    assert spec["paths"][PATH]["post"]["security"] == [{"APIKeyHeader": []}]


@pytest.mark.parametrize("change", [
    {"context": ""}, {"max_output_tokens": 0}, {"max_output_tokens": 1601},
    {"instructions": "x" * 12001}, {"model": "nao-permitido"},
])
def test_invalid_payload_never_calls_provider(api, change):
    app, client = api
    assert client.post(PATH, json=PAYLOAD | change, headers={"X-API-Key": KEY}).status_code == 422
    app.state.provider.generate.assert_not_called()


@pytest.mark.parametrize("error,status", [(ProviderError("segredo"), 502), (ConfigurationError("segredo"), 503)])
def test_safe_backend_errors(api, error, status):
    app, client = api
    app.state.provider.generate.side_effect = error
    response = client.post(PATH, json=PAYLOAD, headers={"X-API-Key": KEY})
    assert response.status_code == status and "segredo" not in response.text


def test_cors_only_allows_configured_origin(api):
    _, client = api
    headers = {"Origin": "http://localhost:8501", "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "X-API-Key,Content-Type"}
    response = client.options(PATH, headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"
    response = client.options(PATH, headers=headers | {"Origin": "https://outro.example"})
    assert response.status_code == 400 and "access-control-allow-origin" not in response.headers


def test_game_client_to_fastapi_preserves_turn_and_memory(api, monkeypatch):
    app, client = api
    requests_seen = []
    def post(url, **kwargs):
        requests_seen.append((url, kwargs))
        return client.post(PATH, json=kwargs["json"], headers=kwargs["headers"])
    monkeypatch.setattr("game.systems.api_client.requests.post", post)
    turn = {"fala": "Ainda respiro.", "opcoes": [
        {"texto": label, "intencao": intent} for label, intent in [
            ("Quem é você?", "curiosidade"), ("Vou ajudar.", "empatia"),
            ("Fico com você.", "lealdade"), ("Fale logo.", "agressividade")]]}
    app.state.provider.generate.return_value = json.dumps(turn)
    service = DialogueService(NarrativeAPIClient(Settings(api_key=KEY)))
    result = service.converse(new_game(), get_choice(3))
    assert result.ok and result.source == "ia" and len(result.options) == 4
    url, options = requests_seen[-1]
    assert url == "http://127.0.0.1:8000" + PATH
    assert options["headers"] == {"X-API-Key": KEY}
    assert options["timeout"] == 30.0 and options["allow_redirects"] is False
    assert app.state.provider.generate.call_args.args[0].response_schema is not None
    from game.systems.fragments import get_fragment
    app.state.provider.generate.return_value = "Vi brasas entre as pedras."
    assert service.remember(new_game(), get_fragment("a_batalha")).ok
    assert app.state.provider.generate.call_args.args[0].response_schema is None
    assert len(requests_seen) == 2


@pytest.mark.parametrize("status,body", [
    (401, {"detail": "segredo"}), (502, {"detail": "segredo"}), (307, {}),
    (200, {}), (200, {"texto": None}), (200, {"texto": ""}), (200, {"texto": 2}),
])
def test_client_rejects_http_errors_and_invalid_responses(monkeypatch, status, body):
    response = MagicMock(status_code=status)
    response.json.return_value = body
    monkeypatch.setattr("game.systems.api_client.requests.post", MagicMock(return_value=response))
    with pytest.raises(AIClientError) as error:
        NarrativeAPIClient(Settings(api_key=KEY)).generate(PromptBuilder().build(new_game(), get_choice(1)))
    assert "segredo" not in str(error.value)


@pytest.mark.parametrize("error", [requests.Timeout("segredo"), requests.ConnectionError("segredo"),
                                  ValueError("segredo")])
def test_client_errors_use_existing_offline_fallback(monkeypatch, error):
    monkeypatch.setattr("game.systems.api_client.requests.post", MagicMock(side_effect=error))
    service = DialogueService(NarrativeAPIClient(Settings(api_key=KEY)))
    result = service.converse(new_game(), get_choice(3))
    assert not result.ok and "segredo" not in result.error


def test_client_without_key_never_sends_request(monkeypatch):
    post = MagicMock()
    monkeypatch.setattr("game.systems.api_client.requests.post", post)
    with pytest.raises(AIClientError):
        NarrativeAPIClient(Settings()).generate(PromptBuilder().build(new_game(), get_choice(1)))
    post.assert_not_called()


def test_frontend_reads_only_group_api_configuration(monkeypatch, tmp_path):
    monkeypatch.setattr("game.config.PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "nao-deve-ser-usada-pelo-jogo")
    (tmp_path / ".env").write_text("API_KEY=chave-local\nAPI_URL=http://localhost:8001\n", encoding="utf-8")
    settings = Settings.from_env()
    assert settings.api_key == "chave-local" and settings.api_url == "http://localhost:8001"
    assert "chave-local" not in repr(settings)
