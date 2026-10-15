"""Cliente HTTP da API do grupo. O jogo não importa o SDK da OpenAI."""
import requests
from game.config import ConfigurationError, Settings
from game.systems.prompt_builder import DialoguePrompt


class AIClientError(Exception):
    pass


class NarrativeAPIClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, prompt: DialoguePrompt) -> str:
        try:
            self.settings.validate()
            response = requests.post(
                self.settings.api_url.rstrip("/") + "/v1/ia-generativa/texto",
                headers={"X-API-Key": self.settings.api_key},
                json={"instructions": prompt.instructions, "context": prompt.context,
                      "response_schema": prompt.schema, "max_output_tokens": prompt.max_output_tokens},
                timeout=self.settings.timeout, allow_redirects=False,
            )
            if response.status_code != 200:
                raise AIClientError("API indisponível. Verifique o backend e sua credencial de acesso.")
            text = response.json()["texto"]
            if not isinstance(text, str) or not text.strip():
                raise AIClientError("A API retornou uma resposta vazia.")
            return text
        except ConfigurationError:
            raise AIClientError("Configure API_URL e API_KEY no frontend/.env e reinicie o jogo.") from None
        except (requests.RequestException, ValueError, KeyError, TypeError):
            raise AIClientError("Não foi possível consultar a API do grupo.") from None
