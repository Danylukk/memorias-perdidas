from dataclasses import dataclass, replace

from game.models.state import GameState

STAT_LIMITS = (0, 100)
TOTAL_TURNS = 5


@dataclass(frozen=True)
class Choice:
    id: int
    label: str
    action: str
    player_effects: tuple[tuple[str, int], ...]
    trust_effect: int = 0
    # Fala própria de Darian no roteiro offline (opções fixas do turno 1).
    fallback: str = "..."
    intent: str = "curiosidade"


# A IA (ou o roteiro offline) só escolhe a intenção de cada opção; os números pertencem ao Python.
INTENTS = {
    "curiosidade": ((("curiosidade", 1),), 0),
    "empatia": ((("empatia", 1), ("energia", -5)), 5),
    "lealdade": ((("lealdade", 1),), 5),
    "agressividade": ((("agressividade", 1), ("vida", -5)), -10),
    "egoismo": ((("egoismo", 1),), -5),
}


def choice_from_intent(choice_id: int, text: str, intent: str) -> Choice:
    effects, trust = INTENTS[intent]
    return Choice(choice_id, text, f"Kael respondeu: \"{text}\"", effects, trust, intent=intent)


# Turno 1: as quatro opções do mockup da CP4.
CHOICES = (
    Choice(1, "Quem é você?", "Kael perguntou a Darian quem ele é.", (("curiosidade", 1),),
           fallback="Meu nome é Darian... e você devia se lembrar disso.", intent="curiosidade"),
    Choice(2, "Você me conhece?", "Kael perguntou se Darian o conhece.", (("curiosidade", 2),),
           fallback="Conheço o seu rosto, Kael. É o resto que me preocupa.", intent="curiosidade"),
    Choice(3, "Ajudar o soldado", "Kael decidiu ajudar Darian.",
           (("empatia", 2), ("lealdade", 1)), 10,
           fallback="Cuidado com a perna... ainda não sei se posso confiar em você.", intent="empatia"),
    Choice(4, "Ir embora", "Kael deu as costas e começou a se afastar, deixando Darian.", (("egoismo", 2),), -10,
           fallback="Vai me deixar aqui para morrer, Kael? Então você não mudou nada.", intent="egoismo"),
)

# Ações da tabela da CP4 (§1.6), oferecidas pelo roteiro offline com os efeitos originais.
CP4_ACTIONS = (
    Choice(5, "Perguntar sobre o passado", "Kael perguntou a Darian o que aconteceu antes da batalha.",
           (("curiosidade", 2),), intent="curiosidade"),
    Choice(6, "Ameaçar Darian", "Kael ameaçou Darian para arrancar respostas à força.",
           (("agressividade", 2), ("empatia", -1), ("vida", -10)), -15, intent="agressividade"),
)


def get_choice(choice_id: int) -> Choice:
    for choice in CHOICES + CP4_ACTIONS:
        if choice.id == choice_id:
            return choice
    raise ValueError("Escolha desconhecida.")


def clamp(value: int) -> int:
    return max(STAT_LIMITS[0], min(STAT_LIMITS[1], value))


def apply_effects(state: GameState, choice: Choice) -> GameState:
    updates = {name: clamp(getattr(state.player, name) + delta) for name, delta in choice.player_effects}
    return replace(
        state,
        player=replace(state.player, **updates),
        npc=replace(state.npc, confianca_em_kael=clamp(state.npc.confianca_em_kael + choice.trust_effect)),
    )


def apply_choice(state: GameState, choice_id: int) -> GameState:
    return apply_effects(state, get_choice(choice_id))
