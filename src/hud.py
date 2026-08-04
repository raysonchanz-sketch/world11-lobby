import math
import pygame
from src.ui_theme import draw_panel as _draw_block_panel, outlined_text as _draw_outlined_text, draw_glow, _shade

"""
Mario-style battle HUD — drawn entirely with pygame primitives, no image
assets required. Chunky black outlines, beveled "block" panels with drop
shadows, and a color-graded percentage readout (green -> yellow -> orange ->
red) like the classic Smash HUD, but reskinned with Mario-palette blocks and
mushroom stock icons instead of hearts. Panel/text drawing is shared with
every other menu screen via src.ui_theme for a consistent look.
"""

BLACK = (16, 16, 20)
WHITE = (255, 250, 240)
BRICK = (198, 100, 44)
BRICK_DARK = (150, 70, 28)
GOLD = (255, 196, 20)
GOLD_DARK = (196, 140, 10)
SKY = (92, 148, 252)
DANGER = (230, 46, 46)


def _damage_color(pct):
    if pct < 50:
        return (86, 204, 92)
    elif pct < 100:
        return (255, 214, 51)
    elif pct < 150:
        return (255, 140, 32)
    else:
        return (230, 46, 46)


def _draw_mushroom(surface, cx, cy, size, cap_color):
    cap_r = size // 2
    cap_rect = pygame.Rect(cx - cap_r, cy - cap_r, cap_r * 2, cap_r)
    pygame.draw.ellipse(surface, BLACK, cap_rect.inflate(4, 4))
    pygame.draw.ellipse(surface, cap_color, cap_rect)

    spot_r = max(2, size // 8)
    for ox, oy in ((-cap_r * 0.45, -cap_r * 0.15), (cap_r * 0.45, -cap_r * 0.15), (0, -cap_r * 0.6)):
        pygame.draw.circle(surface, WHITE, (int(cx + ox), int(cy + oy)), spot_r)
        pygame.draw.circle(surface, BLACK, (int(cx + ox), int(cy + oy)), spot_r, 1)

    stem_w = int(size * 0.55)
    stem_h = int(size * 0.4)
    stem_rect = pygame.Rect(cx - stem_w // 2, cy, stem_w, stem_h)
    pygame.draw.rect(surface, BLACK, stem_rect.inflate(3, 3), border_radius=3)
    pygame.draw.rect(surface, (250, 235, 205), stem_rect, border_radius=3)


class MarioHUD:
    def __init__(self):
        pygame.font.init()
        self._name_font = pygame.font.SysFont("arialblack,arial", 18, bold=True)
        self._pct_font = pygame.font.SysFont("arialblack,arial", 40, bold=True)
        self._pct_font_small = pygame.font.SysFont("arialblack,arial", 30, bold=True)
        self._timer_font = pygame.font.SysFont("arialblack,arial", 30, bold=True)

        self._prev_pct = {}
        self._pop_timer = {}

        # Load mushroom sprites
        self._mushroom_normal = None
        self._mushroom_empty = None
        try:
            from src.ui_sprites import _load
            m_normal = _load("mushroom_icon_normal.png", 1)
            m_yellow = _load("yellow_mushroom_icon.png", 1)
            if m_normal:
                self._mushroom_normal = pygame.transform.smoothscale(m_normal, (20, 20))
            if m_yellow:
                self._mushroom_empty = pygame.transform.smoothscale(m_yellow, (20, 20))
        except Exception:
            pass

    def _update_pop(self, idx, percentage):
        prev = self._prev_pct.get(idx, percentage)
        if percentage > prev:
            self._pop_timer[idx] = 12
        self._prev_pct[idx] = percentage

        timer = self._pop_timer.get(idx, 0)
        if timer > 0:
            self._pop_timer[idx] = timer - 1
            progress = timer / 12.0
            return 1.0 + 0.35 * progress
        return 1.0

    def _draw_player_panel(self, surface, idx, info, rect):
        color = info.get("color", (200, 200, 200))
        name = info.get("name", f"P{idx + 1}")
        percentage = info.get("percentage", 0)
        stocks = info.get("stocks", 3)
        max_stocks = info.get("max_stocks", stocks)
        shield_pct = info.get("shield_pct")
        combo = info.get("combo")
        input_type = info.get("input_type", "")

        if percentage >= 150:
            pulse = (math.sin(pygame.time.get_ticks() / 140.0) + 1) / 2
            draw_glow(surface, rect, DANGER, strength=0.5 + 0.5 * pulse, radius=14)

        _draw_block_panel(surface, rect, _shade(color, -110), border=4, radius=12)

        tab_w, tab_h = 92, 26
        tab_rect = pygame.Rect(rect.x + 10, rect.y - tab_h // 2, tab_w, tab_h)
        _draw_block_panel(surface, tab_rect, color, border=3, radius=8)
        _draw_outlined_text(surface, name, self._name_font,
                             tab_rect.center, WHITE, outline_width=2, center=True)

        if input_type:
            inp_font = pygame.font.SysFont("arial", 12, bold=True)
            inp_label = "GAMEPAD" if "controller" in input_type.lower() or "gamepad" in input_type.lower() else "KEYBOARD"
            inp_color = (180, 230, 255) if inp_label == "KEYBOARD" else (255, 200, 100)
            inp_surf = inp_font.render(inp_label, True, inp_color)
            inp_rect = inp_surf.get_rect(midtop=(rect.centerx, rect.bottom - 8))
            pygame.draw.rect(surface, (0, 0, 0, 180), inp_rect.inflate(6, 4), border_radius=3)
            surface.blit(inp_surf, inp_rect)

        pct_color = _damage_color(percentage)
        scale = self._update_pop(idx, percentage)
        pct_text = f"{int(percentage)}%"
        font = self._pct_font
        base_surf = font.render(pct_text, True, pct_color)
        if scale != 1.0:
            w, h = base_surf.get_size()
            base_surf = pygame.transform.smoothscale(base_surf, (int(w * scale), int(h * scale)))

        pct_center = (rect.centerx, rect.centery + 6)
        stamp = pygame.Surface((base_surf.get_width() + 12, base_surf.get_height() + 12), pygame.SRCALPHA)
        outline_glyph = font.render(pct_text, True, BLACK)
        if scale != 1.0:
            ow, oh = outline_glyph.get_size()
            outline_glyph = pygame.transform.smoothscale(outline_glyph, (int(ow * scale), int(oh * scale)))
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                if dx == 0 and dy == 0:
                    continue
                stamp.blit(outline_glyph, (dx + 6, dy + 6))
        stamp.blit(base_surf, (6, 6))
        stamp_rect = stamp.get_rect(center=pct_center)
        surface.blit(stamp, stamp_rect)

        icon_size = 20
        gap = 6
        total_w = max_stocks * icon_size + max(0, max_stocks - 1) * gap
        start_x = rect.centerx - total_w // 2 + icon_size // 2
        icon_y = rect.bottom - 16
        for i in range(max_stocks):
            alive = i < stocks
            icon_x = start_x + i * (icon_size + gap)
            if self._mushroom_normal:
                icon = self._mushroom_normal if alive else self._mushroom_empty
                if icon is None:
                    icon = self._mushroom_normal
                if not alive:
                    dim = icon.copy()
                    dim.set_alpha(70)
                    surface.blit(dim, (icon_x - 10, icon_y - 10))
                else:
                    surface.blit(icon, (icon_x - 10, icon_y - 10))
            else:
                icon_color = color if alive else _shade(color, -140)
                _draw_mushroom(surface, icon_x, icon_y, icon_size, icon_color)

        # --- Shield health bar ---
        if shield_pct is not None and (shield_pct < 0.999 or info.get("shielding")):
            bar_w, bar_h = rect.width - 24, 6
            bar_rect = pygame.Rect(rect.x + 12, rect.y + 34, bar_w, bar_h)
            pygame.draw.rect(surface, BLACK, bar_rect.inflate(3, 3), border_radius=3)
            pygame.draw.rect(surface, _shade(color, -90), bar_rect, border_radius=3)
            fill_w = max(0, int(bar_w * max(0.0, min(1.0, shield_pct))))
            if fill_w > 0:
                fill_color = SKY if shield_pct > 0.35 else DANGER
                pygame.draw.rect(surface, fill_color, (bar_rect.x, bar_rect.y, fill_w, bar_h), border_radius=3)

        # --- Combo counter popup ---
        if combo and combo.get("count", 0) > 1:
            hot = combo.get("hot", False)
            combo_color = (255, 255, 100) if hot else (225, 225, 230)
            combo_text = f"{combo['count']} HITS  {combo.get('damage', 0):.0f}%"
            combo_surf = self._name_font.render(combo_text, True, combo_color)
            combo_pos = combo_surf.get_rect(midbottom=(rect.centerx, rect.y - 14))
            outlined_bg = pygame.Surface((combo_surf.get_width() + 8, combo_surf.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(outlined_bg, (0, 0, 0, 140), outlined_bg.get_rect(), border_radius=6)
            surface.blit(outlined_bg, outlined_bg.get_rect(center=combo_pos.center))
            surface.blit(combo_surf, combo_pos)

    def _draw_timer(self, surface, screen_w, time_left):
        minutes = int(time_left) // 60
        seconds = int(time_left) % 60
        text = f"{minutes}:{seconds:02d}"

        panel_w, panel_h = 120, 52
        rect = pygame.Rect(0, 0, panel_w, panel_h)
        rect.midtop = (screen_w // 2, 12)
        if time_left <= 10:
            pulse = (math.sin(pygame.time.get_ticks() / 120.0) + 1) / 2
            draw_glow(surface, rect, DANGER, strength=0.4 + 0.6 * pulse, radius=12)
        _draw_block_panel(surface, rect, GOLD, border=4, radius=10)
        for sx in (rect.left + 14, rect.centerx, rect.right - 14):
            pygame.draw.circle(surface, GOLD_DARK, (sx, rect.top + 10), 4)
            pygame.draw.circle(surface, BLACK, (sx, rect.top + 10), 4, 1)

        _draw_outlined_text(surface, text, self._timer_font, rect.center,
                             BLACK, outline_width=0, center=True)

    def draw(self, surface, players, time_left=None):
        screen_w, screen_h = surface.get_size()

        panel_w, panel_h = 260, 92
        margin_x, margin_y = 24, 20

        if len(players) > 0:
            rect = pygame.Rect(margin_x, screen_h - panel_h - margin_y, panel_w, panel_h)
            self._draw_player_panel(surface, 0, players[0], rect)

        if len(players) > 1:
            rect = pygame.Rect(screen_w - panel_w - margin_x, screen_h - panel_h - margin_y,
                                panel_w, panel_h)
            self._draw_player_panel(surface, 1, players[1], rect)

        if time_left is not None:
            self._draw_timer(surface, screen_w, time_left)
