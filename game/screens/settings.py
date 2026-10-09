"""Configurações (opção do Menu Principal no mockup da CP4)."""
import pygame

from game.screens.ui import (GOLD, GOLD_BRIGHT, MUTED, TEXT, background, button, credits_footer, divider, label,
                             panel)


class SettingsScreen:
    PANEL = pygame.Rect(340, 90, 600, 470)
    ROWS = tuple(pygame.Rect(380, 180 + i * 80, 520, 58) for i in range(3))
    BACK = pygame.Rect(549, 490, 182, 40)

    def __init__(self, settings, ai_available, model=""):
        self.settings = dict(settings)
        self.ai_available = ai_available
        self.model = model
        self.selected = 0

    def rows(self):
        ia = ("Ligados" if self.settings["usar_ia"] else "Desligados (roteiro offline)") if self.ai_available \
            else "Indisponível — configure OPENAI_API_KEY e OPENAI_MODEL no .env"
        return (("usar_ia", "Diálogos com IA (ChatGPT / LLM)", ia),
                ("tela_cheia", "Tela cheia", "Sim" if self.settings["tela_cheia"] else "Não"),
                ("texto_animado", "Texto animado", "Sim" if self.settings["texto_animado"] else "Não"))

    def toggle(self, index):
        key = self.rows()[index][0]
        if key == "usar_ia" and not self.ai_available:
            return None
        self.settings[key] = not self.settings[key]
        return "settings_changed"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                self.selected = (self.selected + (1 if event.key == pygame.K_DOWN else -1)) % len(self.ROWS)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.toggle(self.selected)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.BACK.collidepoint(event.pos):
                return "back"
            for index, rect in enumerate(self.ROWS):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    return self.toggle(index)
        return None

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(background(130), (0, 0))
        panel(surface, self.PANEL, 235)
        label(surface, "CONFIGURAÇÕES", (self.PANEL.centerx, self.PANEL.y + 22), 32, GOLD_BRIGHT, align="center")
        divider(surface, self.PANEL.x + 60, self.PANEL.right - 60, self.PANEL.y + 70)
        for index, ((key, name, value), rect) in enumerate(zip(self.rows(), self.ROWS)):
            selected = index == self.selected
            pygame.draw.rect(surface, (30, 26, 20) if selected else (18, 18, 22), rect)
            pygame.draw.rect(surface, GOLD_BRIGHT if selected else (70, 60, 44), rect, 2 if selected else 1)
            label(surface, name, (rect.x + 18, rect.y + 8), 19, TEXT)
            disabled = key == "usar_ia" and not self.ai_available
            label(surface, value, (rect.x + 18, rect.y + 33), 14, MUTED if disabled else GOLD, italic=True)
        info = f"Modelo configurado: {self.model}" if self.ai_available else "Sem chave da API: o jogo usa o roteiro offline."
        label(surface, info, (self.PANEL.centerx, 432), 14, MUTED, italic=True, align="center")
        label(surface, "Clique ou Enter para alternar", (self.PANEL.centerx, 454), 13, MUTED, align="center")
        button(surface, self.BACK, "Voltar", caps=True, selected=True, size=18)
        credits_footer(surface, [])
