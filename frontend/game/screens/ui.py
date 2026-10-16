"""Elementos visuais comuns, seguindo os mockups da CP4 (16:9, fantasia sombria, molduras douradas)."""
from functools import lru_cache
from pathlib import Path

import pygame

SIZE = (1280, 720)  # mockups da CP4 em 16:9
BG = (10, 12, 16)
PANEL = (14, 16, 21)
LINE = (63, 69, 71)
TEXT = (228, 220, 200)
MUTED = (150, 146, 136)
GOLD = (201, 168, 106)
GOLD_BRIGHT = (236, 200, 128)
RED = (206, 110, 100)
LIFE = (170, 36, 36)
ENERGY = (58, 110, 190)
NAME_COLORS = {"Darian": (104, 158, 226), "Lira": (126, 186, 120), "Kael": GOLD_BRIGHT}
ASSETS = Path(__file__).resolve().parents[2] / "assets"
FOOTER = pygame.Rect(0, 645, 1280, 75)
SERIF = "palatinolinotype,bookantiqua,palatino,georgia,constantia,cambria,timesnewroman,dejavuserif,serif"


@lru_cache(maxsize=64)
def asset(name):
    return pygame.image.load(ASSETS / name).convert_alpha()


@lru_cache(maxsize=64)
def scaled(name, size):
    return pygame.transform.smoothscale(asset(name), size)


def fit_image(surface, image, rect, flip=False):
    """Contém a imagem inteira, com escala uniforme e sem deformar personagens."""
    factor = min(rect.width / image.get_width(), rect.height / image.get_height())
    size = (max(1, round(image.get_width() * factor)), max(1, round(image.get_height() * factor)))
    fitted = pygame.transform.smoothscale(image, size)
    if flip:
        fitted = pygame.transform.flip(fitted, True, False)
    surface.blit(fitted, fitted.get_rect(center=rect.center))


@lru_cache(maxsize=4)
def background(shade=40):
    surface = pygame.Surface(SIZE)
    surface.fill(BG)
    fit_image(surface, asset("backgrounds/bg_ruinas_principal.png"), surface.get_rect())
    overlay = pygame.Surface(SIZE, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, shade))
    surface.blit(overlay, (0, 0))
    return surface


@lru_cache(maxsize=32)
def sprite(name, scale, flip=False):
    """Sprite oficial recortado nas bordas transparentes e em escala uniforme."""
    image = asset(f"characters/{name}.png")
    image = image.subsurface(image.get_bounding_rect(min_alpha=16))
    image = pygame.transform.smoothscale(image, (round(image.get_width() * scale), round(image.get_height() * scale)))
    return pygame.transform.flip(image, True, False) if flip else image


@lru_cache(maxsize=16)
def frame(name, size):
    """Adapta a largura pelas faixas de textura, preservando cantos e ornamento central."""
    source = asset(name)
    # Os PNGs têm margens transparentes com ruído de alpha <= 15.
    bounds = source.get_bounding_rect(min_alpha=16).inflate(16, 16).clip(source.get_rect())
    source = source.subsurface(bounds)
    width, height = size
    factor = min(height / source.get_height(), width / (source.get_width() * 0.3))
    scaled_source = pygame.transform.smoothscale(
        source, (round(source.get_width() * factor), round(source.get_height() * factor)))
    sw, sh = scaled_source.get_size()
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
        strip = scaled_source.subsurface((sx, 0, source_width, sh))
        result.blit(pygame.transform.smoothscale(strip, (max(0, target_width), sh)), (x, (height - sh) // 2))
        x += target_width
    return result


@lru_cache(maxsize=48)
def font(size=20, bold=False, italic=False):
    return pygame.font.SysFont(SERIF, size, bold=bold, italic=italic)


def label(surface, text, position, size=20, color=TEXT, bold=False, italic=False, align="left", shadow=False):
    rendered = font(size, bold, italic).render(text, True, color)
    rect = rendered.get_rect()
    setattr(rect, {"left": "topleft", "center": "midtop", "right": "topright"}[align], position)
    if shadow:
        surface.blit(font(size, bold, italic).render(text, True, (0, 0, 0)), rect.move(1, 2))
    surface.blit(rendered, rect)
    return rect


def wrap(text, width, size, bold=False, italic=False):
    current_font = font(size, bold, italic)
    lines, current = [], ""
    words = []
    for word in text.split():
        # Uma palavra longa também deve caber na caixa (inclusive saída válida do LLM).
        chunk = ""
        for char in word:
            if chunk and current_font.size(chunk + char)[0] > width:
                words.append(chunk)
                chunk = ""
            chunk += char
        if chunk:
            words.append(chunk)
    for word in words:
        candidate = f"{current} {word}".strip()
        if current_font.size(candidate)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(surface, text, rect, size=20, color=TEXT, italic=False, align="left", min_size=13):
    """Quebra o texto na largura da caixa e reduz a fonte até caber, sem desenhar fora dela."""
    lines = wrap(text, rect.width, size, italic=italic)
    if len(lines) * (size + 5) > rect.height and size > min_size:
        return paragraph(surface, text, rect, size - 1, color, italic, align, min_size)
    previous_clip = surface.get_clip()
    surface.set_clip(rect)
    for index, line in enumerate(lines):
        x = {"left": rect.x, "center": rect.centerx}[align]
        label(surface, line, (x, rect.y + index * (size + 5)), size, color, italic=italic, align=align)
    surface.set_clip(previous_clip)


def panel(surface, rect, alpha=225, border=GOLD):
    """Painel escuro com moldura dourada e cantos ornamentados, como nos mockups."""
    shade = pygame.Surface(rect.size, pygame.SRCALPHA)
    shade.fill((*PANEL, alpha))
    surface.blit(shade, rect)
    pygame.draw.rect(surface, border, rect, 2)
    pygame.draw.rect(surface, (70, 58, 38), rect.inflate(-8, -8), 1)
    for corner in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
        diamond(surface, corner, 5, border)


def diamond(surface, center, radius, color):
    x, y = center
    pygame.draw.polygon(surface, color, [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)])


def divider(surface, x1, x2, y, color=GOLD):
    pygame.draw.line(surface, (90, 74, 48), (x1, y), (x2, y))
    diamond(surface, ((x1 + x2) // 2, y), 4, color)


def button(surface, rect, text, enabled=True, selected=False, size=19, caps=False, icon=None):
    """Botão com a moldura oficial; texto centralizado, em até duas linhas."""
    surface.blit(frame("ui/botao_menu_base.png", rect.size), rect)
    if selected:
        pygame.draw.rect(surface, GOLD_BRIGHT, rect.inflate(-6, -6), 2, border_radius=3)
    if not enabled:
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        surface.blit(shade, rect)
    text = text.upper() if caps else text
    color = (GOLD_BRIGHT if selected else TEXT) if enabled else MUTED
    inner = rect.width - (60 if icon else 34)
    # Primeiro tenta uma linha reduzindo a fonte; só quebra em duas linhas se ainda não couber.
    while size > 13 and font(size).size(text)[0] > inner:
        size -= 1
    lines = wrap(text, inner, size)
    if len(lines) > 1:
        size = min(size, max(11, (rect.height - 10) // 2))
        lines = wrap(text, inner, size)
    total = len(lines) * (size + 2)
    top = rect.centery - total // 2 - 1
    center_x = rect.centerx + (12 if icon else 0)
    for index, line in enumerate(lines):
        label(surface, line, (center_x, top + index * (size + 2)), size, color, align="center")
    if icon:
        width = font(size).size(lines[0])[0]
        image = scaled(icon, (16, 26))
        surface.blit(image, image.get_rect(midright=(center_x - width // 2 - 10, rect.centery)))


def bar(surface, rect, value, color, maximum=100):
    """Barra do HUD (vida/energia) com moldura dourada."""
    pygame.draw.rect(surface, (20, 16, 14), rect)
    filled = rect.inflate(-4, -4)
    filled.width = round(filled.width * max(0, min(value, maximum)) / maximum)
    pygame.draw.rect(surface, color, filled)
    highlight = filled.copy()
    highlight.height = max(1, filled.height // 3)
    pygame.draw.rect(surface, tuple(min(255, c + 50) for c in color), highlight)
    pygame.draw.rect(surface, GOLD, rect, 1)


@lru_cache(maxsize=64)
def cover(name, size):
    """Preenche `size` sem deformar: escala para cobrir e recorta o centro."""
    image = asset(name)
    factor = max(size[0] / image.get_width(), size[1] / image.get_height())
    resized = pygame.transform.smoothscale(
        image, (max(size[0], round(image.get_width() * factor)), max(size[1], round(image.get_height() * factor))))
    area = pygame.Rect(0, 0, *size)
    area.center = resized.get_rect().center
    return resized.subsurface(area).copy()


def portrait(surface, rect, name, dark=False):
    """Retrato em moldura dourada; `name` é um arquivo em assets/."""
    pygame.draw.rect(surface, (18, 14, 12), rect)
    image = cover(name, rect.inflate(-6, -6).size)
    surface.blit(darken(image) if dark else image, rect.inflate(-6, -6))
    pygame.draw.rect(surface, GOLD, rect, 2)
    pygame.draw.rect(surface, (90, 70, 40), rect.inflate(-4, -4), 1)


def fragment_counter(surface, rect, count, total):
    panel(surface, rect, 215)
    surface.blit(scaled("ui/icone_cristal.png", (18, 28)), (rect.x + 16, rect.centery - 14))
    text = f"Fragmentos: {count}/{total}"
    size = 19
    while size > 11 and font(size).size(text)[0] > rect.width - 58:
        size -= 1
    label(surface, text, (rect.x + 44, rect.centery - font(size).get_height() // 2), size)


def credits_footer(surface, items, quote=True):
    """Faixa inferior dos mockups: identifica os assets e textos gerados por IA."""
    shade = pygame.Surface(FOOTER.size, pygame.SRCALPHA)
    shade.fill((8, 9, 12, 238))
    surface.blit(shade, FOOTER)
    pygame.draw.line(surface, (70, 58, 38), FOOTER.topleft, FOOTER.topright)
    if items:
        label(surface, "Assets gerados por IA:", (22, FOOTER.centery - 9), 15, TEXT)
    start = max(200, 22 + font(15).size("Assets gerados por IA:")[0] + 18)
    end = 1080 if quote else SIZE[0] - 18
    cell_width = (end - start) // max(1, len(items))
    for index, (image, text) in enumerate(items):
        x = start + index * cell_width
        thumb = pygame.Rect(x, FOOTER.y + 12, 50, 50)
        portrait(surface, thumb, image)
        lines = text.split("\n")
        size = 14
        while size > 10 and any(font(size).size(line)[0] > cell_width - 72 for line in lines):
            size -= 1
        line_height = max(font(size, False, False).render(line, True, MUTED).get_height()
                          for line in lines) + 2
        top = FOOTER.centery - len(lines) * line_height // 2
        for row, line in enumerate(lines):
            label(surface, line, (thumb.right + 10, top + row * line_height), size, MUTED)
    if quote:
        label(surface, "“ALGUMAS MEMÓRIAS", (1180, FOOTER.y + 16), 14, MUTED, align="center")
        label(surface, "NUNCA MORREM.”", (1180, FOOTER.y + 34), 14, MUTED, align="center")
        divider(surface, 1120, 1240, FOOTER.y + 58, (110, 92, 60))


FADE_SECONDS = 0.45


def fade_in(surface, started, now):
    """Escurecimento que clareia após uma troca de cena (transição entre telas e fases)."""
    progress = (now - started) / FADE_SECONDS
    if 0 <= progress < 1:
        dim(surface, round(255 * (1 - progress)))


def dim(surface, alpha=150):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    surface.blit(shade, (0, 0))


def darken(image, factor=0.3):
    result = image.copy()
    result.fill((round(255 * factor),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    return result


def lock(surface, center):
    x, y = center
    pygame.draw.arc(surface, (170, 160, 150), pygame.Rect(x - 9, y - 20, 18, 22), 0, 3.1416, 3)
    body = pygame.Rect(x - 13, y - 9, 26, 20)
    pygame.draw.rect(surface, (150, 138, 124), body, border_radius=3)
    pygame.draw.circle(surface, (40, 34, 30), (x, y), 3)
