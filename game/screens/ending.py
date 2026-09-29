"""Fim da jornada: quem Kael se tornou e em quem decidiu confiar (CP4 §1.7)."""
import pygame

from game.screens.ui import (GOLD, GOLD_BRIGHT, MUTED, TEXT, background, button, cover, credits_footer, divider,
                             label, panel, paragraph, sprite)
from game.systems.fragments import TOTAL_FRAGMENTS

ATTRIBUTES = (("empatia", "Empatia"), ("agressividade", "Agressividade"), ("curiosidade", "Curiosidade"),
              ("egoismo", "Egoísmo"), ("lealdade", "Lealdade"))


class EndingScreen:
    NEW_GAME = pygame.Rect(380, 588, 230, 44)
    FRAGMENTS = pygame.Rect(630, 588, 230, 44)
    MENU = pygame.Rect(880, 588, 230, 44)

    def __init__(self, journey):
        self.player = journey.player
        self.trust = {npc_id: journey.trust(npc_id) for npc_id in ("darian", "lira")}
        self.memories = dict(journey.memories)
        self.ending = journey.ending()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                return "fragments"
            if event.key == pygame.K_RETURN:
                return "new_game"
            if event.key == pygame.K_ESCAPE:
                return "menu"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in ((self.FRAGMENTS, "fragments"), (self.MENU, "menu"), (self.NEW_GAME, "new_game")):
                if rect.collidepoint(event.pos):
                    return action
        return None

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(background(120), (0, 0))
        kael = sprite("kael", 0.4)
        surface.blit(kael, kael.get_rect(midbottom=(190, 640)))
        label(surface, "FIM DA JORNADA", (745, 26), 18, MUTED, align="center")
        label(surface, f"Kael, {self.ending.titulo}", (745, 50), 40, GOLD_BRIGHT, align="center")
        paragraph(surface, self.ending.descricao, pygame.Rect(420, 108, 650, 56), 18, TEXT, italic=True,
                  align="center")
        panel(surface, pygame.Rect(380, 176, 330, 396), 225)
        label(surface, "QUEM KAEL SE TORNOU", (545, 192), 17, GOLD, align="center")
        divider(surface, 410, 680, 222)
        rows = [(name, getattr(self.player, key)) for key, name in ATTRIBUTES]
        rows += [("Vida", self.player.vida), ("Energia", self.player.energia)]
        for index, (name, value) in enumerate(rows):
            label(surface, name, (412, 236 + index * 30), 18)
            label(surface, str(value), (678, 236 + index * 30), 18, GOLD_BRIGHT, align="right")
        panel(surface, pygame.Rect(730, 176, 380, 396), 225)
        label(surface, "EM QUEM KAEL CONFIOU", (920, 192), 17, GOLD, align="center")
        divider(surface, 760, 1080, 222)
        paragraph(surface, self.ending.destino, pygame.Rect(758, 234, 324, 110), 18, TEXT)
        label(surface, f"Confiança — Darian: {self.trust['darian']}  ·  Lira: {self.trust['lira']}",
              (920, 352), 15, MUTED, align="center")
        label(surface, f"Fragmentos: {len(self.memories)}/{TOTAL_FRAGMENTS}", (920, 386), 18, GOLD, align="center")
        for index, memory in enumerate(self.memories.values()):
            rect = pygame.Rect(758 + index * 82, 418, 72, 72)
            surface.blit(cover(f"fragments/{memory.fragment.id}.png", rect.size), rect)
            pygame.draw.rect(surface, GOLD, rect, 1)
            label(surface, memory.fragment.titulo, (rect.centerx, rect.bottom + 6), 11, MUTED, align="center")
        if not self.memories:
            label(surface, "Nenhuma memória recuperada.", (920, 440), 15, MUTED, italic=True, align="center")
        button(surface, self.NEW_GAME, "Novo Jogo [Enter]", selected=True)
        button(surface, self.FRAGMENTS, "Fragmentos [F]")
        button(surface, self.MENU, "Menu [Esc]")
        credits_footer(surface, [("portraits/kael.png", "Personagens — ChatGPT,\ngeração de imagens"),
                                 ("backgrounds/bg_ruinas_principal.png", "Cenário — ChatGPT,\ngeração de imagens")])
