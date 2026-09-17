import json
from dataclasses import dataclass
from pathlib import Path

from game.models.npc import NPC
from game.models.player import Player

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class GameState:
    player: Player
    npc: NPC
    situacao: str


def new_game() -> GameState:
    """Carrega um estado novo; estes JSONs são dados iniciais, não saves."""
    initial = json.loads((DATA_DIR / "game_state.json").read_text(encoding="utf-8"))
    character = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8"))["darian"]
    for key in ("personalidade", "informacoes_conhecidas", "informacoes_permitidas", "segredos"):
        character[key] = tuple(character[key])
    return GameState(Player(**initial["kael"]), NPC(**character), initial["situacao"])
