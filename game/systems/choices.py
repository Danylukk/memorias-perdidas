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
    # Fala roteirizada exibida somente quando a IA falha, sempre identificada como reserva.
    fallback: str = "..."
    intent: str = "curiosidade"


# A IA só escolhe a intenção de cada opção; os números pertencem ao Python.
INTENTS = {
    "curiosidade": ((("curiosidade", 1),), 0,
                    "Algumas respostas você vai ter que encontrar sozinho, Kael."),
    "empatia": ((("empatia", 1), ("energia", -5)), 5,
                "Não esperava isso de você... obrigado."),
    "lealdade": ((("lealdade", 1),), 5,
                 "Se está falando sério, então ainda há algo do velho Kael em você."),
    "agressividade": ((("agressividade", 1), ("vida", -5)), -10,
                      "Cuidado com o tom, Kael. Ferido ou não, ainda sei me defender."),
    "egoismo": ((("egoismo", 1),), -5,
                "Sempre pensando primeiro em si mesmo. Isso você não esqueceu."),
}


def choice_from_intent(choice_id: int, text: str, intent: str) -> Choice:
    effects, trust, fallback = INTENTS[intent]
    return Choice(choice_id, text, f"Kael respondeu: \"{text}\"", effects, trust, fallback, intent)


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

# Reserva do turno 2 quando a IA não gera opções; inclui as ações da tabela da CP4 (§1.6).
ROUND_2 = (
    Choice(5, "Perguntar sobre o passado", "Kael perguntou a Darian o que aconteceu antes da batalha.",
           (("curiosidade", 2),),
           fallback="Há coisas que você precisa lembrar sozinho. Eu não vou dizer ainda.", intent="curiosidade"),
    Choice(6, "Ameaçar Darian", "Kael ameaçou Darian para arrancar respostas à força.",
           (("agressividade", 2), ("empatia", -1), ("vida", -10)), -15,
           fallback="Ainda consigo segurar uma lâmina, Kael. Tente de novo e verá.", intent="agressividade"),
    Choice(7, "Estancar o ferimento", "Kael rasgou a própria capa para estancar o ferimento de Darian.",
           (("empatia", 1), ("lealdade", 1), ("energia", -15)), 10,
           fallback="O sangue parou... obrigado. Não esperava isso de você.", intent="empatia"),
    Choice(8, "Prometer não abandoná-lo", "Kael prometeu que não abandonaria Darian nas ruínas.",
           (("lealdade", 2),), 5,
           fallback="Promessas eram fáceis para você, Kael. Espero que esta seja diferente.", intent="lealdade"),
)

# Reserva genérica dos turnos seguintes: cabe em qualquer ponto da conversa.
GENERIC_FALLBACK = (
    ("O que mais você sabe sobre mim?", "curiosidade"),
    ("Fique quieto. Deixe-me cuidar disso.", "empatia"),
    ("Não vou deixar você para trás.", "lealdade"),
    ("Chega de rodeios. Fale de uma vez.", "agressividade"),
    ("Isso não é problema meu.", "egoismo"),
)


def fallback_options(turn: int) -> tuple[Choice, ...]:
    """Opções fixas do turno (1-based) quando não há opções geradas."""
    if turn == 1:
        return CHOICES
    if turn == 2:
        return ROUND_2
    start = turn % len(GENERIC_FALLBACK)
    picked = [GENERIC_FALLBACK[(start + i) % len(GENERIC_FALLBACK)] for i in range(4)]
    return tuple(choice_from_intent(200 + turn * 10 + i, text, intent) for i, (text, intent) in enumerate(picked))


def get_choice(choice_id: int) -> Choice:
    for choice in CHOICES + ROUND_2:
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
