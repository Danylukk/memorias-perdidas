from dataclasses import dataclass, replace
from queue import Empty, Queue
from threading import Thread

from game.models.state import new_game
from game.systems.choices import TOTAL_TURNS, Choice, apply_effects, fallback_options
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE
from game.systems.fragments import Fragment, Memory, newly_unlocked


@dataclass
class Turn:
    choice: Choice
    result: DialogueResult | None = None


class Encounter:
    """Conversa com Darian em turnos. Estado e consumo da fila pertencem ao loop principal."""

    def __init__(self, service: DialogueService):
        self.service = service
        self.state = new_game()
        self.turns: list[Turn] = []
        self.memories: dict[str, Memory] = {}
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
        return len(self.turns) == TOTAL_TURNS and not self.generation_in_progress

    @property
    def options_generated(self) -> bool:
        return bool(self.result and self.result.options)

    @property
    def current_choices(self) -> tuple[Choice, ...]:
        if self.generation_in_progress or self.finished:
            return ()
        # Opções geradas pela IA na fala anterior; sem elas, as opções fixas de reserva.
        return self.result.options if self.options_generated else fallback_options(self.round_index + 1)

    def history(self) -> tuple[dict, ...]:
        # Somente falas realmente geradas entram no contexto; reservas não viram "memória" da IA.
        return tuple({"acao": t.choice.action, "fala_de_darian": t.result.text if t.result and t.result.ok else None}
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
        if self.generation_in_progress or self.result is None or self.result.ok:
            return False
        # Reenvia a mesma ação já aplicada, somente após clique explícito.
        self._start(self.history()[:-1], ())
        return True

    def _start(self, history: tuple[dict, ...], fragments: tuple[Fragment, ...]) -> None:
        self.generation_in_progress = True
        self.turns[-1].result = None
        state, choice, service = self.state, self.choice, self.service
        last_turn = len(self.turns) == TOTAL_TURNS
        first_option_id = 1000 + len(self.turns) * 10

        def work():
            try:
                # No último turno não há próximas opções: apenas a fala final de Darian.
                result = (service.respond(state, choice, history) if last_turn
                          else service.converse(state, choice, history, first_option_id))
                if not isinstance(result, DialogueResult):
                    raise TypeError("Resultado inválido.")
            except Exception:
                result = DialogueResult(error=ERROR_MESSAGE)
            memories = []
            for fragment in fragments:
                try:
                    memory = service.remember(state, fragment)
                except Exception:
                    memory = None
                if isinstance(memory, DialogueResult) and memory.ok:
                    memories.append(Memory(fragment, memory.text, True))
                else:
                    memories.append(Memory(fragment, fragment.fallback, False))
            self._results.put((result, tuple(memories)))

        try:
            # Fechar a janela não precisa aguardar a rede; worker não acessa Pygame.
            Thread(target=work, daemon=True, name="darian-dialogue").start()
        except RuntimeError:
            self.generation_in_progress = False
            self.turns[-1].result = DialogueResult(error=ERROR_MESSAGE)
            self._store_memories(tuple(Memory(f, f.fallback, False) for f in fragments))

    def _store_memories(self, memories: tuple[Memory, ...]) -> None:
        for memory in memories:
            self.memories[memory.fragment.id] = memory
        if memories:
            self.new_memories = memories

    def update(self) -> None:
        if not self.generation_in_progress:
            return
        try:
            result, memories = self._results.get_nowait()
        except Empty:
            return
        self.turns[-1].result = result
        self._store_memories(memories)
        self.generation_in_progress = False
