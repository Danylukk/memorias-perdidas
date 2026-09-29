import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.config import Settings
from game.screens.ending import EndingScreen
from game.screens.fragments import FragmentsScreen
from game.screens.gameplay import GameplayScreen
from game.screens.menu import MenuScreen
from game.screens.ui import SIZE, font
from game.systems.dialogue import DialogueService
from game.systems.openai_client import OpenAIClient


class GameApp:
    def __init__(self, dialogue_service=None):
        font.cache_clear()
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Memórias Perdidas — MVP")
        self.canvas = pygame.Surface(SIZE)
        self.clock = pygame.time.Clock()
        self.offline = False
        if dialogue_service is None:
            settings = Settings.from_env()
            # Sem chave/modelo, o jogo roda inteiro pelo roteiro offline, sem tentar a rede.
            self.offline = not (settings.api_key and settings.model)
            dialogue_service = DialogueService(OpenAIClient(settings))
            self.mode = ("Modo: roteiro offline (sem chave da API)" if self.offline
                         else f"Modo: IA — {settings.model}")
        else:
            self.mode = ""
        self.service = dialogue_service
        self.screen = MenuScreen(self.mode)
        # Memórias da última partida desta execução; não há save em disco no MVP.
        self.memories = {}
        self.return_screen = None
        self.running = True

    def viewport(self):
        width, height = self.window.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        size = (max(1, round(SIZE[0] * scale)), max(1, round(SIZE[1] * scale)))
        return pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            viewport = self.viewport()
            if not viewport.collidepoint(event.pos):
                return
            event = pygame.event.Event(event.type, dict(event.dict, pos=(
                int((event.pos[0] - viewport.x) * SIZE[0] / viewport.width),
                int((event.pos[1] - viewport.y) * SIZE[1] / viewport.height),
            )))
        action = self.screen.handle_event(event)
        if action == "new_game":
            self.screen = GameplayScreen(self.service, self.offline)
        elif action == "menu":
            self.screen = MenuScreen(self.mode)
        elif action == "fragments":
            self.return_screen = self.screen
            self.screen = FragmentsScreen(self.current_memories())
        elif action == "back":
            self.screen, self.return_screen = self.return_screen or MenuScreen(self.mode), None
        elif action == "ending":
            self.memories = dict(self.screen.encounter.memories)
            self.screen = EndingScreen(self.screen.encounter)
        elif action == "quit":
            self.running = False

    def current_memories(self):
        if isinstance(self.screen, GameplayScreen):
            self.memories = dict(self.screen.encounter.memories)
        return self.memories

    def draw(self):
        self.screen.draw(self.canvas)
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
