from dataclasses import dataclass, replace

from game.models.state import GameState


@dataclass(frozen=True)
class Choice:
    id: int
    label: str
    action: str
    player_effects: tuple[tuple[str, int], ...]
    trust_effect: int = 0


CHOICES = (
    Choice(1, "Quem é você?", "Kael perguntou a Darian quem ele é.", (("curiosidade", 1),)),
    Choice(2, "Você me conhece?", "Kael perguntou se Darian o conhece.", (("curiosidade", 2),)),
    Choice(3, "Ajudar o soldado", "Kael decidiu ajudar Darian.",
           (("empatia", 2), ("lealdade", 1)), 10),
    Choice(4, "Ir embora", "Kael decidiu ir embora, deixando Darian.", (("egoismo", 2),), -10),
)


def get_choice(choice_id: int) -> Choice:
    for choice in CHOICES:
        if choice.id == choice_id:
            return choice
    raise ValueError("Escolha desconhecida.")


def apply_choice(state: GameState, choice_id: int) -> GameState:
    choice = get_choice(choice_id)
    updates = {name: getattr(state.player, name) + delta for name, delta in choice.player_effects}
    return replace(
        state,
        player=replace(state.player, **updates),
        npc=replace(state.npc, confianca_em_kael=state.npc.confianca_em_kael + choice.trust_effect),
    )
