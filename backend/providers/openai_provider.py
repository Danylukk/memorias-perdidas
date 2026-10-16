"""Único ponto de comunicação com a OpenAI; não depende do jogo ou do FastAPI."""
from openai import OpenAI, OpenAIError
from backend.config import Settings
from backend.models import GenerationInput


class AIClientError(Exception):
    """Erro sanitizado, sem detalhes do SDK ou credenciais."""


class OpenAIProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, prompt: GenerationInput) -> str:
        self.settings.validate()
        try:
            with OpenAI(api_key=self.settings.api_key, base_url="https://api.openai.com/v1",
                        timeout=self.settings.timeout, max_retries=0) as client:
                options = {}
                if prompt.response_schema is not None:
                    options["text"] = {"format": {"type": "json_schema", "name": "turno_darian",
                                                  "schema": prompt.response_schema, "strict": True}}
                response = client.responses.create(
                    model=self.settings.model, instructions=prompt.instructions,
                    input=prompt.context, max_output_tokens=prompt.max_output_tokens,
                    store=False, **options,
                )
            if response.status != "completed" or not response.output_text.strip():
                raise AIClientError("A geração não foi concluída.")
            return response.output_text
        except (OpenAIError, OSError, ValueError, TypeError, AttributeError):
            raise AIClientError("Não foi possível consultar a IA generativa.") from None
