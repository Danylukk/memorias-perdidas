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
    data = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def total_turns(npc_id: str) -> int:
    return len(load_script()[npc_id]["turnos"])


def branch_of(choice: Choice) -> str:
    return BRANCH_OF_INTENT[choice.intent]


def _options(npc_id: str, turn: int, raw_options) -> tuple[Choice, ...]:
    base = 300 + turn * 10 + (0 if npc_id == "darian" else 500)
    return tuple(
        get_choice(option["ref"]) if "ref" in option
        else choice_from_intent(base + index, option["texto"], option["intencao"])
        for index, option in enumerate(raw_options)
    )


def opening(npc_id: str) -> tuple[str, tuple[Choice, ...]]:
    """Fala inicial do personagem e as opções do 1º turno."""
    node = load_script()[npc_id]["abertura"]
    return node["fala"], _options(npc_id, 0, node["opcoes"])


def scripted_turn(turn: int, choice: Choice, npc_id: str = "darian") -> DialogueResult:
    """Resposta à escolha do turno `turn` (1-based) e as opções do turno seguinte."""
    nodes = load_script()[npc_id]["turnos"][str(turn)]
    node = nodes.get(branch_of(choice)) or nodes["perguntas"]
    return DialogueResult(text=node.get("fala") or choice.fallback,
                          options=_options(npc_id, turn, node.get("opcoes", ())), source="roteiro")
