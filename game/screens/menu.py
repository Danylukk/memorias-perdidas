import pygame

from game.screens.ui import GOLD, MUTED, asset, background, button, fit_image, label, paragraph


class MenuScreen:
    NEW_GAME = pygame.Rect(760, 310, 340, 64)
    FRAGMENTS = pygame.Rect(760, 390, 340, 64)
    EXIT = pygame.Rect(760, 470, 340, 64)

    def __init__(self, mode=""):
        self.mode = mode

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "new_game"
            if event.key == pygame.K_ESCAPE:
                return "quit"
            if event.key == pygame.K_f:
                return "fragments"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.NEW_GAME.collidepoint(event.pos):
                return "new_game"
            if self.FRAGMENTS.collidepoint(event.pos):
                return "fragments"
            if self.EXIT.collidepoint(event.pos):
                return "quit"
        return None

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(background(90), (0, 0))
        label(surface, "FIAP / RPG NARRATIVO", (72, 75), 18, GOLD)
        pygame.draw.line(surface, GOLD, (72, 122), (1128, 122))
        fit_image(surface, asset("characters/kael.png"), pygame.Rect(120, 135, 500, 540))
        fit_image(surface, asset("ui/logo_memorias_perdidas.png"), pygame.Rect(700, 135, 455, 155))
        paragraph(surface,
                  "Enquanto Kael descobre quem ele era no passado, você decide quem ele será no presente.",
                  pygame.Rect(72, 695, 570, 74), 17, MUTED)
        button(surface, self.NEW_GAME, "Novo Jogo")
        button(surface, self.FRAGMENTS, "Fragmentos")
        button(surface, self.EXIT, "Sair")
        label(surface, "Enter para começar · F para Fragmentos", (760, 556), 17, MUTED)
        label(surface, "MVP acadêmico · Kael × Darian", (760, 718), 17, MUTED)
        if self.mode:
            label(surface, self.mode, (760, 590), 17, GOLD)
