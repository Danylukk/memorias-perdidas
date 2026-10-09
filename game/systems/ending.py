"""Desfecho (CP4 §1.7): decidir em quem confiar e definir quem Kael deseja se tornar."""
from dataclasses import dataclass

from game.models.player import Player

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

# Decisão final: em quem Kael vai confiar.
DECISIONS = (
    ("darian", "Confiar em Darian"),
    ("lira", "Confiar em Lira"),
    ("ambos", "Confiar nos dois"),
    ("sozinho", "Seguir sozinho"),
)
TRUST_NEEDED = {"darian": 30, "lira": 40}


@dataclass(frozen=True)
class Ending:
    titulo: str
    descricao: str
    destino: str


def profile(player: Player) -> tuple[str, str]:
    _, titulo, descricao = max(PROFILES, key=lambda p: (getattr(player, p[0]), -PROFILES.index(p)))
    return titulo, descricao


def compute_ending(player: Player, trust: dict[str, int], decision: str) -> Ending:
    titulo, descricao = profile(player)
    darian_ok = trust["darian"] >= TRUST_NEEDED["darian"]
    lira_ok = trust["lira"] >= TRUST_NEEDED["lira"]
    if decision == "darian":
        destino = ("Kael segue ao lado de Darian. O soldado promete contar, aos poucos, quem Kael foi na guerra."
                   if darian_ok else
                   "Kael estende a mão a Darian, mas o soldado desvia o olhar. A confiança perdida nas ruínas não volta tão cedo.")
    elif decision == "lira":
        destino = ("Kael parte com Lira. A curandeira ainda guarda segredos, mas agora caminha ao lado dele."
                   if lira_ok else
                   "Lira aceita a companhia de Kael com cautela. Ainda não confia nele o bastante para contar o que sabe.")
    elif decision == "ambos":
        destino = ("Kael reúne Darian e Lira. Pela primeira vez desde que despertou, ele não está sozinho."
                   if darian_ok and lira_ok else
                   "Kael tenta unir os dois, mas a desconfiança que semeou pesa mais que as ruínas.")
    else:
        destino = ("Kael deixa as ruínas sozinho, levando apenas o medalhão e as perguntas. "
                   "O que Darian e Lira sabiam fica para trás.")
    return Ending(titulo, descricao, destino)
