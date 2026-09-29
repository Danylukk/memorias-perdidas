import json
import logging
import re
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from game.models.state import GameState
from game.systems.choices import INTENTS, Choice, choice_from_intent
from game.systems.fragments import Fragment
from game.systems.prompt_builder import DialoguePrompt, PromptBuilder

logger = logging.getLogger(__name__)
ERROR_MESSAGE = "Não foi possível gerar a resposta de Darian. Verifique a conexão e a configuração da IA."
MAX_RESPONSE_LENGTH = 360
MAX_MEMORY_LENGTH = 420
MAX_OPTION_LENGTH = 80
OPTION_COUNT = 4


class NarrativeClient(Protocol):
    def generate(self, prompt: DialoguePrompt) -> str: ...


@dataclass(frozen=True)
class DialogueResult:
    text: str = ""
    error: str = ""
    # Próximas opções de Kael; vazio quando não houver.
    options: tuple[Choice, ...] = ()
    # "ia" quando gerado pelo LLM; "roteiro" quando vem do roteiro offline.
    source: str = "ia"

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


def validate_response(raw: str, max_sentences: int = 2, max_length: int = MAX_RESPONSE_LENGTH) -> str:
    if not isinstance(raw, str):
        raise ValueError("Resposta inválida.")
    text = " ".join(raw.split())
    # Aspas externas são formatação, não uma terceira frase após o ponto final.
    if len(text) >= 2 and (text[0], text[-1]) in (("“", "”"), ('"', '"'), ("«", "»")):
        text = text[1:-1].strip()
    if not text or len(text) > max_length:
        raise ValueError("Resposta vazia ou longa demais.")
    if any(mark in text for mark in ("{", "}", "[", "]", "`", "<", ">", "**")):
        raise ValueError("Formato inválido.")
    if re.search(r"\b(IA|ChatGPT|OpenAI|LLM|prompt|modelo|instruções)\b", text, re.IGNORECASE):
        raise ValueError("Metalinguagem inválida.")
    if re.search(r"\b(vida|energia|empatia|agressividade|curiosidade|egoísmo|egoismo|lealdade|confiança|fragmentos)\s*[:=+\-]", text, re.IGNORECASE):
        raise ValueError("Comando de estado inválido.")
    sentence_text = re.sub(r"\.{2,}", "…", text)
    sentences = [s for s in re.split(r"[.!?]+", sentence_text) if s.strip()]
    if len(sentences) > max_sentences or not any(c.isalpha() for c in text):
        raise ValueError("Resposta inválida.")
    return text


def parse_turn(raw: str, first_option_id: int) -> DialogueResult:
    """Valida o JSON do turno: fala de Darian + exatamente 4 opções com intenção conhecida."""
    data = json.loads(raw)
    text = validate_response(data["fala"])
    options = data["opcoes"]
    if not isinstance(options, list) or len(options) != OPTION_COUNT:
        raise ValueError("Quantidade de opções inválida.")
    choices = []
    for index, option in enumerate(options):
        if option.get("intencao") not in INTENTS:
            raise ValueError("Intenção inválida.")
        label = validate_response(option["texto"], 1, MAX_OPTION_LENGTH).strip("\"“”")
        choices.append(choice_from_intent(first_option_id + index, label, option["intencao"]))
    if len({c.label.casefold() for c in choices}) != OPTION_COUNT:
        raise ValueError("Opções repetidas.")
    return DialogueResult(text=text, options=tuple(choices))


class DialogueService:
    def __init__(self, client: NarrativeClient, prompt_builder: PromptBuilder | None = None):
        self.client = client
        self.prompt_builder = prompt_builder or PromptBuilder()

    def respond(self, state: GameState, choice: Choice, history: tuple[dict, ...] = ()) -> DialogueResult:
        return self._generate(lambda: self.prompt_builder.build(state, choice, history), validate_response)

    def converse(self, state: GameState, choice: Choice, history: tuple[dict, ...] = (),
                 first_option_id: int = 1000) -> DialogueResult:
        """Fala de Darian e as próximas opções de Kael, geradas na mesma chamada."""
        started = monotonic()
        logger.info("Início da geração do turno.")
        try:
            prompt = self.prompt_builder.build_turn(state, choice, history)
            result = parse_turn(self.client.generate(prompt), first_option_id)
        except Exception:
            logger.warning("Falha na geração do turno (%.2fs).", monotonic() - started)
            return DialogueResult(error=ERROR_MESSAGE)
        logger.info("Geração do turno concluída (%.2fs).", monotonic() - started)
        return result

    def remember(self, state: GameState, fragment: Fragment) -> DialogueResult:
        return self._generate(lambda: self.prompt_builder.build_fragment(state, fragment),
                              lambda raw: validate_response(raw, 4, MAX_MEMORY_LENGTH))

    def _generate(self, build_prompt, validate) -> DialogueResult:
        started = monotonic()
        logger.info("Início da geração narrativa.")
        try:
            text = validate(self.client.generate(build_prompt()))
        except Exception:
            # Fronteira com o provedor: nenhum corpo de erro ou resposta em logs/UI.
            logger.warning("Falha na geração narrativa (%.2fs).", monotonic() - started)
            return DialogueResult(error=ERROR_MESSAGE)
        logger.info("Geração narrativa concluída (%.2fs).", monotonic() - started)
        return DialogueResult(text=text)
