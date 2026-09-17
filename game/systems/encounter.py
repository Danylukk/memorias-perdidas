from queue import Empty, Queue
from threading import Thread

from game.models.state import new_game
from game.systems.choices import Choice, apply_choice, get_choice
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE


class Encounter:
    """Um encontro/uma escolha. Estado e consumo da fila pertencem ao loop principal."""

    def __init__(self, service: DialogueService):
        self.service = service
        self.state = new_game()
        self.choice: Choice | None = None
        self.result: DialogueResult | None = None
        self.generation_in_progress = False
        self._results: Queue[DialogueResult] = Queue(maxsize=1)

    def choose(self, choice_id: int) -> bool:
        if self.generation_in_progress or self.choice is not None:
            return False
        choice = get_choice(choice_id)
        self.state = apply_choice(self.state, choice.id)
        self.choice = choice
        self._start()
        return True

    def retry(self) -> bool:
        if self.generation_in_progress or self.result is None or self.result.ok:
            return False
        # Reenvia a mesma ação já aplicada, somente após clique explícito.
        self._start()
        return True

    def _start(self) -> None:
        self.generation_in_progress = True
        self.result = None
        state, choice = self.state, self.choice

        def work():
            try:
                result = self.service.respond(state, choice)
            except Exception:
                result = DialogueResult(error=ERROR_MESSAGE)
            self._results.put(result)

        try:
            # Fechar a janela não precisa aguardar a rede; worker não acessa Pygame.
            Thread(target=work, daemon=True, name="darian-dialogue").start()
        except RuntimeError:
            self.generation_in_progress = False
            self.result = DialogueResult(error=ERROR_MESSAGE)

    def update(self) -> None:
        if not self.generation_in_progress:
            return
        try:
            self.result = self._results.get_nowait()
        except Empty:
            return
        self.generation_in_progress = False
