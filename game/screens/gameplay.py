import pygame

from game.screens.ui import GOLD, MUTED, RED, background, button, dialogue_panel, label, panel, paragraph, ruins_scene
from game.systems.choices import CHOICES
from game.systems.encounter import Encounter


class GameplayScreen:
    MENU = pygame.Rect(880, 24, 280, 46)
    RETRY = pygame.Rect(880, 680, 280, 50)
    CHOICE_RECTS = tuple(pygame.Rect(40 + (i % 2) * 410, 584 + (i // 2) * 72, 390, 58) for i in range(4))

    def __init__(self, dialogue_service):
        self.encounter = Encounter(dialogue_service)
        self.scene = ruins_scene()

    def handle_event(self, event):
        encounter = self.encounter
        if encounter.generation_in_progress:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            if event.key in keys:
                encounter.choose(keys.index(event.key) + 1)
            if event.key == pygame.K_r:
                encounter.retry()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.MENU.collidepoint(event.pos):
                return "menu"
            for choice, rect in zip(CHOICES, self.CHOICE_RECTS):
                if rect.collidepoint(event.pos):
                    encounter.choose(choice.id)
            if self.RETRY.collidepoint(event.pos):
                encounter.retry()
        return None

    def update(self):
        self.encounter.update()

    @property
    def dialogue_text(self):
        encounter = self.encounter
        if encounter.generation_in_progress:
            return "Darian está pensando..."
        if encounter.result is not None:
            return encounter.result.text if encounter.result.ok else encounter.result.error
        return "Você... está vivo?"

    def draw(self, surface):
        surface.blit(background(90), (0, 0))
        encounter, player, npc = self.encounter, self.encounter.state.player, self.encounter.state.npc
        label(surface, "MEMÓRIAS PERDIDAS", (40, 24), 27, GOLD, True)
        label(surface, f"Vida {player.vida}/100   Energia {player.energia}/100   Fragmentos {player.fragmentos}/12", (40, 68), 18)
        button(surface, self.MENU, "Voltar ao menu  [Esc]", not encounter.generation_in_progress)
        surface.blit(self.scene, (40, 115))
        label(surface, "RUÍNAS / APÓS A BATALHA", (40, 96), 16)
        label(surface, "KAEL", (268, 372), 16, GOLD)
        label(surface, "DARIAN", (566, 372), 16, GOLD)

        panel(surface, pygame.Rect(880, 115, 280, 544))
        label(surface, "KAEL", (900, 137), 24, GOLD, True)
        for index, (name, value) in enumerate([
            ("Empatia", player.empatia), ("Agressividade", player.agressividade),
            ("Curiosidade", player.curiosidade), ("Egoísmo", player.egoismo), ("Lealdade", player.lealdade),
        ]):
            label(surface, f"{name:<15}{value}", (900, 187 + index * 33), 18)
        pygame.draw.line(surface, MUTED, (900, 368), (1138, 368))
        label(surface, "DARIAN / SOLDADO", (900, 390), 20, GOLD)
        label(surface, "Gravemente ferido", (900, 430), 18)
        label(surface, f"Confiança: {npc.confianca_em_kael}", (900, 466), 20)
        paragraph(surface, "Seu passado permanece oculto. Nenhum fragmento foi desbloqueado.",
                  pygame.Rect(900, 523, 235, 120), 18, MUTED)

        dialogue_panel(surface, pygame.Rect(40, 403, 800, 170))
        failed = encounter.result is not None and not encounter.result.ok
        if failed:
            heading = "FALHA NA GERAÇÃO / nenhuma fala recebida"
        elif encounter.result is not None or encounter.generation_in_progress:
            heading = "DARIAN / Resposta narrativa — ChatGPT (LLM)"
        else:
            heading = "DARIAN / abertura roteirizada"
        label(surface, heading, (58, 430), 17, RED if failed else GOLD)
        paragraph(surface, self.dialogue_text, pygame.Rect(58, 464, 764, 96), 20, RED if failed else (225, 220, 205))
        for choice, rect in zip(CHOICES, self.CHOICE_RECTS):
            button(surface, rect, f"{choice.id}. {choice.label}", encounter.choice is None,
                   encounter.choice == choice)
        if failed:
            button(surface, self.RETRY, "Tentar novamente [R]")
        if encounter.generation_in_progress:
            footer = "Gerando resposta · aguarde. Você pode fechar a janela a qualquer momento."
        elif failed:
            footer = "Efeitos mantidos. Repetir a geração não aplica os atributos novamente."
        elif encounter.result is not None:
            footer = "Fim deste encontro do MVP. Volte ao menu e inicie um Novo Jogo para explorar outra escolha."
        else:
            footer = "Escolha com o mouse ou teclas 1–4. Resposta narrativa — ChatGPT (LLM)."
        label(surface, footer, (40, 754), 16, MUTED)
