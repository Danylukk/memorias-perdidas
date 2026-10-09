import json
import time
from threading import Event
from unittest.mock import MagicMock

import pygame
import pytest

from game.app import GameApp
from game.config import Settings
from game.screens.ending import EndingScreen
from game.screens.fragments import FragmentsScreen
from game.screens.gameplay import GameplayScreen
from game.screens.menu import MenuScreen
from game.screens.settings import SettingsScreen
from game.screens.ui import SIZE
from game.systems import save
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


def key(code):
    return pygame.event.Event(pygame.KEYDOWN, key=code)


def wait_for_ui(app):
    deadline = time.monotonic() + 3
    screen = app.screen
    while (screen.journey.busy or screen.walk_target is not None) and time.monotonic() < deadline:
        screen.update()
        app.draw()
        time.sleep(0.001)
    screen.update()
    assert not screen.journey.busy


@pytest.fixture
def app():
    client = MagicMock(spec=OpenAIClient)
    client.generate.side_effect = reply
    app = GameApp(DialogueService(client))
    yield app, client
    app.close()


def test_screens_are_16_9_like_the_cp4_mockups(app):
    app, _ = app
    assert SIZE == (1280, 720)
    assert [action for action, _, _ in MenuScreen.ITEMS] == ["new_game", "continue", "fragments", "settings", "quit"]
    app.draw()
    assert not app.screen.can_continue
    app.handle_event(click(MenuScreen.CONTINUE))  # sem save, CONTINUAR fica desabilitado
    assert isinstance(app.screen, MenuScreen)


def test_menu_choice_pending_result_and_reset(app):
    app, client = app
    entered, release = Event(), Event()

    def delayed(prompt):
        entered.set()
        assert release.wait(3)
        return reply(prompt)

    client.generate.side_effect = delayed
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert isinstance(app.screen, GameplayScreen)
    assert app.screen.dialogue_text == "Você... está vivo?"
    assert app.screen.actions() == ["Quem é você?", "Você me conhece?", "Ajudar o soldado", "Ir embora"]
    app.draw()
    try:
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
        assert entered.wait(3)
        assert app.screen.encounter.state.player.empatia == 2
        assert app.screen.encounter.state.npc.confianca_em_kael == 30
        assert app.screen.dialogue_text == "Darian está pensando..."
        for _ in range(5):
            app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
            app.handle_event(key(pygame.K_ESCAPE))
            app.screen.update()
            app.draw()
        assert isinstance(app.screen, GameplayScreen)
    finally:
        release.set()
    wait_for_ui(app)
    assert app.screen.dialogue_text == "Ainda respiro. Fique comigo."
    assert app.screen.actions()[0] == "Resposta curiosidade"
    assert client.generate.call_count == 1
    app.handle_event(key(pygame.K_ESCAPE))
    assert isinstance(app.screen, MenuScreen) and app.screen.can_continue
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert app.screen.encounter.state.player.empatia == 0
    assert app.screen.encounter.state.npc.confianca_em_kael == 20


def test_missing_key_continues_by_script_and_retry_does_not_reapply(app):
    app, _ = app
    app.service = DialogueService(OpenAIClient(Settings()))
    app.handle_event(click(MenuScreen.NEW_GAME))
    app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
    wait_for_ui(app)
    screen = app.screen
    assert screen.failed
    assert screen.dialogue_text == screen.encounter.choice.fallback
    assert screen.encounter.result.source == "roteiro"
    assert len(screen.actions()) == 4
    app.draw()
    app.handle_event(click(GameplayScreen.RETRY))
    wait_for_ui(app)
    assert screen.encounter.state.player.empatia == 2
    assert screen.encounter.state.npc.confianca_em_kael == 30


def test_close_while_request_is_pending(app):
    app, client = app
    release = Event()
    client.generate.side_effect = lambda prompt: (release.wait(3) and reply(prompt))
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
    app.window = pygame.display.set_mode((640, 360))
    app.draw()
    x, y = MenuScreen.NEW_GAME.center
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x // 2, y // 2)))
    assert isinstance(app.screen, GameplayScreen)
    app.handle_event(key(pygame.K_ESCAPE))
    x, y = MenuScreen.EXIT.center
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x // 2, y // 2)))
    assert not app.running


def test_full_playthrough_with_exploration_lira_and_ending(app):
    app, client = app
    app.handle_event(click(MenuScreen.NEW_GAME))
    screen = app.screen
    for _ in range(5):  # Ajudar o soldado, depois sempre a opção gerada de lealdade
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
        wait_for_ui(app)
        app.draw()
    assert screen.encounter.finished and "darian" in screen.journey.memories
    assert screen.actions() == ["Explorar as ruínas"]
    app.handle_event(click(GameplayScreen.WIDE))
    assert screen.journey.phase == "exploracao"
    assert screen.actions() == ["Estandarte", "Espadas", "Soldado caído", "Medalhão", "Falar com Lira"]
    assert screen.button_rects() == GameplayScreen.EXPLORE_RECTS
    app.handle_event(click(GameplayScreen.EXPLORE_RECTS[0]))  # Kael caminha até o estandarte
    assert screen.walk_target is not None
    wait_for_ui(app)
    assert "ordem_de_arkan" in screen.journey.memories
    assert screen.journey.memories["ordem_de_arkan"].generated
    app.handle_event(key(pygame.K_TAB))
    app.draw()
    assert screen.show_profile
    app.handle_event(key(pygame.K_TAB))
    app.handle_event(key(pygame.K_f))
    assert isinstance(app.screen, FragmentsScreen)
    app.draw()
    app.handle_event(click(FragmentsScreen.CARD_RECTS[1]))
    app.handle_event(click(FragmentsScreen.CARD_RECTS[2]))  # Lira ainda bloqueada
    app.handle_event(click(FragmentsScreen.CARD_RECTS[7]))  # espaço de parte futura
    app.draw()
    app.handle_event(click(FragmentsScreen.BACK))
    assert app.screen is screen
    curiosity = screen.journey.player.curiosidade
    app.handle_event(click(GameplayScreen.EXPLORE_RECTS[3]))  # Medalhão: sem andar
    assert screen.walk_target is None and screen.journey.message.heading == "Medalhão"
    assert screen.journey.player.curiosidade == curiosity + 1
    app.handle_event(click(GameplayScreen.EXPLORE_RECTS[4]))  # Falar com Lira
    wait_for_ui(app)
    assert screen.journey.phase == "lira"
    assert screen.journey.darian_outcome == "cuidado"
    assert screen.dialogue_text.startswith("Kael... Darian disse que você o ajudou.")
    for _ in range(3):
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[1]))
        wait_for_ui(app)
        app.draw()
    assert screen.actions() == ["Decidir em quem confiar"]
    app.handle_event(key(pygame.K_RETURN))
    assert screen.actions() == ["Confiar em Darian", "Confiar em Lira", "Confiar nos dois", "Seguir sozinho"]
    app.draw()
    app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
    assert screen.actions() == ["Ver desfecho"]
    app.handle_event(click(GameplayScreen.WIDE))
    assert isinstance(app.screen, EndingScreen)
    assert app.screen.ending.titulo == "O Protetor"  # empatia 5 empata com lealdade 5
    app.draw()
    assert not save.has_progress()
    app.handle_event(click(EndingScreen.MENU))
    app.handle_event(click(MenuScreen.FRAGMENTS))
    assert isinstance(app.screen, FragmentsScreen)
    assert {"darian", "ordem_de_arkan"} <= set(app.screen.memories)
    app.handle_event(key(pygame.K_ESCAPE))
    assert isinstance(app.screen, MenuScreen)


def test_continue_restores_saved_journey(app):
    app, _ = app
    app.handle_event(click(MenuScreen.NEW_GAME))
    app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
    wait_for_ui(app)
    trust = app.screen.journey.trust("darian")
    app.handle_event(key(pygame.K_ESCAPE))
    app.handle_event(click(MenuScreen.CONTINUE))
    assert isinstance(app.screen, GameplayScreen)
    assert app.screen.encounter.round_index == 1
    assert app.screen.journey.trust("darian") == trust == 30
    assert app.screen.actions()[0] == "Resposta curiosidade"


def test_settings_toggle_and_persist(app):
    app, _ = app
    app.handle_event(click(MenuScreen.SETTINGS))
    assert isinstance(app.screen, SettingsScreen)
    app.draw()
    app.handle_event(click(SettingsScreen.ROWS[0]))  # desliga a IA
    app.handle_event(click(SettingsScreen.ROWS[2]))  # texto animado
    assert save.load_settings() == {"usar_ia": False, "tela_cheia": False, "texto_animado": False}
    assert app.offline and "roteiro offline" in app.mode
    app.handle_event(click(SettingsScreen.BACK))
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert app.screen.journey.offline and not app.screen.animate_text


def test_offline_mode_without_key_plays_to_the_end(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr("game.config.PROJECT_ROOT", tmp_path)
    app = GameApp()
    try:
        assert app.offline and "roteiro offline" in app.screen.mode
        app.draw()
        app.handle_event(click(MenuScreen.NEW_GAME))
        screen = app.screen
        for _ in range(40):
            if screen.journey.phase == "fim":
                break
            index = 4 if screen.journey.phase == "exploracao" else 0
            app.handle_event(click(screen.button_rects()[index]))
            wait_for_ui(app)
            assert not screen.failed
            app.draw()
        assert screen.journey.phase == "fim"
        app.handle_event(click(GameplayScreen.WIDE))
        assert isinstance(app.screen, EndingScreen)
        app.draw()
    finally:
        app.close()


def test_fade_between_screens_and_scenes(app):
    from game.screens import ui

    app, _ = app
    before = app.fade_t0
    app.handle_event(click(MenuScreen.NEW_GAME))
    assert app.fade_t0 > before
    app.fade_t0 = time.monotonic()
    app.draw()
    dark = app.canvas.get_at((640, 300))
    app.fade_t0 = time.monotonic() - ui.FADE_SECONDS
    app.draw()
    assert sum(app.canvas.get_at((640, 300))[:3]) > sum(dark[:3])
    screen = app.screen
    for _ in range(5):
        app.handle_event(click(GameplayScreen.CHOICE_RECTS[2]))
        wait_for_ui(app)
    t0 = screen._fade_t0
    app.handle_event(click(GameplayScreen.WIDE))  # Darian → exploração
    assert screen.journey.phase == "exploracao" and screen._fade_t0 > t0


def test_scene_fade_darkens_then_clears(app):
    from game.screens import ui

    screen = GameplayScreen(MagicMock(), offline=True, animate_text=False)
    canvas = pygame.Surface(SIZE)
    screen._fade_t0 = -10.0
    screen.draw(canvas)
    clear = sum(canvas.get_at((640, 300))[:3])
    screen._fade_t0 = time.monotonic() - ui.FADE_SECONDS * 0.4
    screen.draw(canvas)
    assert sum(canvas.get_at((640, 300))[:3]) < clear
