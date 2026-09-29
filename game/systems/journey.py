"""Jornada de uma partida (CP4 §1.3 e §1.7).

Kael desperta e encontra Darian → explora as ruínas (objetos e locais despertam fragmentos) →
encontra Lira → decide em quem confiar. O estado pertence ao Python; a IA só escreve falas e lembranças.
"""
from collections import Counter
from dataclasses import asdict, dataclass, replace
from queue import Empty, Queue
from threading import Thread

from game.models.npc import NPC
from game.models.player import Player
from game.models.state import GameState, initial_player, load_npc, situation
from game.systems import save
from game.systems.encounter import Encounter, recall
from game.systems.ending import DECISIONS, Ending, compute_ending
from game.systems.fragments import Memory, get_fragment
from game.systems.script import branch_of

PHASES = ("darian", "exploracao", "lira", "decisao", "fim")


@dataclass(frozen=True)
class Hotspot:
    id: str
    nome: str
    x: int | None  # None: ação sobre o próprio Kael (o medalhão que ele carrega)
    narracao: str
    fragmento: str | None = None
    efeitos: tuple[tuple[str, int], ...] = ()  # aplicados uma única vez


# Posições na largura da tela (1280), alinhadas ao cenário oficial das ruínas.
HOTSPOTS = (
    Hotspot("estandarte", "Estandarte rasgado", 125,
            "Um estandarte rasgado, com uma cruz dourada bordada. Kael reconhece o símbolo antes mesmo de entender por quê.",
            "ordem_de_arkan"),
    Hotspot("espadas", "Espadas cravadas", 395,
            "Espadas cravadas no chão e escudos queimados. O cheiro de fumaça desperta algo em Kael.",
            "a_batalha"),
    Hotspot("darian", "Darian", 780,
            "Darian descansa encostado nas pedras, respirando com dificuldade. Ele acompanha Kael com o olhar."),
    Hotspot("soldado", "Soldado caído", 945,
            "Um soldado caído, com a mesma cruz dourada no escudo. Kael fecha os olhos dele em silêncio.",
            efeitos=(("empatia", 1),)),
    Hotspot("medalhao", "Medalhão", None,
            "Kael examina o medalhão antigo em seu pescoço. O metal está frio, gasto de tanto ser apertado.",
            efeitos=(("curiosidade", 1),)),
    Hotspot("lira", "Lira", 1085, "Uma curandeira de capa verde se aproxima, cuidando dos feridos."),
)
# Como Kael tratou Darian (caminho predominante da conversa): contexto da Lira e efeito na confiança dela.
DARIAN_OUTCOMES = {
    "cuidado": ("Kael ajudou Darian: cuidou do ferimento dele e ficou ao seu lado.", 10),
    "perguntas": ("Kael interrogou Darian sobre o passado, sem se comprometer a ajudá-lo.", 0),
    "confronto": ("Kael ameaçou e pressionou Darian ferido em busca de respostas.", -5),
    "abandono": ("Kael tentou abandonar Darian gravemente ferido nas ruínas.", -10),
}


def darian_outcome(encounter: Encounter) -> str:
    """Caminho predominante das escolhas com Darian; em empate, vale o mais recente."""
    branches = [branch_of(turn.choice) for turn in encounter.turns]
    if not branches:
        return "perguntas"
    counts = Counter(branches)
    best = max(counts.values())
    return next(branch for branch in reversed(branches) if counts[branch] == best)


EXPLORATION_INTRO = "Explore as ruínas: investigue o que desperta lembranças e procure Lira, a curandeira."
INVESTIGATION_COST = 5  # energia


def get_hotspot(hotspot_id: str) -> Hotspot:
    return next(h for h in HOTSPOTS if h.id == hotspot_id)


@dataclass(frozen=True)
class Message:
    """Narração exibida na caixa de diálogo durante a exploração."""
    heading: str
    text: str
    source: str = "jogo"  # "jogo", "ia" ou "roteiro"


class Journey:
    def __init__(self, service, offline: bool = False):
        self.service = service
        self.offline = offline
        self.player: Player = initial_player()
        self.npcs: dict[str, NPC] = {"darian": load_npc("darian"), "lira": load_npc("lira")}
        self.memories: dict[str, Memory] = {}
        self.explored: set[str] = set()
        self.decision: str | None = None
        self.darian_outcome: str | None = None
        self.phase = "darian"
        self.message = Message("Ruínas", EXPLORATION_INTRO)
        self.new_memories: tuple[Memory, ...] = ()
        self.encounter: Encounter | None = self._encounter("darian")
        self.investigating = False
        self._jobs: Queue[tuple[str, tuple[Memory, ...]]] = Queue(maxsize=1)

    def _encounter(self, npc_id: str) -> Encounter:
        history = ()
        if npc_id == "lira" and self.darian_outcome:
            history = (DARIAN_OUTCOMES[self.darian_outcome][0],
                       f"Confiança de Darian em Kael ao fim da conversa: {self.npcs['darian'].confianca_em_kael}.")
        state = GameState(self.player, self.npcs[npc_id], situation(npc_id), history)
        variant = self.darian_outcome if npc_id == "lira" else None
        return Encounter(self.service, self.offline, state, npc_id, self.memories, variant)

    # --- Estado exibido ---
    @property
    def busy(self) -> bool:
        return self.investigating or bool(self.encounter and self.encounter.generation_in_progress)

    @property
    def current_player(self) -> Player:
        return self.encounter.state.player if self.encounter else self.player

    def trust(self, npc_id: str) -> int:
        if self.encounter and self.encounter.npc_id == npc_id:
            return self.encounter.state.npc.confianca_em_kael
        return self.npcs[npc_id].confianca_em_kael

    @property
    def conversation_over(self) -> bool:
        return bool(self.encounter and self.encounter.finished)

    # --- Transições ---
    def advance(self) -> bool:
        """Botão de continuar após uma conversa: Darian → exploração; Lira → decisão."""
        if not self.conversation_over:
            return False
        self._close_encounter()
        self.phase = "exploracao" if self.phase == "darian" else "decisao"
        self.message = (Message("Ruínas", EXPLORATION_INTRO) if self.phase == "exploracao"
                        else Message("Decisão", "Em quem Kael vai confiar?"))
        return True

    def _close_encounter(self) -> None:
        state = self.encounter.state
        self.player = state.player
        self.npcs[self.encounter.npc_id] = state.npc
        if self.encounter.npc_id == "darian":
            # Consequência que atravessa cenas: Lira sabe como Kael tratou Darian.
            self.darian_outcome = darian_outcome(self.encounter)
            lira = self.npcs["lira"]
            trust = max(0, min(100, lira.confianca_em_kael + DARIAN_OUTCOMES[self.darian_outcome][1]))
            self.npcs["lira"] = replace(lira, confianca_em_kael=trust)
        self.encounter = None

    def interact(self, hotspot_id: str) -> bool:
        if self.phase != "exploracao" or self.busy:
            return False
        hotspot = get_hotspot(hotspot_id)
        self.new_memories = ()
        if hotspot.id == "lira":
            self.phase = "lira"
            self.encounter = self._encounter("lira")
            return True
        self.message = Message(hotspot.nome, hotspot.narracao)
        if hotspot.efeitos and hotspot.id not in self.explored:
            # Cada ponto de interesse altera Kael uma única vez (CP4 §1.5: investigar ruínas).
            self.explored.add(hotspot.id)
            updates = {name: max(0, min(100, getattr(self.player, name) + delta)) for name, delta in hotspot.efeitos}
            self.player = replace(self.player, **updates)
        if hotspot.fragmento is None or hotspot.fragmento in self.memories:
            return True
        # Objetos e locais desbloqueiam lembranças (CP4 §1.5); a regra é do jogo, o texto é da IA.
        self.explored.add(hotspot.id)
        fragment = get_fragment(hotspot.fragmento)
        self.player = replace(self.player, energia=max(0, self.player.energia - INVESTIGATION_COST),
                              fragmentos=len(self.memories) + 1)
        self.investigating = True
        state = GameState(self.player, self.npcs["darian"], situation("darian"))
        service, offline = self.service, self.offline

        def work():
            self._jobs.put((hotspot.nome, recall(service, state, (fragment,), offline)))

        try:
            Thread(target=work, daemon=True, name="fragment-memory").start()
        except RuntimeError:
            self._jobs.put((hotspot.nome, (Memory(fragment, fragment.fallback, False),)))
        return True

    def decide(self, decision: str) -> bool:
        if self.phase != "decisao" or decision not in dict(DECISIONS):
            return False
        self.decision = decision
        self.phase = "fim"
        self.message = Message("Decisão", dict(DECISIONS)[decision] + ".")
        return True

    def ending(self) -> Ending:
        trust = {npc_id: npc.confianca_em_kael for npc_id, npc in self.npcs.items()}
        return compute_ending(self.player, trust, self.decision or "sozinho")

    def update(self) -> bool:
        """Consome resultados pendentes; retorna True quando algo mudou (para salvar)."""
        changed = False
        if self.encounter and self.encounter.update():
            self.new_memories = self.encounter.new_memories
            changed = True
        if self.investigating:
            try:
                _, memories = self._jobs.get_nowait()
            except Empty:
                return changed
            for memory in memories:
                self.memories[memory.fragment.id] = memory
                self.message = Message(f"Memória recuperada — {memory.fragment.titulo}", memory.text,
                                       "ia" if memory.generated else "roteiro")
            self.new_memories = memories
            self.investigating = False
            changed = True
        return changed

    # --- Save/Continuar ---
    def to_dict(self) -> dict:
        return {
            "versao": 1,
            "phase": self.phase,
            "player": asdict(self.player),
            "npcs": {npc_id: asdict(npc) for npc_id, npc in self.npcs.items()},
            "memories": [m.to_dict() for m in self.memories.values()],
            "explored": sorted(self.explored),
            "decision": self.decision,
            "darian_outcome": self.darian_outcome,
            "message": asdict(self.message),
            "encounter": self.encounter.to_dict() if self.encounter else None,
        }

    @classmethod
    def from_dict(cls, service, offline: bool, data: dict) -> "Journey":
        journey = cls(service, offline)
        journey.phase = data["phase"]
        journey.player = Player(**data["player"])
        journey.npcs = {npc_id: NPC(**{k: tuple(v) if isinstance(v, list) else v for k, v in npc.items()})
                        for npc_id, npc in data["npcs"].items()}
        journey.memories.clear()
        journey.memories.update({m["fragment"]: Memory.from_dict(m) for m in data["memories"]})
        journey.explored = set(data["explored"])
        journey.decision = data["decision"]
        journey.darian_outcome = data.get("darian_outcome")
        journey.message = Message(**data["message"])
        journey.encounter = (Encounter.from_dict(service, offline, data["encounter"], journey.memories)
                             if data["encounter"] else None)
        return journey

    def persist(self) -> None:
        """Salva o progresso (CONTINUAR) e acrescenta as memórias à galeria de Fragmentos."""
        if self.busy:
            return
        gallery = save.read(save.GALLERY, {})
        gallery = gallery if isinstance(gallery, dict) else {}
        gallery.update({m.fragment.id: m.to_dict() for m in self.memories.values()})
        save.write(save.GALLERY, gallery)
        if self.phase == "fim":
            save.delete(save.PROGRESS)
        else:
            save.write(save.PROGRESS, self.to_dict())


def load_gallery() -> dict[str, Memory]:
    data = save.read(save.GALLERY, {})
    memories = {}
    for value in (data.values() if isinstance(data, dict) else ()):
        try:
            memory = Memory.from_dict(value)
        except (KeyError, TypeError, ValueError):
            continue
        memories[memory.fragment.id] = memory
    return memories


def load_progress(service, offline: bool) -> Journey | None:
    data = save.read(save.PROGRESS)
    if not isinstance(data, dict):
        return None
    try:
        return Journey.from_dict(service, offline, data)
    except (KeyError, TypeError, ValueError):
        return None
