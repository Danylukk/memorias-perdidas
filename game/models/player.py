from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    nome: str = "Kael"
    vida: int = 100
    energia: int = 100
    empatia: int = 0
    agressividade: int = 0
    curiosidade: int = 0
    egoismo: int = 0
    lealdade: int = 0
    fragmentos: int = 0
