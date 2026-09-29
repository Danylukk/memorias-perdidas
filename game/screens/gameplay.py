"""Telas Pygame."""
import pygame

from game.screens.ui import GOLD, MUTED, RED, background, bar, button, dialogue_panel, label, panel, paragraph, ruins_scene
from game.systems.choices import TOTAL_TURNS
from game.systems.encounter import Encounter
from game.systems.fragments import TOTAL_FRAGMENTS

class GameplayScreen:
    MENU = pygame.Rect(880, 24, 280, 46)
    FRAGMENTS = pygame.Rect(880, 610, 280, 50)
    RETRY = pygame.Rect(880, 680, 280, 50)
    ENDING = pygame.Rect(40, 600, 800, 64)
    CHOICE_RECTS = tuple(pygame.Rect(40, 580 + i * 44, 800, 40) for i in range(4))

    def __init__(self, dialogue_service):
        self.encounter = Encounter(dialogue_service)
        self.scene = ruins_scene()

    def handle_event(self, event):
        encounter = self.encounter
        if encounter.generation_in_progress:
            return None
        choices = encounter.current_choices
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if event.key == pygame.K_f:
                return "fragments"
            if event.key == pygame.K_RETURN and encounter.finished:
                return "ending"
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            if event.key in keys and keys.index(event.key) < len(choices):
                encounter.choose(choices[keys.index(event.key)].id)
            if event.key == pygame.K_r:
                encounter.retry()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.MENU.collidepoint(event.pos):
                return "menu"
            if self.FRAGMENTS.collidepoint(event.pos):
                return "fragments"
            if encounter.finished and self.ENDING.collidepoint(event.pos):
                return "ending"
            for choice, rect in zip(choices, self.CHOICE_RECTS):
                if rect.collidepoint(event.pos):
                    encounter.choose(choice.id)
            if self.RETRY.collidepoint(event.pos):
                encounter.retry()
        return None

    def update(self):
        self.encounter.update()

    @property
    def failed(self):
        result = self.encounter.result
        return result is not None and not result.ok

    @property
    def dialogue_text(self):
        encounter = self.encounter
        if encounter.generation_in_progress:
            return "Darian está pensando..."
        if encounter.result is not None:
            # Falha da IA: fala de reserva roteirizada, sempre identificada como tal.
            return encounter.result.text if encounter.result.ok else encounter.choice.fallback
        return "Você... está vivo?"

    def draw(self, surface):
        surface.blit(background(90), (0, 0))
        encounter, player, npc = self.encounter, self.encounter.state.player, self.encounter.state.npc
        label(surface, "MEMÓRIAS PERDIDAS", (40, 20), 27, GOLD, True)
        label(surface, "Vida", (40, 62), 16)
        bar(surface, pygame.Rect(90, 64, 150, 14), player.vida, (160, 45, 45))
        label(surface, f"{player.vida}", (248, 62), 16)
        label(surface, "Energia", (300, 62), 16)
        bar(surface, pygame.Rect(376, 64, 150, 14), player.energia, (60, 100, 170))
        label(surface, f"{player.energia}", (534, 62), 16)
        label(surface, f"Fragmentos: {player.fragmentos}/{TOTAL_FRAGMENTS}", (600, 62), 16, GOLD)
        button(surface, self.MENU, "Voltar ao menu  [Esc]", not encounter.generation_in_progress)
        surface.blit(self.scene, (40, 115))
        shown_turn = min(encounter.round_index + (0 if encounter.generation_in_progress or encounter.finished else 1),
                         TOTAL_TURNS) or 1
        label(surface, f"RUÍNAS / TURNO {shown_turn}/{TOTAL_TURNS}", (40, 94), 16)
        label(surface, "KAEL", (268, 372), 16, GOLD)
        label(surface, "DARIAN", (566, 372), 16, GOLD)
        self._draw_side_panel(surface, player, npc)
        self._draw_dialogue(surface)

        choices = encounter.current_choices
        if encounter.finished:
            button(surface, self.ENDING, "Ver desfecho  [Enter]", selected=True)
        elif choices:
            for index, (choice, rect) in enumerate(zip(choices, self.CHOICE_RECTS)):
                button(surface, rect, f"{index + 1}. {choice.label}", size=17)
        button(surface, self.FRAGMENTS, "Fragmentos  [F]", not encounter.generation_in_progress)
        if self.failed and not encounter.generation_in_progress:
            button(surface, self.RETRY, "Tentar IA de novo [R]")
        label(surface, self._footer(), (40, 768), 16, MUTED)

    def _draw_side_panel(self, surface, player, npc):
        panel(surface, pygame.Rect(880, 115, 280, 480))
        label(surface, "KAEL", (900, 130), 24, GOLD, True)
        for index, (name, value) in enumerate([
            ("Empatia", player.empatia), ("Agressividade", player.agressividade),
            ("Curiosidade", player.curiosidade), ("Egoísmo", player.egoismo), ("Lealdade", player.lealdade),
        ]):
            label(surface, f"{name:<15}{value}", (900, 172 + index * 28), 18)
        pygame.draw.line(surface, MUTED, (900, 318), (1138, 318))
        label(surface, "DARIAN / SOLDADO", (900, 330), 20, GOLD)
        label(surface, npc.estado.capitalize(), (900, 362), 18)
        label(surface, f"Confiança: {npc.confianca_em_kael}", (900, 390), 20)
        bar(surface, pygame.Rect(900, 420, 238, 10), npc.confianca_em_kael, GOLD)
        pygame.draw.line(surface, MUTED, (900, 444), (1138, 444))
        new = self.encounter.new_memories
        if new:
            label(surface, "MEMÓRIA RECUPERADA", (900, 456), 18, GOLD)
            titles = ", ".join(m.fragment.titulo for m in new)
            paragraph(surface, f"{titles}. Abra Fragmentos [F] para ler.", pygame.Rect(900, 484, 238, 100), 17)
        else:
            paragraph(surface, "Algumas escolhas despertam fragmentos do passado de Kael.",
                      pygame.Rect(900, 460, 238, 120), 17, MUTED)

    def _draw_dialogue(self, surface):
        encounter = self.encounter
        dialogue_panel(surface, pygame.Rect(40, 403, 800, 170))
        failed = self.failed and not encounter.generation_in_progress
        if failed:
            heading = "DARIAN / fala de reserva (roteirizada) — IA indisponível"
        elif encounter.result is not None or encounter.generation_in_progress:
            heading = "DARIAN / Resposta narrativa — ChatGPT (LLM)"
        else:
            heading = "DARIAN / abertura roteirizada"
        label(surface, heading, (62, 436), 17, RED if failed else GOLD)
        if encounter.choice is not None:
            label(surface, f"Kael: {encounter.choice.label}", (62, 460), 15, MUTED)
        paragraph(surface, self.dialogue_text, pygame.Rect(62, 484, 756, 76), 20, (225, 220, 205))

    def _footer(self):
        encounter = self.encounter
        if encounter.generation_in_progress:
            return "Gerando resposta · aguarde. Você pode fechar a janela a qualquer momento."
        if self.failed:
            return "IA indisponível: fala de reserva exibida. Continue ou tente a IA de novo (efeitos mantidos)."
        if encounter.finished:
            return "A conversa terminou. Veja o desfecho de Kael."
        if encounter.options_generated:
            return "Fala de Darian e opções de Kael geradas por ChatGPT (LLM). Teclas 1–4 ou mouse."
        if encounter.round_index == 0:
            return "Opções iniciais do roteiro. Escolha com o mouse ou teclas 1–4."
        return "Opções de reserva (roteirizadas). Escolha com o mouse ou teclas 1–4."
