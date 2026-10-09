"""Regressões encontradas na revisão de entrega; execução real de eventos e desenho SDL."""
import json
import time
from unittest.mock import MagicMock

import pygame
import pytest

from game.app import GameApp
from game.screens.gameplay import GameplayScreen
from game.screens import ui
from game.systems import save
from game.systems.dialogue import parse_turn, validate_response
from game.systems.journey import load_progress
from game.systems.script import load_script


def settle(screen):
    deadline = time.monotonic() + 3
    while screen.journey.busy and time.monotonic() < deadline:
        screen.update()
        time.sleep(0.001)
    assert not screen.journey.busy


@pytest.fixture
def offline_app():
    app = GameApp(MagicMock())
    app.settings['usar_ia'] = False
    yield app
    app.close()


def explore(app):
    app._route('new_game')
    screen = app.screen
    for _ in range(5):
        screen.activate(0)
        settle(screen)
    screen.activate(0)
    assert screen.journey.phase == 'exploracao'
    return screen


def test_new_game_can_continue_before_first_choice(offline_app):
    app = offline_app
    app._route('new_game')
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert app.screen.can_continue
    app._route('continue')
    assert isinstance(app.screen, GameplayScreen)
    assert app.screen.encounter.round_index == 0
    assert app.screen.dialogue_text == 'Você... está vivo?'


@pytest.mark.parametrize('exit_event', ['menu', 'close'])
def test_medallion_survives_menu_or_window_close(offline_app, exit_event):
    screen = explore(offline_app)
    before = screen.journey.player.curiosidade
    screen.activate(3)
    assert load_progress(offline_app.service, True).player.curiosidade == before + 1
    if exit_event == 'menu':
        offline_app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    else:
        offline_app.handle_event(pygame.event.Event(pygame.QUIT))
    restored = load_progress(offline_app.service, True)
    assert restored.player.curiosidade == before + 1
    assert restored.interact('medalhao')
    assert restored.player.curiosidade == before + 1


@pytest.mark.parametrize('text', [' '.join(['brasas'] * 48), ' '.join(['memórias'] * 46), 'W' * 360])
def test_valid_long_dialogue_fits_without_losing_lines(offline_app, text):
    app = offline_app
    app._route('new_game')
    screen = app.screen
    validate_response(text, 4, 420)
    screen.journey.encounter = None
    from game.systems.journey import Message
    screen.journey.message = Message('Memória recuperada — A Batalha', text, 'roteiro')
    box = screen.dialogue_box()
    lines = ui.wrap(text, box.width - 175, 13)
    assert len(lines) * 18 <= box.height - 62
    assert all(ui.font(13).size(line)[0] <= box.width - 175 for line in lines)
    assert box.bottom == GameplayScreen.DIALOGUE.bottom
    assert box.top >= 96
    assert box.bottom < GameplayScreen.CHOICE_RECTS[0].top
    screen.animate_text = False
    app.draw()


@pytest.mark.parametrize('count', [0, 4, 12])
def test_fragment_counter_text_stays_inside_frame(offline_app, monkeypatch, count):
    rect = pygame.Rect(1050, 22, 210, 44)
    drawn = []
    label = ui.label
    def record(*args, **kwargs):
        result = label(*args, **kwargs)
        drawn.append(result)
        return result
    monkeypatch.setattr(ui, 'label', record)
    ui.fragment_counter(offline_app.canvas, rect, count, 12)
    assert all(rect.inflate(-12, -8).contains(r) for r in drawn)


def test_four_asset_credits_fit_screen_without_overlapping(offline_app, monkeypatch):
    items = [(f'portraits/{name}.png', f'Personagem {name.capitalize()} — ChatGPT,\ngeração de imagens')
             for name in ('kael', 'darian', 'lira')]
    items.append(('backgrounds/bg_ruinas_principal.png', 'Cenário — ChatGPT,\ngeração de imagens'))
    labels, portraits = [], []
    old_label, old_portrait = ui.label, ui.portrait
    def record_label(*args, **kwargs):
        rect = old_label(*args, **kwargs)
        labels.append(rect)
        return rect
    def record_portrait(surface, rect, *args, **kwargs):
        portraits.append(rect)
        return old_portrait(surface, rect, *args, **kwargs)
    monkeypatch.setattr(ui, 'label', record_label)
    monkeypatch.setattr(ui, 'portrait', record_portrait)
    ui.credits_footer(offline_app.canvas, items, quote=False)
    assert all(ui.FOOTER.contains(r) for r in labels + portraits)
    for i, rect in enumerate(labels):
        assert not any(rect.colliderect(other) for other in labels[i + 1:] + portraits)


def test_repeated_ai_intents_are_rejected_even_with_different_labels():
    turn = {'fala': 'Ainda estou aqui.', 'opcoes': [
        {'texto': f'Resposta {i}', 'intencao': 'empatia'} for i in range(4)]}
    with pytest.raises(ValueError, match='Intenções repetidas'):
        parse_turn(json.dumps(turn), 1000)


def test_lira_offline_does_not_assert_kaels_former_role():
    line = load_script()['lira']['turnos']['2']['cuidado']['fala']
    assert 'soldado que você foi' not in line
    assert 'como você agiu nas ruínas' in line


def test_memory_gallery_paginates_long_text_without_losing_content(offline_app):
    from game.screens.fragments import FragmentsScreen
    from game.systems.fragments import Memory, get_fragment
    text = ' '.join(['brasas'] * 60)
    memory = Memory(get_fragment('a_batalha'), text, True)
    screen = FragmentsScreen({'a_batalha': memory})
    pages, size = screen.memory_pages(memory)
    assert len(pages) > 1
    assert ''.join(pages).replace(' ', '') == f'“{text}”'.replace(' ', '')
    assert all(len(ui.wrap(page, 296, size, italic=True)) * (size + 5) <= 96 for page in pages)
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEDOWN))
    assert screen.page == 1
    screen.draw(offline_app.canvas)
    screen.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
    assert screen.page == 0
