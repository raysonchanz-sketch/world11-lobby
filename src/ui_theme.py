"""
ui_theme.py
-----------
Shared visual-polish toolkit used by every menu/HUD screen: gradient
backgrounds, drifting decorative particles, beveled "block" panels with
drop shadows, pulsing glow highlights for selection, confetti bursts, and
fade transitions between screens. Everything here is additive — screens
still own their own layout and sprite choices, this module just gives them
a consistent, nicer-looking toolbox to draw with.
"""

import math
import random
import pygame

BLACK = (10, 10, 16)
WHITE = (255, 250, 240)

# Night-sky menu gradient (matches the existing 30,30,50 vibe but richer)
BG_TOP = (18, 20, 42)
BG_BOTTOM = (48, 40, 82)

_gradient_cache = {}
_vignette_cache = {}


def draw_gradient_bg(surface, top_color=BG_TOP, bottom_color=BG_BOTTOM):
    """Vertical gradient background, cached per (size, colors)."""
    size = surface.get_size()
    key = (size, top_color, bottom_color)
    grad = _gradient_cache.get(key)
    if grad is None:
        w, h = size
        grad = pygame.Surface((1, h))
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            grad.set_at((0, y), (r, g, b))
        grad = pygame.transform.scale(grad, size)
        _gradient_cache[key] = grad
    surface.blit(grad, (0, 0))


def draw_vignette(surface, strength=140):
    """Subtle darkened edges to focus attention toward the center."""
    size = surface.get_size()
    key = (size, strength)
    vg = _vignette_cache.get(key)
    if vg is None:
        w, h = size
        vg = pygame.Surface(size, pygame.SRCALPHA)
        cx, cy = w / 2, h / 2
        max_d = math.hypot(cx, cy)
        step = 4
        for y in range(0, h, step):
            for x in range(0, w, step):
                d = math.hypot(x - cx, y - cy) / max_d
                a = int(max(0, (d - 0.55)) / 0.45 * strength)
                if a > 0:
                    pygame.draw.rect(vg, (0, 0, 0, min(255, a)), (x, y, step, step))
        _vignette_cache[key] = vg
    surface.blit(vg, (0, 0))


def _shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def draw_panel(surface, rect, base_color, border=4, radius=14, shadow=True):
    """Beveled 'block' panel with a soft drop shadow, matching HUD styling."""
    if shadow:
        shadow_rect = rect.move(0, 6)
        shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect(), border_radius=radius)
        surface.blit(shadow_surf, shadow_rect.topleft)

    pygame.draw.rect(surface, BLACK, rect, border_radius=radius)
    inner = rect.inflate(-border * 2, -border * 2)
    pygame.draw.rect(surface, base_color, inner, border_radius=max(2, radius - 3))

    highlight = _shade(base_color, 55)
    dark = _shade(base_color, -65)
    hl_rect = inner.inflate(-6, -6)
    pygame.draw.line(surface, highlight, hl_rect.topleft, hl_rect.topright, 3)
    pygame.draw.line(surface, highlight, hl_rect.topleft, hl_rect.bottomleft, 3)
    pygame.draw.line(surface, dark, hl_rect.bottomleft, hl_rect.bottomright, 3)
    pygame.draw.line(surface, dark, hl_rect.topright, hl_rect.bottomright, 3)


GOLD_BORDER = (255, 210, 60)


def draw_angled_panel(surface, rect, base_color, border_color=GOLD_BORDER,
                       skew=16, border_width=4, shadow=True, highlight=True,
                       selected=False):
    """Beveled parallelogram panel — the shared angled 'Smash' shape."""
    x, y, w, h = rect
    points = [
        (x + skew, y), (x + w, y),
        (x + w - skew, y + h), (x, y + h),
    ]

    if shadow:
        shadow_pts = [(px + 5, py + 6) for px, py in points]
        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(shadow_surf, (0, 0, 0, 90), shadow_pts)
        surface.blit(shadow_surf, (0, 0))

    pygame.draw.polygon(surface, base_color, points)

    if highlight:
        stripe_h = max(4, h // 5)
        stripe_top = y + h // 6
        stripe_pts = [
            (x + skew * 0.6, stripe_top), (x + w - skew * 0.2, stripe_top),
            (x + w - skew * 0.9, stripe_top + stripe_h), (x + skew * 1.3, stripe_top + stripe_h),
        ]
        stripe_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(stripe_surf, (255, 255, 255, 55), stripe_pts)
        surface.blit(stripe_surf, (0, 0))

    border_col = border_color if selected else _shade(border_color, -70)
    pygame.draw.polygon(surface, border_col, points, border_width if selected else max(2, border_width - 2))

    return points


def clip_to_polygon(surface, image, points, rect):
    """Clip `image` to an angled polygon shape and blit onto `surface`."""
    x, y, w, h = rect
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    local_pts = [(px - x, py - y) for px, py in points]
    pygame.draw.polygon(mask, (255, 255, 255, 255), local_pts)
    clipped = pygame.Surface((w, h), pygame.SRCALPHA)
    clipped.blit(image, (0, 0))
    clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(clipped, (x, y))


def draw_glass_panel(surface, rect, radius=18, alpha=140, tint=(20, 20, 40)):
    """Frosted-glass style backing panel, good behind pause/victory menus."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*tint, alpha), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (255, 255, 255, 35), panel.get_rect(), 2, border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_glow(surface, rect, color, strength=1.0, radius=None, layers=5):
    """Soft pulsing glow behind a selected button/card. strength in [0,1]."""
    if strength <= 0:
        return
    radius = radius or (rect.height // 2 + 10)
    glow = pygame.Surface((rect.width + radius * 2, rect.height + radius * 2), pygame.SRCALPHA)
    center = glow.get_rect().center
    for i in range(layers, 0, -1):
        a = int(35 * strength * (i / layers))
        pad = int(radius * (i / layers))
        r = pygame.Rect(0, 0, rect.width + pad * 2, rect.height + pad * 2)
        r.center = center
        pygame.draw.rect(glow, (*color, a), r, border_radius=r.height // 2)
    surface.blit(glow, (rect.centerx - glow.get_width() // 2, rect.centery - glow.get_height() // 2))


def outlined_text(surface, text, font, pos, fg_color, outline_width=3,
                   outline_color=BLACK, center=False):
    """Text with a clean stroked outline (reused across all screens)."""
    base = font.render(text, True, fg_color)
    w, h = base.get_size()
    pad = outline_width
    stamp = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    if outline_width > 0:
        outline_glyph = font.render(text, True, outline_color)
        for dx in (-outline_width, 0, outline_width):
            for dy in (-outline_width, 0, outline_width):
                if dx == 0 and dy == 0:
                    continue
                stamp.blit(outline_glyph, (dx + pad, dy + pad))
    stamp.blit(base, (pad, pad))

    rect = stamp.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(stamp, rect)
    return rect


class ParticleField:
    """Gentle drifting background decoration (coins, stars, blocks...).

    Pass a list of already-loaded surfaces; particles pick randomly from
    them, drift upward with slight horizontal sway, twinkle, and wrap
    around the screen. Purely decorative, safe to skip if sprites=[]."""

    def __init__(self, sprites, count, w, h, speed=(12, 32), area_pad=40):
        self.sprites = [s for s in sprites if s is not None]
        self.w, self.h = w, h
        self.particles = []
        if not self.sprites:
            return
        for _ in range(count):
            self.particles.append({
                "sprite": random.choice(self.sprites),
                "x": random.uniform(-area_pad, w + area_pad),
                "y": random.uniform(-area_pad, h + area_pad),
                "speed": random.uniform(*speed),
                "sway_phase": random.uniform(0, math.tau),
                "sway_amp": random.uniform(6, 18),
                "twinkle_phase": random.uniform(0, math.tau),
            })

    def update(self, dt):
        for p in self.particles:
            p["y"] -= p["speed"] * dt
            p["sway_phase"] += dt * 0.8
            p["twinkle_phase"] += dt * 3.0
            if p["y"] < -50:
                p["y"] = self.h + 50
                p["x"] = random.uniform(-40, self.w + 40)

    def draw(self, surface):
        for p in self.particles:
            sprite = p["sprite"]
            x = p["x"] + math.sin(p["sway_phase"]) * p["sway_amp"]
            alpha = int(140 + 100 * ((math.sin(p["twinkle_phase"]) + 1) / 2))
            img = sprite.copy()
            img.set_alpha(alpha)
            surface.blit(img, (x, p["y"]))


class ConfettiBurst:
    """Colorful falling confetti rectangles for victory celebrations."""

    def __init__(self, w, h, count=90, colors=None):
        self.w, self.h = w, h
        self.colors = colors or [
            (255, 90, 90), (255, 210, 60), (90, 200, 255),
            (120, 230, 120), (230, 120, 230),
        ]
        self.particles = []
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(0, w),
                "y": random.uniform(-h, 0),
                "vy": random.uniform(60, 160),
                "vx": random.uniform(-25, 25),
                "size": random.uniform(4, 9),
                "color": random.choice(self.colors),
                "rot": random.uniform(0, 360),
                "spin": random.uniform(-180, 180),
            })

    def update(self, dt):
        for p in self.particles:
            p["y"] += p["vy"] * dt
            p["x"] += p["vx"] * dt
            p["rot"] += p["spin"] * dt
            if p["y"] > self.h + 20:
                p["y"] = random.uniform(-40, -10)
                p["x"] = random.uniform(0, self.w)

    def draw(self, surface):
        for p in self.particles:
            s = p["size"]
            piece = pygame.Surface((s, s * 2), pygame.SRCALPHA)
            piece.fill(p["color"])
            rotated = pygame.transform.rotate(piece, p["rot"])
            surface.blit(rotated, (p["x"], p["y"]))


def fade(screen, clock, mode="out", duration=0.28, color=(8, 8, 14)):
    """Blocking fade to (mode='out') or from (mode='in') a solid color.

    Call fade(screen, clock, 'out') right before leaving a screen, and
    fade(screen, clock, 'in') right after a screen is entered, to smooth
    over the cut between menus.
    """
    snapshot = screen.copy()
    steps = max(1, int(duration * 60))
    overlay = pygame.Surface(screen.get_size())
    overlay.fill(color)
    for i in range(steps + 1):
        t = i / steps
        alpha = int(255 * t) if mode == "out" else int(255 * (1 - t))
        screen.blit(snapshot, (0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def ease_out(t):
    return 1 - (1 - t) ** 3
