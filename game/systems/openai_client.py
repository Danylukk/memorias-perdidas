from openai import OpenAI, OpenAIError

from game.config import ConfigurationError, Settings
from game.systems.prompt_builder import DialoguePrompt


class AIClientError(Exception):
    """Erro sanitizado, sem detalhes do SDK ou credenciais."""


class OpenAIClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, prompt: DialoguePrompt) -> str:
        try:
            self.settings.validate()
            # Cliente local à thread; uma requisição por ação, sem retries do SDK.
            with OpenAI(
                api_key=self.settings.api_key,
                base_url="https://api.openai.com/v1",
                timeout=self.settings.timeout,
                max_retries=0,
            ) as client:
                response = client.responses.create(
                    model=self.settings.model,
                    instructions=prompt.instructions,
                    input=prompt.context,
                    max_output_tokens=512,
                    store=False,
                )
            if response.status != "completed":
                raise AIClientError("A geração não foi concluída.")
            return response.output_text
        except ConfigurationError:
            raise AIClientError("Configure OPENAI_API_KEY e OPENAI_MODEL no .env e reinicie o jogo.") from None
        except (OpenAIError, OSError, ValueError, TypeError, AttributeError):
            # Nunca incluir str(exc): erros do provedor podem conter dados sensíveis.
            raise AIClientError("Verifique a conexão e a configuração da IA.") from None
