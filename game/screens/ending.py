import pygame

from game.screens.ui import GOLD, MUTED, asset, background, button, fit_image, label, panel, paragraph
from game.systems.ending import compute_ending
from game.systems.fragments import TOTAL_FRAGMENTS


class EndingScreen:
    FRAGMENTS = pygame.Rect(640, 690, 250, 56)
    MENU = pygame.Rect(910, 690, 250, 56)
    NEW_GAME = pygame.Rect(370, 690, 250, 56)

    def __init__(self, encounter):
        self.state = encounter.state
        self.memories = dict(encounter.memories)
        self.ending = compute_ending(encounter.state, encounter.choice.id if encounter.choice else None)

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
        surface.blit(background(150), (0, 0))
        player, npc = self.state.player, self.state.npc
        fit_image(surface, asset("characters/kael.png"), pygame.Rect(40, 110, 330, 560))
        label(surface, "FIM DA SESSÃO", (400, 60), 20, MUTED)
        label(surface, f"Kael, {self.ending.titulo}", (400, 92), 38, GOLD, True)
        paragraph(surface, self.ending.descricao, pygame.Rect(400, 160, 760, 90), 20)

        panel(surface, pygame.Rect(400, 270, 360, 390))
        label(surface, "QUEM KAEL SE TORNOU", (420, 288), 18, GOLD)
        for index, (name, value) in enumerate([
            ("Empatia", player.empatia), ("Agressividade", player.agressividade),
            ("Curiosidade", player.curiosidade), ("Egoísmo", player.egoismo), ("Lealdade", player.lealdade),
            ("Vida", player.vida), ("Energia", player.energia),
        ]):
            label(surface, f"{name:<15}{value}", (420, 326 + index * 30), 18)

        panel(surface, pygame.Rect(790, 270, 370, 390))
        label(surface, "DARIAN", (810, 288), 18, GOLD)
        label(surface, f"Confiança final: {npc.confianca_em_kael}", (810, 320), 18)
        paragraph(surface, self.ending.destino_darian, pygame.Rect(810, 356, 330, 110), 18)
        label(surface, f"Fragmentos: {len(self.memories)}/{TOTAL_FRAGMENTS}", (810, 490), 18, GOLD)
        titles = ", ".join(m.fragment.titulo for m in self.memories.values()) or "Nenhuma memória recuperada."
        paragraph(surface, titles, pygame.Rect(810, 522, 330, 120), 17, MUTED)

        button(surface, self.NEW_GAME, "Novo Jogo [Enter]")
        button(surface, self.FRAGMENTS, "Fragmentos [F]")
        button(surface, self.MENU, "Menu [Esc]")
        label(surface, "Enquanto Kael descobre quem era, você decidiu quem ele será.", (400, 760), 16, MUTED)
