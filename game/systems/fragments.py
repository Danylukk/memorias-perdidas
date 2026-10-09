"""Fragmentos de Memória (CP4 §1.5 e Figura 6): personagens, locais e objetos desbloqueiam lembranças.

O Python decide o desbloqueio; a IA apenas escreve a lembrança (CP4 §2.2.2).
"""
from dataclasses import dataclass
from typing import Callable

from game.models.state import GameState

TOTAL_FRAGMENTS = 12


@dataclass(frozen=True)
class Fragment:
    id: str
    titulo: str
    origem: str  # "local", "objeto" ou "personagem"
    tema: str
    descricao: str
    dica: str
    fallback: str
    # Personagens: condição avaliada durante a conversa. Locais/objetos: desbloqueio ao investigar.
    condition: Callable[[GameState], bool] | None = None


def _trust(npc_name: str, minimum: int) -> Callable[[GameState], bool]:
    return lambda state: state.npc.nome == npc_name and state.npc.confianca_em_kael >= minimum


# Mesma ordem e nomes do mockup da tela Fragmentos de Memória.
FRAGMENTS = (
    Fragment(
        "a_batalha", "A Batalha", "local",
        "a batalha que destruiu parte da cidade; mencione fogo, metal e perda; não revele quem causou a batalha",
        # Texto secundário do mockup (Figura 6).
        "A batalha que mudou tudo. O início do fim, e o peso de um passado que ainda me persegue.",
        "Examine as espadas cravadas no campo de batalha.",
        # Resultado do teste real com ChatGPT na CP4 (§2.2.2).
        "O céu estava em chamas. Lembro-me do som do metal, dos gritos e do gosto amargo da perda. "
        "Naquele dia, algo em mim também morreu.",
    ),
    Fragment(
        "ordem_de_arkan", "A Ordem de Arkan", "objeto",
        "figuras encapuzadas da Ordem de Arkan reunidas sob uma cruz dourada numa catedral à luz de velas, "
        "e Kael ajoelhado entre elas; não revele o papel de Kael, os objetivos da ordem nem outros nomes",
        "Uma cruz dourada, um juramento e um nome que ainda ecoa em mim: Arkan.",
        "Investigue o estandarte rasgado.",
        "Velas numa catedral fria. Figuras encapuzadas diante de uma cruz dourada, e eu ajoelhado entre elas. "
        "Juramos algo naquela noite. Ainda não lembro o quê.",
    ),
    Fragment(
        "lira", "Lira", "personagem",
        "uma lembrança de Lira segurando um lírio branco enquanto cuida de Kael ferido em outro tempo; "
        "não revele a relação exata entre os dois",
        "Mãos que curam e uma voz que eu já conhecia antes de acordar nas ruínas.",
        "Conquiste a confiança de Lira (45 ou mais).",
        "Um lírio branco em mãos cuidadosas. Alguém limpava meus ferimentos e cantarolava baixinho. "
        "Eu conhecia aquela voz.",
        _trust("Lira", 45),
    ),
    Fragment(
        "darian", "Darian", "personagem",
        "uma lembrança vaga de ter dividido uma fogueira com um soldado de confiança antes de uma marcha; "
        "sem nomes de facções, cidades ou inimigos",
        "Um companheiro de armas. Ou alguém que eu deixei para trás?",
        "Conquiste a confiança de Darian (40 ou mais).",
        "Uma fogueira baixa, pão dividido em silêncio. Um soldado riu de algo que eu disse. "
        "Naquela noite, eu ainda confiava em alguém.",
        _trust("Darian", 40),
    ),
)


def get_fragment(fragment_id: str) -> Fragment:
    for fragment in FRAGMENTS:
        if fragment.id == fragment_id:
            return fragment
    raise ValueError("Fragmento desconhecido.")


def newly_unlocked(state: GameState, already) -> tuple[Fragment, ...]:
    return tuple(f for f in FRAGMENTS
                 if f.condition is not None and f.id not in already and f.condition(state))


@dataclass(frozen=True)
class Memory:
    fragment: Fragment
    text: str
    generated: bool

    def to_dict(self) -> dict:
        return {"fragment": self.fragment.id, "text": self.text, "generated": self.generated}

    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        return cls(get_fragment(data["fragment"]), data["text"], bool(data["generated"]))
