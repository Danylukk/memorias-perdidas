import pygame

from game.screens.ui import GOLD, MUTED, RED, background, button, fragment_art, fragment_card, label, panel, paragraph
from game.systems.fragments import FRAGMENTS, TOTAL_FRAGMENTS


class FragmentsScreen:
    BACK = pygame.Rect(800, 700, 320, 56)
    CARD_RECTS = tuple(pygame.Rect(60 + (i % 4) * 170, 150 + (i // 4) * 185, 155, 170) for i in range(TOTAL_FRAGMENTS))

    def __init__(self, memories):
        self.memories = dict(memories)
        # Slots além dos fragmentos do MVP permanecem bloqueados, como no mockup (x/12).
        self.slots = list(FRAGMENTS) + [None] * (TOTAL_FRAGMENTS - len(FRAGMENTS))
        unlocked = [i for i, f in enumerate(self.slots) if f is not None and f.id in self.memories]
        self.selected = unlocked[0] if unlocked else 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_f):
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
        surface.blit(background(150), (0, 0))
        label(surface, "FRAGMENTOS DE MEMÓRIA", (60, 36), 32, GOLD, True)
        label(surface, "Algumas memórias nunca morrem. Elas apenas esperam para serem lembradas.", (60, 84), 17, MUTED)
        label(surface, f"Fragmentos: {len(self.memories)}/{TOTAL_FRAGMENTS}", (900, 44), 22, GOLD)
        for index, (fragment, rect) in enumerate(zip(self.slots, self.CARD_RECTS)):
            unlocked = fragment is not None and fragment.id in self.memories
            fragment_card(surface, rect, fragment.titulo if unlocked else "", unlocked, index == self.selected)
        self._draw_detail(surface)
        button(surface, self.BACK, "Voltar  [Esc]")

    def _draw_detail(self, surface):
        area = pygame.Rect(760, 150, 400, 530)
        panel(surface, area)
        fragment = self.slots[self.selected]
        memory = self.memories.get(fragment.id) if fragment is not None else None
        if memory is None:
            label(surface, "BLOQUEADO", (780, 170), 26, MUTED, True)
            hint = (f"Dica: {fragment.dica}" if fragment is not None
                    else "Este fragmento pertence a uma parte da história ainda não implementada no MVP.")
            paragraph(surface, hint, pygame.Rect(780, 220, 360, 200), 18, MUTED)
            return
        label(surface, memory.fragment.titulo, (780, 170), 26, GOLD, True)
        surface.blit(fragment_art((360, 190)), (780, 212))
        paragraph(surface, f"“{memory.text}”", pygame.Rect(780, 420, 360, 200), 18)
        source = ("Texto gerado por ChatGPT (LLM)" if memory.generated
                  else "Reserva roteirizada — IA indisponível")
        label(surface, source, (780, 640), 15, GOLD if memory.generated else RED)
