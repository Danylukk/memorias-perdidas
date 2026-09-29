from dataclasses import asdict, dataclass, replace
from queue import Empty, Queue
from threading import Thread

from game.models.npc import NPC
from game.models.player import Player
from game.models.state import GameState, new_game
from game.systems.choices import Choice, apply_effects, choice_from_dict, choice_to_dict
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE
from game.systems.fragments import Fragment, Memory, newly_unlocked
from game.systems.script import branch_of, opening, scripted_turn, total_turns


@dataclass
class Turn:
    choice: Choice
    result: DialogueResult | None = None


class Encounter:
    """Conversa com um NPC em turnos. Estado e consumo da fila pertencem ao loop principal."""

    def __init__(self, service: DialogueService, offline: bool = False, state: GameState | None = None,
                 npc_id: str = "darian", memories: dict | None = None):
        self.service = service
        # Offline: sem chave/modelo configurados, o roteiro ramificado conduz a conversa sem chamar a API.
        self.offline = offline
        self.npc_id = npc_id
        self.state = state or new_game(npc_id)
        self.total_turns = total_turns(npc_id)
        self.opening_line, self.opening_choices = opening(npc_id)
        self.turns: list[Turn] = []
        # Compartilhado com a jornada: fragmentos já recuperados não são desbloqueados de novo.
        self.memories: dict[str, Memory] = memories if memories is not None else {}
        self.new_memories: tuple[Memory, ...] = ()
        self.generation_in_progress = False
        self._results: Queue[tuple[DialogueResult, tuple[Memory, ...]]] = Queue(maxsize=1)

    @property
    def choice(self) -> Choice | None:
        return self.turns[-1].choice if self.turns else None

    @property
    def result(self) -> DialogueResult | None:
        return self.turns[-1].result if self.turns else None

    @property
    def round_index(self) -> int:
        return len(self.turns)

    @property
    def finished(self) -> bool:
        return len(self.turns) == self.total_turns and not self.generation_in_progress

    @property
    def options_generated(self) -> bool:
        return bool(self.result and self.result.source == "ia" and self.result.options)

    @property
    def branch(self) -> str | None:
        return branch_of(self.choice) if self.choice else None

    @property
    def current_choices(self) -> tuple[Choice, ...]:
        if self.generation_in_progress or self.finished:
            return ()
        # 1º turno: opções de abertura. Depois: opções da IA ou do roteiro, conforme a fala anterior.
        return self.result.options if self.turns else self.opening_choices

    def history(self) -> tuple[dict, ...]:
        return tuple({"acao": t.choice.action, f"fala_de_{self.npc_id}": t.result.text or None}
                     for t in self.turns if t.result is not None)

    def choose(self, choice_id: int) -> bool:
        choice = next((c for c in self.current_choices if c.id == choice_id), None)
        if choice is None:
            return False
        history = self.history()
        self.new_memories = ()
        self.state = apply_effects(self.state, choice)
        self.turns.append(Turn(choice))
        # O desbloqueio é decidido aqui, pelo Python, antes de qualquer chamada à IA.
        unlocked = newly_unlocked(self.state, set(self.memories))
        if unlocked:
            total = len(self.memories) + len(unlocked)
            self.state = replace(self.state, player=replace(self.state.player, fragmentos=total))
        self._start(history, unlocked)
        return True

    def retry(self) -> bool:
        if self.offline or self.generation_in_progress or self.result is None or self.result.ok:
            return False
        # Reenvia a mesma ação já aplicada, somente após clique explícito.
        self._start(self.history()[:-1], ())
        return True

    def _start(self, history: tuple[dict, ...], fragments: tuple[Fragment, ...]) -> None:
        self.generation_in_progress = True
        self.turns[-1].result = None
        state, choice, service, offline = self.state, self.choice, self.service, self.offline
        turn, total, npc_id = len(self.turns), self.total_turns, self.npc_id
        last_turn = turn == total
        scripted = scripted_turn(turn, choice, npc_id)

        def work():
            if offline:
                result = scripted
            else:
                try:
                    # No último turno não há próximas opções: apenas a fala final.
                    result = (service.respond(state, choice, history) if last_turn
                              else service.converse(state, choice, history, 1000 + turn * 10, total))
                    if not isinstance(result, DialogueResult) or not result.ok:
                        raise ValueError("Falha na geração.")
                    if not last_turn and not result.options:
                        result = replace(result, options=scripted.options)
                except Exception:
                    # A história continua pelo roteiro; o erro fica registrado para permitir nova tentativa.
                    result = replace(scripted, error=ERROR_MESSAGE)
            self._results.put((result, recall(service, state, fragments, offline)))

        try:
            # Fechar a janela não precisa aguardar a rede; worker não acessa Pygame.
            Thread(target=work, daemon=True, name=f"{npc_id}-dialogue").start()
        except RuntimeError:
            self.generation_in_progress = False
            self.turns[-1].result = replace(scripted, error=ERROR_MESSAGE)
            self._store_memories(tuple(Memory(f, f.fallback, False) for f in fragments))

    def _store_memories(self, memories: tuple[Memory, ...]) -> None:
        for memory in memories:
            self.memories[memory.fragment.id] = memory
        if memories:
            self.new_memories = memories

    def update(self) -> bool:
        """Consome o resultado do worker; retorna True quando um turno foi concluído."""
        if not self.generation_in_progress:
            return False
        try:
            result, memories = self._results.get_nowait()
        except Empty:
            return False
        self.turns[-1].result = result
        self._store_memories(memories)
        self.generation_in_progress = False
        return True

    # --- Save/Continuar (JSON, CP4 §4) ---
    def to_dict(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "player": asdict(self.state.player),
            "npc": asdict(self.state.npc),
            "situacao": self.state.situacao,
            "turns": [{"choice": choice_to_dict(t.choice), "result": result_to_dict(t.result)} for t in self.turns],
        }

    @classmethod
    def from_dict(cls, service, offline: bool, data: dict, memories: dict) -> "Encounter":
        npc = NPC(**{k: tuple(v) if isinstance(v, list) else v for k, v in data["npc"].items()})
        state = GameState(Player(**data["player"]), npc, data["situacao"])
        encounter = cls(service, offline, state, data["npc_id"], memories)
        encounter.turns = [Turn(choice_from_dict(t["choice"]), result_from_dict(t["result"])) for t in data["turns"]]
        return encounter


def recall(service, state: GameState, fragments: tuple[Fragment, ...], offline: bool) -> tuple[Memory, ...]:
    """Pede à IA o texto de cada lembrança; sem IA ou em falha, usa o texto do roteiro."""
    memories = []
    for fragment in fragments:
        try:
            memory = None if offline else service.remember(state, fragment)
        except Exception:
            memory = None
        if isinstance(memory, DialogueResult) and memory.ok:
            memories.append(Memory(fragment, memory.text, True))
        else:
            memories.append(Memory(fragment, fragment.fallback, False))
    return tuple(memories)


def result_to_dict(result: DialogueResult | None) -> dict | None:
    if result is None:
        return None
    return {"text": result.text, "error": result.error, "source": result.source,
            "options": [choice_to_dict(c) for c in result.options]}


def result_from_dict(data: dict | None) -> DialogueResult | None:
    if data is None:
        return None
    return DialogueResult(data["text"], data["error"], tuple(choice_from_dict(c) for c in data["options"]),
                          data["source"])
