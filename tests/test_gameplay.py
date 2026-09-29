import json
import time
from threading import Event
from unittest.mock import MagicMock

import pygame
import pytest

from game.app import GameApp
from game.config import Settings
from game.screens.gameplay import GameplayScreen
from game.screens.menu import MenuScreen
from game.systems.dialogue import DialogueService
from game.systems.openai_client import OpenAIClient


def reply(prompt, fala="Ainda respiro. Fique comigo."):
    """Turnos pedem JSON (fala + opções); fala final e fragmentos pedem texto."""
    if prompt.schema is None:
        return fala
    return json.dumps({"fala": fala, "opcoes": [
        {"texto": f"Resposta {intent}", "intencao": intent}
        for intent in ("curiosidade", "empatia", "lealdade", "agressividade")]})


def click(rect):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


def wait_for_ui(app):
    deadline = time.monotonic() + 3
    while app.screen.encounter.generation_in_progress and time.monotonic() < deadline:
        app.screen.update()
        app.draw()
        time.sleep(0.001)
    assert not app.screen.encounter.generation_in_progress


@pytest.fixture
def app():
    client = MagicMock(spec=OpenAIClient)
    client.generate.side_effect = reply
    app = GameApp(DialogueService(client))
    yield app, client
    app.close()


def test_menu_choice_pending_result_and_reset(app):
    app, client = app
    entered, release = Event(), Event()

    def delayed(prompt):
        entered.set()
        assert release.wait(3)
        return reply(prompt)

    client.generate.side_effect = delayed
    assert isinstance(app.screen, MenuScreen)
    app.draw()
    client.generate.assert_not_called()
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert isinstance(app.screen, GameplayScreen)
    assert app.screen.dialogue_text == "Você... está vivo?"
    assert len(app.screen.CHOICE_RECTS) == 4
    app.draw()
    try:
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
        assert entered.wait(3)
        assert app.screen.encounter.state.player.empatia == 2
        assert app.screen.encounter.state.npc.confianca_em_kael == 30
        assert app.screen.dialogue_text == "Darian está pensando..."
        for _ in range(8):
            app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
            app.screen.update()
            app.draw()
        app.handle_event(click(GameplayScreen.MENU))
        assert isinstance(app.screen, GameplayScreen)
    finally:
        release.set()
    wait_for_ui(app)
    assert app.screen.dialogue_text == "Ainda respiro. Fique comigo."
    assert client.generate.call_count == 1
    app.handle_event(click(GameplayScreen.MENU))
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert app.screen.encounter.state.player.empatia == 0
    assert app.screen.encounter.state.npc.confianca_em_kael == 20


def test_missing_key_shows_error_and_retry_does_not_reapply(app):
    app, _ = app
    app.service = DialogueService(OpenAIClient(Settings()))
    app.handle_event(click(MenuScreen.NEW_GAME))
    app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
    wait_for_ui(app)
    # Falha nunca vira fala da IA: a tela mostra a reserva roteirizada, identificada como tal.
    assert app.screen.failed
    assert app.screen.dialogue_text == app.screen.encounter.choice.fallback
    assert "Não foi possível" in app.screen.encounter.result.error
    assert app.screen.encounter.result.text == ""
    app.draw()
    app.handle_event(click(GameplayScreen.RETRY))
    wait_for_ui(app)
    assert app.screen.encounter.state.player.empatia == 2
    assert app.screen.encounter.state.npc.confianca_em_kael == 30
    app.handle_event(click(GameplayScreen.MENU))
    assert isinstance(app.screen, MenuScreen)


def test_close_while_request_is_pending(app):
    app, client = app
    release = Event()
    client.generate.side_effect = lambda prompt: (release.wait(3) and "Fique.")
    app.handle_event(click(MenuScreen.NEW_GAME))
    app.handle_event(click(GameplayScreen.CHOICE_RECTS[0]))
    try:
        app.handle_event(pygame.event.Event(pygame.QUIT))
        assert not app.running
    finally:
        release.set()
    wait_for_ui(app)


def test_scaled_window_clicks_and_menu_exit(app):
    app, _ = app
    app.window = pygame.display.set_mode((600, 400))
    app.draw()
    x, y = MenuScreen.NEW_GAME.center
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x // 2, y // 2)))
    assert isinstance(app.screen, GameplayScreen)
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    x, y = MenuScreen.EXIT.center
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x // 2, y // 2)))
    assert not app.running


def test_full_playthrough_fragments_and_ending(app):
    from game.screens.ending import EndingScreen
    from game.screens.fragments import FragmentsScreen

    app, client = app
    app.handle_event(click(MenuScreen.NEW_GAME))
    for _ in range(5):  # Ajudar o soldado, depois sempre a opção gerada de lealdade
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
        wait_for_ui(app)
        app.draw()
    screen = app.screen
    assert screen.encounter.turns[1].choice.label == "Resposta lealdade"
    assert screen.encounter.finished
    assert set(screen.encounter.memories) == {"darian", "o_medalhao"}
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
    assert isinstance(app.screen, FragmentsScreen)
    app.draw()
    app.handle_event(click(FragmentsScreen.CARD_RECTS[5]))  # slot bloqueado
    app.draw()
    app.handle_event(click(FragmentsScreen.BACK))
    assert app.screen is screen
    app.handle_event(click(GameplayScreen.ENDING))
    assert isinstance(app.screen, EndingScreen)
    assert app.screen.ending.titulo == "O Companheiro"
    app.draw()
    app.handle_event(click(EndingScreen.MENU))
    assert isinstance(app.screen, MenuScreen)
    app.handle_event(click(MenuScreen.FRAGMENTS))
    assert set(app.screen.memories) == {"darian", "o_medalhao"}
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert isinstance(app.screen, MenuScreen)
    # 5 turnos + 2 fragmentos; nenhuma chamada extra.
    assert client.generate.call_count == 7
