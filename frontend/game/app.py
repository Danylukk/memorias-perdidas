import os
from time import monotonic

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.config import Settings
from game.screens.ending import EndingScreen
from game.screens.fragments import FragmentsScreen
from game.screens.gameplay import GameplayScreen
from game.screens.menu import MenuScreen
from game.screens.settings import SettingsScreen
from game.screens.ui import SIZE, fade_in, font
from game.systems import save
from game.systems.dialogue import DialogueService
from game.systems.journey import load_gallery, load_progress
from game.systems.api_client import NarrativeAPIClient


class GameApp:
    def __init__(self, dialogue_service=None):
        font.cache_clear()
        pygame.display.init()
        pygame.font.init()
        self.settings = save.load_settings()
        self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Memórias Perdidas — MVP")
        self.canvas = pygame.Surface(SIZE)
        self.clock = pygame.time.Clock()
        if dialogue_service is None:
            config = Settings.from_env()
            self.ai_available = bool(config.api_key and config.api_url)
            self.model = "via API do grupo"
            dialogue_service = DialogueService(NarrativeAPIClient(config))
        else:
            # Serviço injetado (testes): tratado como IA disponível.
            self.ai_available, self.model = True, "injetado"
        self.service = dialogue_service
        self.return_screen = None
        self.apply_display()
        self.screen = self.menu()
        self.fade_t0 = monotonic()
        self.running = True

    @property
    def offline(self):
        # Sem acesso à API, ou com a IA desligada nas Configurações, usa roteiro offline.
        return not (self.ai_available and self.settings["usar_ia"])

    @property
    def mode(self):
        return "Diálogos: roteiro offline" if self.offline else f"Diálogos: ChatGPT (LLM) — {self.model}"

    def menu(self):
        return MenuScreen(self.mode, save.has_progress())

    def apply_display(self):
        flags = pygame.FULLSCREEN if self.settings["tela_cheia"] else pygame.RESIZABLE
        try:
            self.window = pygame.display.set_mode(SIZE, flags)
        except pygame.error:
            self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)

    def viewport(self):
        width, height = self.window.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        size = (max(1, round(SIZE[0] * scale)), max(1, round(SIZE[1] * scale)))
        return pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)

    def to_canvas(self, pos):
        viewport = self.viewport()
        return (int((pos[0] - viewport.x) * SIZE[0] / viewport.width),
                int((pos[1] - viewport.y) * SIZE[1] / viewport.height))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._persist_gameplay()
            self.running = False
            return
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            if not self.viewport().collidepoint(event.pos):
                return
            event = pygame.event.Event(event.type, dict(event.dict, pos=self.to_canvas(event.pos)))
        previous = self.screen
        action = self.screen.handle_event(event)
        self._route(action)
        if self.screen is not previous:
            self.fade_t0 = monotonic()

    def _route(self, action):
        if action == "new_game":
            save.delete(save.PROGRESS)
            self.screen = GameplayScreen(self.service, self.offline, animate_text=self.settings["texto_animado"])
            self._persist_gameplay()
        elif action == "continue":
            journey = load_progress(self.service, self.offline)
            self.screen = (GameplayScreen(self.service, self.offline, journey, self.settings["texto_animado"])
                           if journey else self.menu())
        elif action == "menu":
            self._persist_gameplay()
            self.screen = self.menu()
        elif action == "fragments":
            self.return_screen = self.screen
            memories = (self.screen.journey.memories if isinstance(self.screen, GameplayScreen)
                        else load_gallery())
            self.screen = FragmentsScreen(memories)
        elif action == "settings":
            self.screen = SettingsScreen(self.settings, self.ai_available, self.model)
        elif action == "settings_changed":
            self.settings = dict(self.screen.settings)
            save.save_settings(self.settings)
            self.apply_display()
        elif action == "back":
            if isinstance(self.screen, SettingsScreen) or self.return_screen is None:
                self.screen, self.return_screen = self.menu(), None
            else:
                self.screen, self.return_screen = self.return_screen, None
        elif action == "ending":
            self.screen = EndingScreen(self.screen.journey)
        elif action == "quit":
            self._persist_gameplay()
            self.running = False

    def _persist_gameplay(self):
        if isinstance(self.screen, GameplayScreen):
            self.screen.journey.persist()

    def draw(self):
        self.screen.draw(self.canvas)
        fade_in(self.canvas, self.fade_t0, monotonic())
        viewport = self.viewport()
        self.window.fill((0, 0, 0))
        self.window.blit(pygame.transform.smoothscale(self.canvas, viewport.size), viewport)
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    self.handle_event(event)
                self.screen.update()
                self.draw()
                self.clock.tick(60)
        finally:
            self.close()

    def close(self):
        font.cache_clear()
        pygame.quit()
