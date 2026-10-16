from dataclasses import dataclass


@dataclass(frozen=True)
class NPC:
    nome: str
    papel: str
    personalidade: tuple[str, ...]
    estado: str
    confianca_em_kael: int
    conhece_kael: bool
    pode_revelar_passado: bool
    informacoes_conhecidas: tuple[str, ...]
    informacoes_permitidas: tuple[str, ...]
    segredos: tuple[str, ...]
