from functools import lru_cache
from pathlib import Path

import pygame

SIZE = (1200, 800)
BG = (14, 18, 23)
PANEL = (23, 29, 35)
LINE = (63, 69, 71)
TEXT = (225, 220, 205)
MUTED = (151, 158, 156)
GOLD = (194, 163, 102)
RED = (196, 115, 108)
ASSETS = Path(__file__).resolve().parents[2] / "assets"


@lru_cache(maxsize=8)
def asset(name):
    return pygame.image.load(ASSETS / name).convert_alpha()


def fit_image(surface, image, rect):
    """Contém a imagem inteira, com escala uniforme e sem deformar personagens."""
    factor = min(rect.width / image.get_width(), rect.height / image.get_height())
    size = (max(1, round(image.get_width() * factor)), max(1, round(image.get_height() * factor)))
    fitted = pygame.transform.smoothscale(image, size)
    surface.blit(fitted, fitted.get_rect(center=rect.center))


@lru_cache(maxsize=2)
def background(shade=90):
    surface = pygame.Surface(SIZE)
    surface.fill(BG)
    fit_image(surface, asset("backgrounds/bg_ruinas_principal.png"), surface.get_rect())
    overlay = pygame.Surface(SIZE, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, shade))
    surface.blit(overlay, (0, 0))
    return surface


@lru_cache(maxsize=16)
def frame(name, size):
    """Adapta a largura pelas faixas de textura, preservando cantos e ornamento central."""
    source = asset(name)
    # Os PNGs têm margens transparentes com ruído de alpha <= 15.
    # A margem extra conserva a suavização das bordas; os originais não são editados.
    bounds = source.get_bounding_rect(min_alpha=16).inflate(16, 16).clip(source.get_rect())
    source = source.subsurface(bounds)
    width, height = size
    factor = min(height / source.get_height(), width / (source.get_width() * 0.3))
    scaled = pygame.transform.smoothscale(source, (round(source.get_width() * factor), round(source.get_height() * factor)))
    sw, sh = scaled.get_size()
    cap = max(1, round(sw * 0.1))
    middle = max(1, round(sw * 0.1))
    center_x = (sw - middle) // 2
    left_fill = (width - 2 * cap - middle) // 2
    right_fill = width - 2 * cap - middle - left_fill
    source_parts = [(0, cap), (cap, center_x - cap), (center_x, middle),
                    (center_x + middle, sw - cap - center_x - middle), (sw - cap, cap)]
    target_widths = (cap, left_fill, middle, right_fill, cap)
    result = pygame.Surface(size, pygame.SRCALPHA)
    x = 0
    for (sx, source_width), target_width in zip(source_parts, target_widths):
        strip = scaled.subsurface((sx, 0, source_width, sh))
        result.blit(pygame.transform.smoothscale(strip, (target_width, sh)), (x, (height - sh) // 2))
        x += target_width
    return result


def dialogue_panel(surface, rect):
    surface.blit(frame("ui/caixa_dialogo_base.png", rect.size), rect)


@lru_cache(maxsize=16)
def font(size=20, bold=False):
    return pygame.font.SysFont("consolas,dejavusansmono", size, bold=bold)


def label(surface, text, position, size=20, color=TEXT, bold=False):
    surface.blit(font(size, bold).render(text, True, color), position)


def panel(surface, rect):
    pygame.draw.rect(surface, PANEL, rect)
    pygame.draw.rect(surface, LINE, rect, 1)


def paragraph(surface, text, rect, size=20, color=TEXT):
    """Quebra também palavras longas; respeita a caixa sem desenhar sobre controles."""
    current_font = font(size)
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current_font.size(candidate)[0] <= rect.width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = ""
        for char in word:
            if current_font.size(current + char)[0] > rect.width:
                lines.append(current)
                current = ""
            current += char
    if current:
        lines.append(current)
    if len(lines) * (size + 6) > rect.height and size > 14:
        return paragraph(surface, text, rect, size - 1, color)
    previous_clip = surface.get_clip()
    surface.set_clip(rect)
    for index, line in enumerate(lines):
        label(surface, line, (rect.x, rect.y + index * (size + 6)), size, color)
    surface.set_clip(previous_clip)


def button(surface, rect, text, enabled=True, selected=False):
    surface.blit(frame("ui/botao_menu_base.png", rect.size), rect)
    if not enabled and not selected:
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 130))
        surface.blit(shade, rect)
    if selected:
        pygame.draw.rect(surface, GOLD, rect.inflate(-4, -4), 1)
    label(surface, text, (rect.x + 16, rect.y + (rect.height - 22) // 2), 20,
          TEXT if enabled or selected else MUTED)


def ruins_scene():
    """Composição com imagens inteiras; as faixas laterais preservam a proporção do cenário."""
    scene = pygame.Surface((800, 280), pygame.SRCALPHA)
    scene.fill((*BG, 230))
    fit_image(scene, asset("backgrounds/bg_ruinas_principal.png"), scene.get_rect())
    fit_image(scene, asset("characters/kael.png"), pygame.Rect(125, 2, 245, 250))
    fit_image(scene, asset("characters/darian.png"), pygame.Rect(420, 30, 245, 250))
    return scene
