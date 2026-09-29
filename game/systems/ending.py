"""Desfecho da sessão, calculado somente a partir do estado Python."""
from dataclasses import dataclass

from game.models.state import GameState

# Em empate, vale a ordem desta tabela.
PROFILES = (
    ("empatia", "O Protetor",
     "Kael escolheu cuidar de quem sangrava ao seu lado. Quem quer que tenha sido, agora é alguém que não abandona os feridos."),
    ("lealdade", "O Companheiro",
     "Kael manteve a palavra em meio às ruínas. A lealdade que demonstrou pode ser a primeira coisa verdadeira que recuperou."),
    ("curiosidade", "O Buscador",
     "Kael fez perguntas antes de agir. As respostas ainda estão enterradas, mas ele já decidiu que vai desenterrá-las."),
    ("agressividade", "O Implacável",
     "Kael arrancou respostas pela força. O passado pode ter sido violento, e o presente começa a se parecer com ele."),
    ("egoismo", "O Sobrevivente",
     "Kael colocou a si mesmo em primeiro lugar. Sobreviveu às ruínas, mas deixou para trás quem talvez soubesse quem ele era."),
)


@dataclass(frozen=True)
class Ending:
    titulo: str
    descricao: str
    destino_darian: str


def compute_ending(state: GameState, final_intent: str | None) -> Ending:
    player = state.player
    attribute, titulo, descricao = max(PROFILES, key=lambda p: (getattr(player, p[0]), -PROFILES.index(p)))
    trust = state.npc.confianca_em_kael
    if final_intent == "egoismo":
        destino = "Darian ficou para trás, sozinho entre os mortos."
    elif final_intent in ("empatia", "lealdade") and trust >= 40:
        destino = "Darian foi levado para longe das ruínas, apoiado no ombro de Kael."
    elif trust >= 40:
        destino = "Darian passou a confiar em Kael e promete contar mais quando chegar a hora."
    elif trust <= 10:
        destino = "Darian não confia mais em Kael. O que sabe, vai guardar para si."
    else:
        destino = "Darian ainda hesita. A confiança entre os dois está por um fio."
    return Ending(titulo, descricao, destino)
