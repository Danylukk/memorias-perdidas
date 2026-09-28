from dataclasses import dataclass, replace

from game.models.state import GameState

STAT_LIMITS = (0, 100)


@dataclass(frozen=True)
class Choice:
    id: int
    label: str
    action: str
    player_effects: tuple[tuple[str, int], ...]
    trust_effect: int = 0
    # Fala roteirizada exibida somente quando a IA falha, sempre identificada como reserva.
    fallback: str = "..."


CHOICES = (
    Choice(1, "Quem é você?", "Kael perguntou a Darian quem ele é.", (("curiosidade", 1),),
           fallback="Meu nome é Darian... e você devia se lembrar disso."),
    Choice(2, "Você me conhece?", "Kael perguntou se Darian o conhece.", (("curiosidade", 2),),
           fallback="Conheço o seu rosto, Kael. É o resto que me preocupa."),
    Choice(3, "Ajudar o soldado", "Kael decidiu ajudar Darian.",
           (("empatia", 2), ("lealdade", 1)), 10,
           fallback="Cuidado com a perna... ainda não sei se posso confiar em você."),
    Choice(4, "Ir embora", "Kael deu as costas e começou a se afastar, deixando Darian.", (("egoismo", 2),), -10,
           fallback="Vai me deixar aqui para morrer, Kael? Então você não mudou nada."),
)

ROUND_2 = (
    Choice(5, "Perguntar sobre o passado", "Kael perguntou a Darian o que aconteceu antes da batalha.",
           (("curiosidade", 2),),
           fallback="Há coisas que você precisa lembrar sozinho. Eu não vou dizer ainda."),
    Choice(6, "Ameaçar Darian", "Kael ameaçou Darian para arrancar respostas à força.",
           (("agressividade", 2), ("empatia", -1), ("vida", -10)), -15,
           fallback="Ainda consigo segurar uma lâmina, Kael. Tente de novo e verá."),
    Choice(7, "Estancar o ferimento", "Kael rasgou a própria capa para estancar o ferimento de Darian.",
           (("empatia", 1), ("lealdade", 1), ("energia", -15)), 10,
           fallback="O sangue parou... obrigado. Não esperava isso de você."),
    Choice(8, "Examinar o medalhão", "Kael examinou o medalhão antigo em seu pescoço diante de Darian.",
           (("curiosidade", 1),),
           fallback="Esse medalhão... guarde-o bem. Ele ainda significa alguma coisa."),
)

ROUND_3 = (
    Choice(9, "Levar Darian ao abrigo", "Kael apoiou Darian no ombro e decidiu levá-lo para longe das ruínas.",
           (("lealdade", 2), ("empatia", 1), ("energia", -25)), 10,
           fallback="Se me carregar até lá, Kael, eu te devo a vida."),
    Choice(10, "Exigir a verdade", "Kael exigiu que Darian contasse toda a verdade sobre quem ele era.",
           (("agressividade", 1), ("curiosidade", 1)), -5,
           fallback="A verdade não cabe nestas ruínas. Não hoje."),
    Choice(11, "Prometer voltar com ajuda", "Kael prometeu a Darian que voltaria com ajuda.",
           (("lealdade", 1),), 5,
           fallback="Promessas eram fáceis para você, Kael. Espero que esta seja diferente."),
    Choice(12, "Partir sozinho", "Kael decidiu partir sozinho e deixar Darian para trás nas ruínas.",
           (("egoismo", 2),), -10,
           fallback="Vá, então. As ruínas vão guardar o que você deixou para trás."),
)

ROUNDS = (CHOICES, ROUND_2, ROUND_3)


def get_choice(choice_id: int) -> Choice:
    for round_choices in ROUNDS:
        for choice in round_choices:
            if choice.id == choice_id:
                return choice
    raise ValueError("Escolha desconhecida.")


def clamp(value: int) -> int:
    return max(STAT_LIMITS[0], min(STAT_LIMITS[1], value))


def apply_choice(state: GameState, choice_id: int) -> GameState:
    choice = get_choice(choice_id)
    updates = {name: clamp(getattr(state.player, name) + delta) for name, delta in choice.player_effects}
    return replace(
        state,
        player=replace(state.player, **updates),
        npc=replace(state.npc, confianca_em_kael=clamp(state.npc.confianca_em_kael + choice.trust_effect)),
    )
