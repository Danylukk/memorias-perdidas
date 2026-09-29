"""Tela 3 — Fragmentos de Memória (CP4, Figura 6)."""
import pygame

from game.screens.ui import (GOLD, GOLD_BRIGHT, MUTED, TEXT, background, button, cover, credits_footer, darken,
                             divider, fragment_counter, label, lock, panel, paragraph)
from game.systems.fragments import FRAGMENTS, TOTAL_FRAGMENTS

LOCKED_ART = tuple(f"fragments/bloqueado_{i}.png" for i in range(1, 9))


class FragmentsScreen:
    # Posições do mockup (1672×941) convertidas para 1280×720.
    TITLE = pygame.Rect(121, 27, 560, 90)
    GRID = pygame.Rect(167, 160, 643, 457)
    DETAIL = pygame.Rect(825, 149, 348, 478)
    BACK = pygame.Rect(909, 580, 182, 38)
    CARD_RECTS = tuple(pygame.Rect(178 + (i % 4) * 158, 171 + (i // 4) * 147, 148, 139) for i in range(TOTAL_FRAGMENTS))

    def __init__(self, memories):
        self.memories = dict(memories)
        # Os 4 primeiros espaços são os fragmentos do mockup; os demais pertencem a partes futuras da história.
        self.slots = list(FRAGMENTS) + [None] * (TOTAL_FRAGMENTS - len(FRAGMENTS))
        unlocked = [i for i, f in enumerate(self.slots) if f is not None and f.id in self.memories]
        self.selected = unlocked[0] if unlocked else 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_f, pygame.K_RETURN):
                return "back"
            moves = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1, pygame.K_UP: -4, pygame.K_DOWN: 4}
            if event.key in moves:
                self.selected = (self.selected + moves[event.key]) % TOTAL_FRAGMENTS
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.BACK.collidepoint(event.pos):
                return "back"
            for index, rect in enumerate(self.CARD_RECTS):
                if rect.collidepoint(event.pos):
                    self.selected = index
        return None

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(background(110), (0, 0))
        panel(surface, self.TITLE, 225)
        label(surface, "FRAGMENTOS DE MEMÓRIA", (self.TITLE.centerx, self.TITLE.y + 12), 36, GOLD_BRIGHT,
              align="center")
        label(surface, "Algumas memórias nunca morrem. Elas apenas esperam para serem lembradas.",
              (self.TITLE.centerx, self.TITLE.y + 56), 15, TEXT, italic=True, align="center")
        fragment_counter(surface, pygame.Rect(1047, 52, 206, 46), len(self.memories), TOTAL_FRAGMENTS)
        panel(surface, self.GRID, 215)
        for index, (fragment, rect) in enumerate(zip(self.slots, self.CARD_RECTS)):
            self._draw_card(surface, index, fragment, rect)
        self._draw_detail(surface)
        credits_footer(surface, [("fragments/a_batalha.png", "Ícones e arte dos fragmentos —\nChatGPT, geração de imagens"),
                                 ("portraits/darian.png", "Texto descritivo —\nChatGPT (LLM)")])

    def _draw_card(self, surface, index, fragment, rect):
        pygame.draw.rect(surface, (12, 12, 15), rect)
        art = rect.inflate(-8, -8)
        art.height -= 26
        unlocked = fragment is not None and fragment.id in self.memories
        if fragment is None:
            image = cover(LOCKED_ART[index - len(FRAGMENTS)], art.size)
        else:
            image = cover(f"fragments/{fragment.id}.png", art.size)
            image = image if unlocked else darken(image, 0.22)
        surface.blit(image, art)
        if fragment is not None and not unlocked:
            lock(surface, (art.centerx, art.centery + 6))
        caption = fragment.titulo if unlocked else "BLOQUEADO"
        label(surface, caption, (rect.centerx, rect.bottom - 26), 15 if unlocked else 13,
              TEXT if unlocked else MUTED, align="center")
        selected = index == self.selected
        pygame.draw.rect(surface, GOLD_BRIGHT if selected else (66, 58, 44), rect, 3 if selected else 1)

    def _draw_detail(self, surface):
        area = self.DETAIL
        panel(surface, area, 232)
        fragment = self.slots[self.selected]
        memory = self.memories.get(fragment.id) if fragment is not None else None
        image_rect = pygame.Rect(area.x + 22, area.y + 52, area.width - 44, 176)
        if fragment is not None:
            name = "fragments/a_batalha_grande.png" if fragment.id == "a_batalha" else f"fragments/{fragment.id}.png"
        else:
            name = LOCKED_ART[self.selected - len(FRAGMENTS)]
        image = cover(name, image_rect.size)
        surface.blit(image if memory or fragment is None else darken(image, 0.25), image_rect)
        pygame.draw.rect(surface, (120, 98, 60), image_rect, 1)
        text = pygame.Rect(area.x + 26, image_rect.bottom + 12, area.width - 52, 96)
        if memory is None:
            label(surface, "Bloqueado", (area.centerx, area.y + 12), 28, MUTED, align="center")
            if fragment is not None:
                lock(surface, image_rect.center)
            hint = (f"Dica: {fragment.dica}" if fragment is not None
                    else "Este fragmento pertence a uma parte da história ainda não implementada no MVP.")
            paragraph(surface, hint, text, 16, MUTED, italic=True)
        else:
            label(surface, fragment.titulo, (area.centerx, area.y + 10), 30, GOLD_BRIGHT, align="center")
            paragraph(surface, f"“{memory.text}”", text, 17, TEXT, italic=True)
            divider(surface, area.x + 26, area.right - 26, text.bottom + 8)
            paragraph(surface, fragment.descricao, pygame.Rect(text.x, text.bottom + 16, text.width, 40), 14, TEXT)
            source = "Texto: ChatGPT (LLM)" if memory.generated else "Texto: roteiro (sem IA)"
            label(surface, source, (area.centerx, text.bottom + 58), 12, GOLD if memory.generated else MUTED,
                  italic=True, align="center")
        button(surface, self.BACK, "Voltar", caps=True, selected=True, size=18)
