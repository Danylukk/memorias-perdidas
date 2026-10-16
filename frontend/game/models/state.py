import json
from dataclasses import dataclass
from pathlib import Path

from game.models.npc import NPC
from game.models.player import Player

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class GameState:
    """Estado enviado a um encontro: Kael, o NPC da conversa e a situação da cena."""
    player: Player
    npc: NPC
    situacao: str
    # O que Kael já fez nesta jornada (ex.: como tratou Darian), para o NPC reagir ao estado acumulado.
    historia: tuple[str, ...] = ()


def _read(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def initial_player() -> Player:
    return Player(**_read("game_state.json")["kael"])


def load_npc(npc_id: str) -> NPC:
    """Estes JSONs são dados iniciais, não saves."""
    character = _read("characters.json")[npc_id]
    for key in ("personalidade", "informacoes_conhecidas", "informacoes_permitidas", "segredos"):
        character[key] = tuple(character[key])
    return NPC(**character)


def situation(npc_id: str) -> str:
    initial = _read("game_state.json")
    return initial["situacao"] if npc_id == "darian" else initial["situacoes"][npc_id]


def new_game(npc_id: str = "darian") -> GameState:
    return GameState(initial_player(), load_npc(npc_id), situation(npc_id))
