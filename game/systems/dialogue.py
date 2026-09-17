import logging
import re
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from game.models.state import GameState
from game.systems.choices import Choice
from game.systems.prompt_builder import DialoguePrompt, PromptBuilder

logger = logging.getLogger(__name__)
ERROR_MESSAGE = "Não foi possível gerar a resposta de Darian. Verifique a conexão e a configuração da IA."
MAX_RESPONSE_LENGTH = 360


class NarrativeClient(Protocol):
    def generate(self, prompt: DialoguePrompt) -> str: ...


@dataclass(frozen=True)
class DialogueResult:
    text: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


def validate_response(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("Resposta inválida.")
    text = " ".join(raw.split())
    # Aspas externas são formatação, não uma terceira frase após o ponto final.
    if len(text) >= 2 and (text[0], text[-1]) in (("“", "”"), ('"', '"'), ("«", "»")):
        text = text[1:-1].strip()
    if not text or len(text) > MAX_RESPONSE_LENGTH:
        raise ValueError("Resposta vazia ou longa demais.")
    if any(mark in text for mark in ("{", "}", "[", "]", "`", "<", ">", "**")):
        raise ValueError("Formato inválido.")
    if re.search(r"\b(IA|ChatGPT|OpenAI|LLM|prompt|modelo|instruções)\b", text, re.IGNORECASE):
        raise ValueError("Metalinguagem inválida.")
    if re.search(r"\b(vida|energia|empatia|agressividade|curiosidade|egoísmo|egoismo|lealdade|confiança|fragmentos)\s*[:=+\-]", text, re.IGNORECASE):
        raise ValueError("Comando de estado inválido.")
    sentence_text = re.sub(r"\.{2,}", "…", text)
    sentences = [s for s in re.split(r"[.!?]+", sentence_text) if s.strip()]
    if len(sentences) > 2 or not any(c.isalpha() for c in text):
        raise ValueError("Resposta inválida.")
    return text


class DialogueService:
    def __init__(self, client: NarrativeClient, prompt_builder: PromptBuilder | None = None):
        self.client = client
        self.prompt_builder = prompt_builder or PromptBuilder()

    def respond(self, state: GameState, choice: Choice) -> DialogueResult:
        started = monotonic()
        logger.info("Início da geração narrativa.")
        try:
            prompt = self.prompt_builder.build(state, choice)
            text = validate_response(self.client.generate(prompt))
        except Exception:
            # Fronteira com o provedor: nenhum corpo de erro ou resposta em logs/UI.
            logger.warning("Falha na geração narrativa (%.2fs).", monotonic() - started)
            return DialogueResult(error=ERROR_MESSAGE)
        logger.info("Geração narrativa concluída (%.2fs).", monotonic() - started)
        return DialogueResult(text=text)
