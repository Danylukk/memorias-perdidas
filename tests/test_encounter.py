import time
from threading import Event
from unittest.mock import MagicMock

from game.models.state import new_game
from game.systems.dialogue import DialogueResult, ERROR_MESSAGE
from game.systems.encounter import Encounter


def await_result(encounter):
    deadline = time.monotonic() + 3
    while encounter.generation_in_progress and time.monotonic() < deadline:
        encounter.update()
        time.sleep(0.001)
    assert not encounter.generation_in_progress


def test_choice_updated_before_thread_and_duplicates_blocked():
    entered, release = Event(), Event()
    received = []

    def respond(state, choice, history=(), first_id=1000):
        received.append((state, choice))
        entered.set()
        assert release.wait(3)
        return DialogueResult(text="Ainda respiro.")

    service = MagicMock()
    service.converse.side_effect = respond
    encounter = Encounter(service)
    try:
        assert encounter.choose(3)
        assert entered.wait(3)
        assert encounter.generation_in_progress
        assert encounter.state.player.empatia == 2
        assert received[0][0].npc.confianca_em_kael == 30
        assert not encounter.choose(3)
        assert not encounter.choose(4)
        assert not encounter.retry()
        encounter.update()  # Não aguarda o worker.
        assert encounter.result is None
    finally:
        release.set()
    await_result(encounter)
    assert encounter.result.ok
    assert not encounter.choose(1)
    assert not encounter.retry()
    assert service.converse.call_count == 1


def test_retry_preserves_effects_and_new_game_resets():
    service = MagicMock()
    service.converse.side_effect = [DialogueResult(error=ERROR_MESSAGE), DialogueResult(text="Fique.")]
    encounter = Encounter(service)
    encounter.choose(3)
    await_result(encounter)
    state = encounter.state
    assert not encounter.result.ok
    assert encounter.retry()
    await_result(encounter)
    assert encounter.result.ok
    assert encounter.state == state
    assert service.converse.call_count == 2
    assert service.converse.call_args_list[0] == service.converse.call_args_list[1]
    assert Encounter(service).state == new_game()


def test_unexpected_worker_failure_unlocks():
    service = MagicMock()
    service.converse.side_effect = RuntimeError("não expor")
    encounter = Encounter(service)
    encounter.choose(4)
    await_result(encounter)
    assert encounter.result.error == ERROR_MESSAGE
    assert encounter.result.source == "roteiro"  # a história segue pelo roteiro offline
    assert len(encounter.current_choices) == 4
    assert encounter.state.player.egoismo == 2


def test_thread_start_failure_is_controlled(monkeypatch):
    def fail(self):
        raise RuntimeError("cannot start thread")
    monkeypatch.setattr("game.systems.encounter.Thread.start", fail)
    encounter = Encounter(MagicMock())
    assert encounter.choose(1)
    assert not encounter.generation_in_progress
    assert encounter.result.error == ERROR_MESSAGE
