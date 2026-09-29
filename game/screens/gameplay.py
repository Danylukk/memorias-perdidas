"""Tela 2 — Gameplay (CP4, Figura 5): cena, HUD, NPC, caixa de diálogo e escolhas."""
from dataclasses import asdict
from time import monotonic

import pygame

from game.screens.ui import (ENERGY, GOLD, GOLD_BRIGHT, LIFE, MUTED, NAME_COLORS, RED, TEXT, background, bar,
                             button, credits_footer, diamond, divider, fragment_counter, frame, label, panel,
                             paragraph, portrait, sprite)
from game.systems.ending import DECISIONS
from game.systems.fragments import TOTAL_FRAGMENTS
from game.systems.journey import HOTSPOTS, Journey
from game.systems.script import BRANCH_NAMES

ATTRIBUTES = (("empatia", "Empatia"), ("agressividade", "Agressividade"), ("curiosidade", "Curiosidade"),
              ("egoismo", "Egoísmo"), ("lealdade", "Lealdade"))
NPC_X = {"darian": 780, "lira": 1085}
MARKER_Y = {"estandarte": 128, "espadas": 395, "darian": 262, "lira": 178}
CONVERSATION_X = {"darian": 520, "lira": 965}
HOTSPOT_ACTIONS = {"estandarte": "Investigar o estandarte", "espadas": "Examinar as espadas",
                   "darian": "Ver Darian", "lira": "Falar com Lira"}


class GameplayScreen:
    # Posições do mockup (1672×941) convertidas para 1280×720.
    DIALOGUE = pygame.Rect(205, 452, 867, 116)
    CHOICE_RECTS = tuple(pygame.Rect(216 + i * 215, 580, 202, 42) for i in range(4))
    WIDE = pygame.Rect(430, 580, 418, 42)
    RETRY = pygame.Rect(1090, 470, 170, 36)
    FEET_Y = 452
    SCALE = 0.185
    WALK_SPEED = 320
    REACH = 130

    def __init__(self, dialogue_service, offline=False, journey=None, animate_text=True):
        self.journey = journey or Journey(dialogue_service, offline)
        npc = self.journey.encounter.npc_id if self.journey.encounter else "lira"
        self.kael_x = float(CONVERSATION_X[npc])
        self.facing_left = False
        self.walk_target = None
        self.pending = None
        self.show_profile = False
        self.animate_text = animate_text
        self.feedback: list[tuple[str, tuple, float]] = []
        self.toast: tuple[str, float] | None = None
        self._text_key = None
        self._text_start = 0.0
        self._last = monotonic()

    # --- Leitura de estado ---
    @property
    def encounter(self):
        return self.journey.encounter

    @property
    def failed(self):
        encounter = self.encounter
        return bool(encounter and encounter.result is not None and not encounter.result.ok)

    @property
    def dialogue_text(self):
        journey, encounter = self.journey, self.encounter
        if encounter:
            if encounter.generation_in_progress:
                return f"{encounter.state.npc.nome} está pensando..."
            if encounter.result is not None:
                return encounter.result.text or encounter.choice.fallback
            return encounter.opening_line
        if journey.investigating:
            return "Kael fecha os olhos e tenta se lembrar..."
        return journey.message.text

    def actions(self):
        """Rótulos da linha de escolhas, conforme a fase da jornada."""
        journey, encounter = self.journey, self.encounter
        if encounter:
            if encounter.finished:
                return ["Explorar as ruínas" if journey.phase == "darian" else "Decidir em quem confiar"]
            return [choice.label for choice in encounter.current_choices]
        if journey.phase == "exploracao":
            return [HOTSPOT_ACTIONS[h.id] for h in HOTSPOTS]
        if journey.phase == "decisao":
            return [text for _, text in DECISIONS]
        return ["Ver desfecho"]

    def button_rects(self):
        count = len(self.actions())
        return (self.WIDE,) if count == 1 else self.CHOICE_RECTS[:count]

    # --- Entrada ---
    def handle_event(self, event):
        journey = self.journey
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.show_profile = not self.show_profile
            return None
        if journey.busy:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if event.key == pygame.K_f:
                return "fragments"
            if event.key == pygame.K_SPACE:
                self._text_start = 0.0
            if event.key == pygame.K_r:
                self.retry()
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            if event.key in keys:
                return self.activate(keys.index(event.key))
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                if len(self.actions()) == 1:
                    return self.activate(0)
                nearest = self.nearest_hotspot()
                if journey.phase == "exploracao" and nearest:
                    journey.interact(nearest.id)
                    self._after_phase_change()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.DIALOGUE.collidepoint(event.pos):
                self._text_start = 0.0
            if self.failed and self.RETRY.collidepoint(event.pos):
                self.retry()
                return None
            for index, rect in enumerate(self.button_rects()):
                if rect.collidepoint(event.pos):
                    return self.activate(index)
            if journey.phase == "exploracao" and event.pos[1] < self.DIALOGUE.top:
                target = next((h for h in HOTSPOTS if self.hotspot_rect(h).collidepoint(event.pos)), None)
                self.walk_to(target.x if target else event.pos[0], target.id if target else None)
        return None

    def activate(self, index):
        journey, encounter = self.journey, self.encounter
        if index >= len(self.actions()):
            return None
        if encounter:
            if encounter.finished:
                journey.advance()
                self._after_phase_change()
                return None
            before = self._snapshot()
            if encounter.choose(encounter.current_choices[index].id):
                self._add_feedback(before)
            return None
        if journey.phase == "exploracao":
            hotspot = HOTSPOTS[index]
            self.walk_to(hotspot.x, hotspot.id)
        elif journey.phase == "decisao":
            journey.decide(DECISIONS[index][0])
            journey.persist()
        elif journey.phase == "fim":
            return "ending"
        return None

    def retry(self):
        return bool(self.encounter and self.encounter.retry())

    def walk_to(self, x, hotspot_id=None):
        # Para ao lado de um personagem, não sobre ele.
        offset = 110 if hotspot_id in NPC_X else 0
        self.walk_target = max(60.0, min(1220.0, float(x) - offset))
        self.pending = hotspot_id

    def nearest_hotspot(self):
        nearest = min(HOTSPOTS, key=lambda h: abs(h.x - self.kael_x))
        return nearest if abs(nearest.x - self.kael_x) <= self.REACH else None

    def hotspot_rect(self, hotspot):
        top = MARKER_Y[hotspot.id] - 20
        return pygame.Rect(hotspot.x - 60, top, 120, self.FEET_Y - top)

    # --- Atualização ---
    def update(self):
        now = monotonic()
        dt, self._last = min(0.05, now - self._last), now
        journey = self.journey
        if journey.update():
            journey.persist()
            if journey.new_memories:
                titles = ", ".join(m.fragment.titulo for m in journey.new_memories)
                self.toast = (f"Memória recuperada: {titles}  ·  F para ver", now)
        if journey.phase == "exploracao" and not journey.busy:
            self._walk(dt)

    def _walk(self, dt):
        pressed = pygame.key.get_pressed()
        direction = (pressed[pygame.K_RIGHT] or pressed[pygame.K_d]) - (pressed[pygame.K_LEFT] or pressed[pygame.K_a])
        if direction:
            self.walk_target, self.pending = None, None
        elif self.walk_target is not None:
            distance = self.walk_target - self.kael_x
            if abs(distance) <= max(self.WALK_SPEED * dt, 1):
                self.kael_x, self.walk_target = self.walk_target, None
                if self.pending:
                    pending, self.pending = self.pending, None
                    self.journey.interact(pending)
                    self._after_phase_change()
                return
            direction = 1 if distance > 0 else -1
        if direction:
            self.facing_left = direction < 0
            self.kael_x = max(60.0, min(1220.0, self.kael_x + direction * self.WALK_SPEED * max(dt, 0.016)))

    def _after_phase_change(self):
        if self.journey.phase == "lira":
            self.kael_x, self.facing_left = float(CONVERSATION_X["lira"]), False
        self.journey.persist()

    def _snapshot(self):
        journey = self.journey
        npc_id = journey.encounter.npc_id
        return asdict(journey.current_player), npc_id, journey.trust(npc_id)

    def _add_feedback(self, before):
        """Mostra acima de Kael o que a escolha mudou (o estado é sempre calculado pelo Python)."""
        player_before, npc_id, trust_before = before
        player_after = asdict(self.journey.current_player)
        now = monotonic()
        names = dict(ATTRIBUTES) | {"vida": "Vida", "energia": "Energia"}
        for key, name in names.items():
            delta = player_after[key] - player_before[key]
            if delta:
                self.feedback.append((f"{name} {delta:+d}", (140, 200, 120) if delta > 0 else RED, now))
        trust_delta = self.journey.trust(npc_id) - trust_before
        if trust_delta:
            self.feedback.append((f"Confiança de {npc_id.capitalize()} {trust_delta:+d}",
                                  (140, 200, 120) if trust_delta > 0 else RED, now))

    # --- Desenho ---
    def draw(self, surface):
        journey = self.journey
        surface.blit(background(25), (0, 0))
        self._draw_scene(surface)
        self._draw_hud(surface)
        self._draw_dialogue(surface)
        single = len(self.actions()) == 1
        for text, rect in zip(self.actions(), self.button_rects()):
            button(surface, rect, text, not journey.busy, selected=single)
        if self.failed and not journey.busy:
            button(surface, self.RETRY, "Tentar IA [R]", size=16)
        label(surface, "MEMÓRIAS PERDIDAS", (1176, 584), 16, (190, 168, 120), align="center", shadow=True)
        label(surface, "ALGUMAS MEMÓRIAS", (1176, 606), 12, (170, 162, 146), align="center", shadow=True)
        label(surface, "NUNCA MORREM.", (1176, 621), 12, (170, 162, 146), align="center", shadow=True)
        credits_footer(surface, self._credits(), quote=False)
        self._draw_overlays(surface)

    def _credits(self):
        items = [("portraits/kael.png", "Personagem Kael — ChatGPT,\ngeração de imagens"),
                 ("portraits/darian.png", "Personagem Darian — ChatGPT,\ngeração de imagens")]
        if self.journey.phase != "darian":
            items.append(("portraits/lira.png", "Personagem Lira — ChatGPT,\ngeração de imagens"))
        items.append(("backgrounds/bg_ruinas_principal.png", "Cenário — ChatGPT,\ngeração de imagens"))
        return items

    def _draw_scene(self, surface):
        journey = self.journey
        if journey.phase == "exploracao":
            near = self.nearest_hotspot()
            mouse = pygame.mouse.get_pos() if pygame.mouse.get_focused() else (-1, -1)
            for hotspot in HOTSPOTS:
                active = hotspot is near or self.hotspot_rect(hotspot).collidepoint(mouse)
                done = hotspot.fragmento in journey.memories
                y = MARKER_Y[hotspot.id]
                diamond(surface, (hotspot.x, y), 8 if active else 5,
                        GOLD_BRIGHT if active else (MUTED if done else GOLD))
                if active:
                    label(surface, hotspot.nome, (hotspot.x, y - 32), 16, GOLD_BRIGHT, align="center", shadow=True)
        darian = sprite("darian", self.SCALE)
        surface.blit(darian, darian.get_rect(midbottom=(NPC_X["darian"], self.FEET_Y)))
        if journey.phase != "darian":
            lira = sprite("lira", self.SCALE, flip=True)
            surface.blit(lira, lira.get_rect(midbottom=(NPC_X["lira"], self.FEET_Y)))
        kael = sprite("kael", self.SCALE, flip=self.facing_left)
        surface.blit(kael, kael.get_rect(midbottom=(round(self.kael_x), self.FEET_Y)))

    def _draw_hud(self, surface):
        journey, player = self.journey, self.journey.current_player
        portrait(surface, pygame.Rect(22, 16, 72, 72), "portraits/kael.png")
        bar(surface, pygame.Rect(102, 24, 236, 17), player.vida, LIFE)
        bar(surface, pygame.Rect(102, 48, 180, 11), player.energia, ENERGY)
        fragment_counter(surface, pygame.Rect(1050, 22, 210, 44), len(journey.memories), TOTAL_FRAGMENTS)
        label(surface, self._caption(), (104, 66), 14, (190, 182, 165), italic=True, shadow=True)

    def _caption(self):
        journey, encounter = self.journey, self.encounter
        if encounter:
            turn = min(encounter.round_index + (0 if encounter.generation_in_progress or encounter.finished else 1),
                       encounter.total_turns)
            path = f" · caminho: {BRANCH_NAMES[encounter.branch]}" if encounter.branch else ""
            return f"Ruínas · {encounter.state.npc.nome} — turno {turn}/{encounter.total_turns}{path}"
        return {"exploracao": "Ruínas · exploração", "decisao": "Ruínas · decisão final",
                "fim": "Ruínas · fim da jornada"}.get(journey.phase, "Ruínas")

    def _speaker(self):
        """Nome, retrato, rótulo de origem do texto e cor do rótulo."""
        journey, encounter = self.journey, self.encounter
        if encounter:
            result = encounter.result
            if encounter.generation_in_progress:
                tag, color = ("Roteiro offline", MUTED) if encounter.offline else ("ChatGPT (LLM) gerando...", GOLD)
            elif result is None:
                tag, color = ("Fala inicial — gerada com ChatGPT na CP4" if encounter.npc_id == "darian"
                              else "Fala inicial — roteiro"), GOLD
            elif not result.ok:
                tag, color = "IA indisponível — roteiro offline", RED
            elif result.source == "roteiro":
                tag, color = "Roteiro offline", MUTED
            else:
                tag, color = "Resposta narrativa — ChatGPT (LLM)", GOLD
            return encounter.state.npc.nome, f"portraits/{encounter.npc_id}.png", tag, color
        message = journey.message
        image = "portraits/kael.png"
        if message.heading.startswith("Memória"):
            fragment = next((m.fragment for m in journey.memories.values()
                             if message.heading.endswith(m.fragment.titulo)), None)
            image = f"fragments/{fragment.id}.png" if fragment else image
        tag = {"ia": ("Lembrança — ChatGPT (LLM)", GOLD), "roteiro": ("Lembrança — roteiro offline", MUTED)}
        return (message.heading, image) + tag.get(message.source, ("", MUTED))

    def _draw_dialogue(self, surface):
        journey, encounter = self.journey, self.encounter
        box = self.DIALOGUE
        surface.blit(frame("ui/caixa_dialogo_base.png", box.size), box)
        name, image, tag, tag_color = self._speaker()
        portrait(surface, pygame.Rect(box.x + 28, box.y + 17, 84, 82), image)
        x = box.x + 130
        label(surface, name, (x, box.y + 16), 22, NAME_COLORS.get(name, GOLD_BRIGHT))
        if tag:
            label(surface, tag, (box.right - 40, box.y + 22), 13, tag_color, italic=True, align="right")
        if encounter and encounter.choice:
            # O que Kael acabou de dizer, logo acima da caixa.
            label(surface, f"Kael: “{encounter.choice.label}”", (box.x + 24, box.y - 24), 16, GOLD_BRIGHT,
                  italic=True, shadow=True)
        paragraph(surface, self._typed(self.dialogue_text), pygame.Rect(x, box.y + 46, box.width - 175, 54), 20, TEXT)
        hint = ("←/→ andar · E investigar · 1–4 ir até · F fragmentos · TAB perfil · Esc menu"
                if journey.phase == "exploracao" else "1–4 escolher · F fragmentos · TAB perfil · Esc menu")
        label(surface, hint, (self.WIDE.centerx, 626), 12, (170, 162, 146), align="center", shadow=True)

    def _typed(self, text):
        """Efeito de digitação (desligável em Configurações); clique ou Espaço completa o texto."""
        if not self.animate_text:
            return text
        if text != self._text_key:
            self._text_key, self._text_start = text, monotonic()
        if self._text_start == 0.0:
            return text
        return text[:int((monotonic() - self._text_start) * 55)]

    def _draw_overlays(self, surface):
        now = monotonic()
        self.feedback = [(text, color, t0) for text, color, t0 in self.feedback if now - t0 < 2.8][-4:]
        for index, (text, color, t0) in enumerate(reversed(self.feedback)):
            y = max(96, self.FEET_Y - 290 - index * 22 - (now - t0) * 12)
            label(surface, text, (round(self.kael_x), round(y)), 17, color, bold=True, align="center", shadow=True)
        if self.toast and now - self.toast[1] < 5:
            rect = pygame.Rect(390, 100, 500, 40)
            panel(surface, rect, 230, GOLD_BRIGHT)
            label(surface, self.toast[0], (rect.centerx, rect.y + 10), 17, GOLD_BRIGHT, align="center")
        if self.show_profile:
            self._draw_profile(surface)

    def _draw_profile(self, surface):
        journey, player = self.journey, self.journey.current_player
        rect = pygame.Rect(430, 96, 420, 330)
        panel(surface, rect, 240)
        label(surface, "PERFIL DE KAEL", (rect.centerx, rect.y + 16), 22, GOLD, align="center")
        divider(surface, rect.x + 40, rect.right - 40, rect.y + 50)
        rows = [(name, getattr(player, key)) for key, name in ATTRIBUTES]
        rows += [("Vida", player.vida), ("Energia", player.energia),
                 ("Confiança de Darian", journey.trust("darian")), ("Confiança de Lira", journey.trust("lira"))]
        for index, (name, value) in enumerate(rows):
            y = rect.y + 62 + index * 26
            label(surface, name, (rect.x + 50, y), 18)
            label(surface, str(value), (rect.right - 50, y), 18, GOLD_BRIGHT, align="right")
        label(surface, "TAB para fechar", (rect.centerx, rect.bottom - 26), 13, MUTED, align="center")
