"""Roteiro offline ramificado: segue o caminho das escolhas quando a IA não está disponível."""
import json
from functools import lru_cache
from pathlib import Path

from game.systems.choices import Choice, choice_from_intent, get_choice
from game.systems.dialogue import DialogueResult

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "data" / "roteiro_offline.json"

BRANCH_OF_INTENT = {
    "empatia": "cuidado", "lealdade": "cuidado", "curiosidade": "perguntas",
    "agressividade": "confronto", "egoismo": "abandono",
}
BRANCH_NAMES = {"cuidado": "Cuidado", "perguntas": "Perguntas", "confronto": "Confronto", "abandono": "Abandono"}


@lru_cache(maxsize=1)
def load_script() -> dict:
    return json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))["turnos"]


def branch_of(choice: Choice) -> str:
    return BRANCH_OF_INTENT[choice.intent]


def scripted_turn(turn: int, choice: Choice) -> DialogueResult:
    """Resposta de Darian à escolha do turno `turn` (1-based) e as opções do turno seguinte."""
    nodes = load_script()[str(turn)]
    node = nodes.get(branch_of(choice)) or nodes["perguntas"]
    options = tuple(
        get_choice(option["ref"]) if "ref" in option
        else choice_from_intent(300 + turn * 10 + index, option["texto"], option["intencao"])
        for index, option in enumerate(node.get("opcoes", ()))
    )
    return DialogueResult(text=node.get("fala") or choice.fallback, options=options, source="roteiro")
