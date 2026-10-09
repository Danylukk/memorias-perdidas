"""Tela 1 — Menu Principal (CP4, Figura 4)."""
import pygame

from game.screens.ui import (MUTED, asset, background, button, credits_footer, fit_image, label, sprite)


class MenuScreen:
    # Posições do mockup (1672×941) convertidas para 1280×720.
    NEW_GAME = pygame.Rect(738, 262, 214, 44)
    CONTINUE = pygame.Rect(740, 318, 210, 40)
    FRAGMENTS = pygame.Rect(740, 368, 210, 40)
    SETTINGS = pygame.Rect(740, 418, 210, 40)
    EXIT = pygame.Rect(740, 468, 210, 40)
    ITEMS = (("new_game", "Novo Jogo", NEW_GAME), ("continue", "Continuar", CONTINUE),
             ("fragments", "Fragmentos", FRAGMENTS), ("settings", "Configurações", SETTINGS),
             ("quit", "Sair", EXIT))

    def __init__(self, mode="", can_continue=False):
        self.mode = mode
        self.can_continue = can_continue
        self.selected = 0

    def enabled(self, action):
        return action != "continue" or self.can_continue

    def handle_event(self, event):
        actions = [action for action, _, _ in self.ITEMS]
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                step = 1 if event.key == pygame.K_DOWN else -1
                self.selected = (self.selected + step) % len(actions)
                while not self.enabled(actions[self.selected]):
                    self.selected = (self.selected + step) % len(actions)
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return actions[self.selected]
            if event.key == pygame.K_ESCAPE:
                return "quit"
            if event.key == pygame.K_f:
                return "fragments"
        if event.type == pygame.MOUSEMOTION:
            for index, (action, _, rect) in enumerate(self.ITEMS):
                if rect.collidepoint(event.pos) and self.enabled(action):
                    self.selected = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, _, rect in self.ITEMS:
                if rect.collidepoint(event.pos) and self.enabled(action):
                    return action
        return None

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(background(20), (0, 0))
        kael = sprite("kael", 0.36)
        surface.blit(kael, kael.get_rect(midbottom=(400, 650)))
        fit_image(surface, asset("ui/logo_memorias_perdidas.png"), pygame.Rect(640, 14, 420, 236))
        for index, (action, text, rect) in enumerate(self.ITEMS):
            button(surface, rect, text, self.enabled(action), index == self.selected,
                   size=23 if action == "new_game" else 19, caps=True,
                   icon="ui/icone_cristal.png" if action == "fragments" else None)
        if self.mode:
            label(surface, self.mode, (845, 520), 15, (200, 190, 170), italic=True, align="center", shadow=True)
        credits_footer(surface, [("portraits/kael.png", "Personagem Kael — ChatGPT,\ngeração de imagens"),
                                 ("backgrounds/bg_ruinas_principal.png", "Cenário — ChatGPT,\ngeração de imagens")])
