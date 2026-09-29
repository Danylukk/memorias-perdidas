"""Fragmentos de Memória: o Python decide o desbloqueio; a IA apenas escreve a lembrança."""
from dataclasses import dataclass
from typing import Callable

from game.models.state import GameState

TOTAL_FRAGMENTS = 12


@dataclass(frozen=True)
class Fragment:
    id: str
    titulo: str
    tema: str
    dica: str
    fallback: str
    condition: Callable[[GameState], bool]


FRAGMENTS = (
    Fragment(
        "a_batalha", "A Batalha",
        "a batalha que destruiu parte da cidade; mencione fogo, metal e perda; não revele quem causou a batalha",
        "Mostre curiosidade sobre o passado (Curiosidade 3 ou mais).",
        # Texto gerado com ChatGPT na CP4 (seção 2.2.2), reaproveitado como reserva.
        "O céu estava em chamas. Lembro-me do som do metal, dos gritos e do gosto amargo da perda. "
        "Naquele dia, algo em mim também morreu.",
        lambda state: state.player.curiosidade >= 3,
    ),
    Fragment(
        "o_medalhao", "O Medalhão",
        "o medalhão antigo que Kael carrega no pescoço; uma sensação de juramento feito diante de alguém; "
        "não revele a origem nem o dono do medalhão",
        "Seja leal a Darian (Lealdade 3 ou mais).",
        "Mãos frias fecharam o medalhão na minha palma. Havia uma promessa naquele gesto. "
        "Não lembro o rosto, só o peso do metal e da palavra dada.",
        lambda state: state.player.lealdade >= 3,
    ),
    Fragment(
        "darian", "Darian",
        "uma lembrança vaga de ter dividido uma fogueira com um soldado de confiança antes de uma marcha; "
        "sem nomes de facções, cidades ou inimigos",
        "Conquiste a confiança de Darian (40 ou mais).",
        "Uma fogueira baixa, pão dividido em silêncio. Um soldado riu de algo que eu disse. "
        "Naquela noite, eu ainda confiava em alguém.",
        lambda state: state.npc.confianca_em_kael >= 40,
    ),
    Fragment(
        "maos_manchadas", "Mãos Manchadas",
        "a lembrança da violência que Kael já cometeu; culpa e frieza; sem revelar vítimas, motivos ou lados da guerra",
        "Aja com agressividade (Agressividade 2 ou mais).",
        "Lembro do peso da lâmina e do silêncio depois do golpe. Não lembro o motivo. "
        "Talvez eu nunca tenha precisado de um.",
        lambda state: state.player.agressividade >= 2,
    ),
)


def get_fragment(fragment_id: str) -> Fragment:
    for fragment in FRAGMENTS:
        if fragment.id == fragment_id:
            return fragment
    raise ValueError("Fragmento desconhecido.")


def newly_unlocked(state: GameState, already: set[str]) -> tuple[Fragment, ...]:
    return tuple(f for f in FRAGMENTS if f.id not in already and f.condition(state))


@dataclass(frozen=True)
class Memory:
    fragment: Fragment
    text: str
    generated: bool
