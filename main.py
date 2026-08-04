import pygame
import sys
import random
import ctypes
from constants import *
from src.sprite_loader import SpriteLoader, MARIO_FILE_MAP, LUIGI_FILE_MAP, YOSHI_FILE_MAP, DONKEY_KONG_FILE_MAP
from src.player         import Player, CTRL_P1, CTRL_P2
from src.ai             import AIController, DIFFICULTY_CONFIGS
from src.controller     import GamepadInput, handle_controller_events, MenuController, InputModePopup

_menu_ctrl = MenuController()


class MouseAwareKeys:
    def __init__(self, ctrl):
        self._attack_key = ctrl.get("attack")
        self._heavy_key = ctrl.get("attack_alt")
        self._raw = {}
        self._prev_left = False
        self._prev_right = False
        self._attack_fire = False
        self._heavy_fire = False

    def refresh(self, raw_keys, mouse_buttons):
        self._raw = raw_keys
        left = mouse_buttons[0]
        right = mouse_buttons[2]
        self._attack_fire = left and not self._prev_left
        self._heavy_fire = right and not self._prev_right
        self._prev_left = left
        self._prev_right = right

    def __getitem__(self, key):
        if key == self._attack_key and self._attack_fire:
            return True
        if key == self._heavy_key and self._heavy_fire:
            return True
        return self._raw[key]


class InputModeGuard:
    """Blocks keyboard input when in controller mode (and vice versa).
    Shows a popup asking to switch modes when wrong input type is detected.
    Call update() each frame, then use should_process_event() to filter events."""

    GRACE_PERIOD = 1.0

    def __init__(self, mode="controller"):
        self.mode = mode
        self._popup = None
        self._start_time = pygame.time.get_ticks() / 1000.0
        self._prev_axes = {}

    def update(self, event, menu_ctrl=None):
        if self._popup:
            self._popup.handle_event(event, menu_ctrl)
            result = self._popup.update()
            if result is not None:
                if result:
                    self.mode = "keyboard" if self.mode == "controller" else "controller"
                self._popup = None
            return False

        now = pygame.time.get_ticks() / 1000.0
        if now - self._start_time < self.GRACE_PERIOD:
            return True

        if event.type == pygame.KEYDOWN and self.mode == "controller":
            self._popup = InputModePopup("Switch to keyboard mode?")
            return False

        if event.type == pygame.JOYBUTTONDOWN and self.mode == "keyboard":
            self._popup = InputModePopup("Switch to controller mode?")
            return False

        if event.type == pygame.JOYAXISMOTION and self.mode == "keyboard":
            try:
                axis_key = (event.joy, event.axis)
                val = event.value
                prev = self._prev_axes.get(axis_key, 0.0)
                self._prev_axes[axis_key] = val
                if abs(val) > 0.6 and abs(val) - abs(prev) > 0.3:
                    self._popup = InputModePopup("Switch to controller mode?")
                    return False
            except Exception:
                pass

        if event.type == pygame.JOYHATMOTION and self.mode == "keyboard":
            if event.value != (0, 0):
                self._popup = InputModePopup("Switch to controller mode?")
                return False

        return True

    def draw(self, screen, font_title, font_btn):
        if self._popup:
            self._popup.draw(screen, font_title, font_btn)

    @property
    def blocked(self):
        return self._popup is not None


from src.tilemap        import Tilemap
from src.background     import Background, FactoryBackground
from src.camera         import Camera
from src.particles      import ParticleSystem, BlastZoneExplosion
from src.screenshake    import ScreenShake
from src.shell          import KoopaShell
from src.egg            import EggProjectile
from src.hud import MarioHUD
from src.projectile import Fireball, Blastshot, Barrel
from src.enemy import Grrrol, BobOmb, Kamek, MagicProjectile
from src.sprite_loader import load_grrrol_sprites, load_bobomb_sprites, load_kamek_sprites
from src.npcs import Goomba, Koopa, ShyGuy, BuzzyBeetle, BulletBill, BillBlaster, load_goomba_sprites, load_koopa_sprites, load_shyguy_sprites, load_buzzy_beetle_sprites, load_bullet_bill_sprites
from src.ui_theme import (draw_gradient_bg, draw_vignette, draw_panel, draw_glass_panel,
                           draw_glow, outlined_text, fade,
                           ease_out, draw_angled_panel, clip_to_polygon, GOLD_BORDER)

class AIKeyProxy:
    def __init__(self, real_keys, ai_controller, controls):
        self.real_keys = real_keys
        self.ai = ai_controller
        self._key_to_action = {v: k for k, v in controls.items()}

    def __getitem__(self, key_code):
        action = self._key_to_action.get(key_code)
        if action and action in self.ai.held:
            return self.ai.held[action]
        return self.real_keys[key_code]

    def __len__(self):
        return len(self.real_keys)

def get_di_y(keys, ctrl):
    if keys[ctrl["jump"]]:
        return -1
    if keys[ctrl["crouch"]]:
        return 1
    return 0

def is_facing(attacker, victim):
    """Return True if attacker is facing toward the victim."""
    if attacker.facing == 1:
        return victim.rect.centerx >= attacker.rect.centerx
    else:
        return victim.rect.centerx <= attacker.rect.centerx

def check_counter_hit(attacker, victim):
    """Check if victim was counter-hit (hit during attack startup).
    Returns (is_counter, modified_kb_bonus)."""
    if victim.is_counter_hit_vulnerable():
        victim.trigger_counter_hit()
        return True, COUNTER_HIT_KB_MULT
    return False, 1.0

CHAR_COLORS = {
    "mario": (229, 37, 33),
    "luigi": (67, 176, 71),
    "yoshi": (118, 188, 66),
    "donkey_kong": (180, 100, 40),
}

def _draw_button(surface, rect, text, font, selected=False, text_color=(255, 255, 255), glow_strength=None):
    bg = (70, 70, 118) if selected else (40, 40, 60)
    draw_angled_panel(surface, rect, bg, border_color=GOLD_BORDER, skew=12,
                       border_width=3, selected=selected)
    outlined_text(surface, text, font, rect.center, text_color,
                  outline_width=2, outline_color=(10, 10, 16), center=True)


def title_screen(screen, clock):
    import os
    import math

    font_big = pygame.font.Font(None, 76)
    font_hint = pygame.font.Font(None, 26)
    font_credit = pygame.font.Font(None, 18)
    font_mode_big = pygame.font.Font(None, 42)
    pulse_timer = 0.0

    sw, sh = screen.get_size()

    portrait_paths = {
        "mario": os.path.join("mario_assets", "mario_portrait_character_select.png"),
        "luigi": os.path.join("luigi_assets", "Luigi_character_select_portrait.png"),
        "yoshi": os.path.join("Yoshi_assets", "Yoshi_character_select_portrait.png"),
        "donkey_kong": os.path.join("Donkey_Kong_assets", "donkey_kong_porrtrait.png"),
    }
    portraits = {}
    for key, path in portrait_paths.items():
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            portraits[key] = img

    fade(screen, clock, "in")

    from src.controller import get_connected_controllers
    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    while True:
        dt = clock.tick(60) / 1000.0
        pulse_timer += dt

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    settings_state["fullscreen"] = not settings_state["fullscreen"]
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                fade(screen, clock, "out")
                return 'start'

        if not _mode_guard.blocked:
            if _menu_ctrl.confirm or _menu_ctrl.any_button:
                fade(screen, clock, "out")
                return 'start'

        draw_gradient_bg(screen)
        sw = screen.get_width()
        sh = screen.get_height()

        cx = sw // 2
        main_w, main_h = 380, 300
        main_x = cx - main_w // 2
        main_y = (sh - main_h) // 2 - 30

        points = [(main_x + 30, main_y), (main_x + main_w, main_y),
                  (main_x + main_w - 30, main_y + main_h), (main_x, main_y + main_h)]
        portrait = portraits.get("mario")
        if portrait:
            pw, ph = portrait.get_size()
            scale = max((main_w + 20) / pw, (main_h + 20) / ph)
            scaled_portrait = pygame.transform.smoothscale(portrait, (int(pw * scale), int(ph * scale)))
            mask_surf = pygame.Surface((main_w, main_h + 10), pygame.SRCALPHA)
            pygame.draw.polygon(mask_surf, (255, 255, 255, 255), [(p[0] - main_x, p[1] - main_y) for p in points])
            clipped = pygame.Surface((main_w + 20, main_h + 20), pygame.SRCALPHA)
            clipped.blit(scaled_portrait, (-5, -10))
            clipped.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(clipped, (main_x - 5, main_y - 5))
        pygame.draw.polygon(screen, (200, 40, 40), points, 4)
        fill_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.polygon(fill_surf, (200, 40, 40, 180), points)
        screen.blit(fill_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        bounce = math.sin(pulse_timer * 2) * 5
        outlined_text(screen, "WORLD 1-1", font_big, (sw // 2, 65 + int(bounce)),
                      (255, 220, 80), outline_width=4, outline_color=(90, 50, 10), center=True)

        hint_alpha = int(140 + 115 * ((math.sin(pulse_timer * 3) + 1) / 2))
        hint = font_hint.render("Press any key to enter", True, (hint_alpha, hint_alpha, min(255, hint_alpha + 20)))
        screen.blit(hint, hint.get_rect(center=(sw // 2, main_y + main_h + 35)))

        credit = font_credit.render("Sprites by: JumpmanMFFG, Chrispriter, Squishy Rex, Rogultgot, NO Body, BidBood, ChaoticYoshi, DotStudio, VannyArts, Avi, Mageker, Racoon Sam, Yoshiguy", True, (200, 220, 255))
        screen.blit(credit, credit.get_rect(center=(sw // 2, screen.get_height() - 15)))

        _mode_guard.draw(screen, font_big, font_hint)

        pygame.display.flip()


def mode_select(screen, font):
    from src.ui_sprites import load_arrow_key, load_mushroom, load_fire_flower
    from src.controller import get_connected_controllers, handle_controller_events, open_bluetooth_settings
    import math
    import webbrowser

    font_title = pygame.font.Font(None, 42)
    font_btn = pygame.font.Font(None, 30)
    font_diff = pygame.font.Font(None, 22)
    font_small = pygame.font.Font(None, 20)
    font_tiny = pygame.font.Font(None, 18)

    BRICK = (198, 100, 44)
    PIPE_GREEN = (46, 138, 60)
    GOLD = (255, 196, 20)
    OCEAN = (40, 120, 180)
    PURPLE = (120, 80, 160)

    modes = ["FIGHT", "FIGHT CPU", "TUTORIAL", "SETTINGS"]
    mode_colors = [BRICK, PIPE_GREEN, OCEAN, PURPLE]
    difficulties = ["easy", "normal", "hard", "pro", "insane"]
    sel = 0
    diff_sel = 1
    confirmed = False
    input_chosen = False
    input_sel = 0
    input_options = ["LOCAL", "ONLINE"]
    pulse_timer = 0.0
    controller_msg = ""
    controller_msg_timer = 0.0
    show_pair_instructions = False
    pair_instr_timer = 0.0
    show_ds4_prompt = False
    _clock = pygame.time.Clock()

    arrow_l = load_arrow_key("left", 2)
    arrow_r = load_arrow_key("right", 2)
    mushroom_icon_small = load_mushroom(2)
    fire_flower_icon_small = load_fire_flower(2)

    sw, sh = screen.get_size()
    panel_width_current = 500.0

    fade(screen, _clock, "in")

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    while True:
        dt = _clock.tick(60) / 1000.0
        pulse_timer += dt
        if controller_msg_timer > 0:
            controller_msg_timer -= dt
        mouse_clicked = False
        mouse_pos = pygame.mouse.get_pos()

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            ctrl_event = handle_controller_events(event)
            if ctrl_event:
                action, idx, name = ctrl_event
                if action == "connected":
                    controller_msg = "Controller: {}".format(name)
                    controller_msg_timer = 3.0
                elif action == "disconnected":
                    controller_msg = "Controller Disconnected"
                    controller_msg_timer = 3.0

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if not confirmed:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        sel = (sel - 1) % len(modes)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        sel = (sel + 1) % len(modes)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        sel = (sel - 2) % len(modes)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        sel = (sel + 2) % len(modes)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if sel == 1:
                            confirmed = True
                        elif sel == 0:
                            confirmed = True
                        elif sel == 2:
                            fade(screen, _clock, "out")
                            return "tutorial", None
                        elif sel == 3:
                            fade(screen, _clock, "out")
                            return "settings", None
                    elif event.key == pygame.K_ESCAPE:
                        fade(screen, _clock, "out")
                        return None, None
                elif not input_chosen and sel == 0:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        input_sel = (input_sel - 1) % len(input_options)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        input_sel = (input_sel + 1) % len(input_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        input_chosen = True
                        fade(screen, _clock, "out")
                        return ("online" if input_sel == 1 else "pvp"), None
                    elif event.key == pygame.K_ESCAPE:
                        confirmed = False
                else:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        diff_sel = (diff_sel - 1) % len(difficulties)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        diff_sel = (diff_sel + 1) % len(difficulties)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        fade(screen, _clock, "out")
                        return "ai", difficulties[diff_sel]
                    elif event.key == pygame.K_ESCAPE:
                        confirmed = False

        if _menu_ctrl.connected and not _mode_guard.blocked:
            if not confirmed:
                if _menu_ctrl.left:
                    sel = (sel - 1) % len(modes)
                elif _menu_ctrl.right:
                    sel = (sel + 1) % len(modes)
                elif _menu_ctrl.up:
                    sel = (sel - 2) % len(modes)
                elif _menu_ctrl.down:
                    sel = (sel + 2) % len(modes)
                elif _menu_ctrl.confirm:
                    if sel == 1:
                        confirmed = True
                    elif sel == 0:
                        confirmed = True
                    elif sel == 2:
                        fade(screen, _clock, "out")
                        return "tutorial", None
                    elif sel == 3:
                        fade(screen, _clock, "out")
                        return "settings", None
                elif _menu_ctrl.cancel:
                    fade(screen, _clock, "out")
                    return None, None
            elif not input_chosen and sel == 0:
                if _menu_ctrl.left:
                    input_sel = (input_sel - 1) % len(input_options)
                elif _menu_ctrl.right:
                    input_sel = (input_sel + 1) % len(input_options)
                elif _menu_ctrl.confirm:
                    input_chosen = True
                    fade(screen, _clock, "out")
                    return ("online" if input_sel == 1 else "pvp"), None
                elif _menu_ctrl.cancel:
                    confirmed = False
            else:
                if _menu_ctrl.left:
                    diff_sel = (diff_sel - 1) % len(difficulties)
                elif _menu_ctrl.right:
                    diff_sel = (diff_sel + 1) % len(difficulties)
                elif _menu_ctrl.confirm:
                    fade(screen, _clock, "out")
                    return "ai", difficulties[diff_sel]
                elif _menu_ctrl.cancel:
                    confirmed = False

        draw_gradient_bg(screen)
        sw = screen.get_width()

        panel_target = 640 if (confirmed) else 500
        panel_width_current += (panel_target - panel_width_current) * min(1.0, dt * 10.0)
        panel_rect = pygame.Rect(0, 0, int(panel_width_current), 480)
        panel_rect.center = (sw // 2, 310)
        draw_glass_panel(screen, panel_rect, radius=22)

        outlined_text(screen, "SELECT MODE", font_title, (sw // 2, 85), (255, 220, 80),
                      outline_width=3, outline_color=(70, 40, 5), center=True)

        btn_w, btn_h = 220, 65
        gap = 12
        total_w = 2 * btn_w + gap
        start_x = sw // 2 - total_w // 2
        top_y = 150

        for i, mode in enumerate(modes):
            col = i % 2
            row = i // 2
            bx = start_x + col * (btn_w + gap)
            by = top_y + row * (btn_h + gap)
            is_sel = (i == sel)
            btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
            draw_angled_panel(screen, btn_rect, mode_colors[i], border_color=GOLD,
                               skew=14, border_width=3, selected=is_sel)
            outlined_text(screen, mode, font_btn, btn_rect.center, (255, 255, 255),
                          outline_width=2, outline_color=(20, 10, 5), center=True)

        if confirmed and sel == 1:
            diff_y = top_y + 2 * (btn_h + gap) + 20
            diff_label = font_btn.render("DIFFICULTY", True, (230, 220, 200))
            screen.blit(diff_label, diff_label.get_rect(center=(sw // 2, diff_y)))

            if arrow_l:
                screen.blit(arrow_l, (sw // 2 - 240, diff_y + 30))
            if arrow_r:
                screen.blit(arrow_r, (sw // 2 + 210, diff_y + 30))

            chip_w, chip_h = 84, 40
            for i, d in enumerate(difficulties):
                bx = sw // 2 - 200 + i * 100
                by = diff_y + 30
                is_sel = (i == diff_sel)
                chip_rect = pygame.Rect(bx, by, chip_w, chip_h)
                chip_rect.centerx = bx + 40
                draw_angled_panel(screen, chip_rect, GOLD if is_sel else (70, 62, 78),
                                   border_color=GOLD, skew=8, border_width=3, selected=is_sel)
                outlined_text(screen, d.upper(), font_diff, chip_rect.center,
                              (40, 25, 5) if is_sel else (220, 218, 228),
                              outline_width=1, outline_color=(0, 0, 0), center=True)

        if confirmed and sel == 0 and not input_chosen:
            diff_y = top_y + 2 * (btn_h + gap) + 20
            diff_label = font_btn.render("LOCAL or ONLINE?", True, (230, 220, 200))
            screen.blit(diff_label, diff_label.get_rect(center=(sw // 2, diff_y)))

            if arrow_l:
                screen.blit(arrow_l, (sw // 2 - 160, diff_y + 30))
            if arrow_r:
                screen.blit(arrow_r, (sw // 2 + 130, diff_y + 30))

            chip_w, chip_h = 140, 40
            for i, d in enumerate(input_options):
                bx = sw // 2 - 150 + i * 170
                by = diff_y + 30
                is_sel = (i == input_sel)
                chip_rect = pygame.Rect(bx, by, chip_w, chip_h)
                draw_angled_panel(screen, chip_rect, GOLD if is_sel else (70, 62, 78),
                                   border_color=GOLD, skew=8, border_width=3, selected=is_sel)
                outlined_text(screen, d, font_diff, chip_rect.center,
                              (40, 25, 5) if is_sel else (220, 218, 228),
                              outline_width=1, outline_color=(0, 0, 0), center=True)

        prompt_alpha = min(255, int(80 + 100 * ((math.sin(pulse_timer * 3) + 1) / 2)))
        if not confirmed:
            prompt = font_small.render("ARROWS/WASD to select  |  ENTER to confirm", True,
                                       (prompt_alpha, prompt_alpha, min(255, prompt_alpha + 40)))
        else:
            prompt = font_small.render("ENTER to confirm  |  ESC to go back", True,
                                       (prompt_alpha, prompt_alpha, min(255, prompt_alpha + 40)))
        screen.blit(prompt, prompt.get_rect(center=(sw // 2, 555)))

        controllers = get_connected_controllers()
        if controller_msg_timer > 0:
            msg_surf = font_small.render(controller_msg, True, (100, 255, 100))
            screen.blit(msg_surf, msg_surf.get_rect(center=(sw // 2, 525)))
        elif controllers:
            names = []
            for _, name, is_ps4 in controllers:
                tag = " (PS4)" if is_ps4 else ""
                names.append(name + tag)
            ctrl_surf = font_small.render("Controllers: {}".format(", ".join(names)), True, (150, 150, 170))
            screen.blit(ctrl_surf, ctrl_surf.get_rect(center=(sw // 2, 525)))
            kb_surf = font_tiny.render("Using keyboard? Press any key to switch", True, (130, 130, 160))
            screen.blit(kb_surf, kb_surf.get_rect(center=(sw // 2, 543)))
        else:
            ctrl_surf = font_small.render("No controller detected", True, (120, 120, 140))
            screen.blit(ctrl_surf, ctrl_surf.get_rect(center=(sw // 2, 525)))

            pair_label = font_tiny.render("[B] Bluetooth Setup  |  [D] Install DS4Windows (PS4)", True, GOLD)
            pair_rect = pair_label.get_rect(center=(sw // 2, 540))
            screen.blit(pair_label, pair_rect)

            keys_now = pygame.key.get_pressed()
            if not hasattr(mode_select, "_b_prev"):
                mode_select._b_prev = False
                mode_select._d_prev = False
            b_pressed = keys_now[pygame.K_b]
            d_pressed = keys_now[pygame.K_d]
            if b_pressed and not mode_select._b_prev:
                open_bluetooth_settings()
                show_pair_instructions = True
                pair_instr_timer = 10.0
            if d_pressed and not mode_select._d_prev:
                try:
                    webbrowser.open("https://github.com/ds4windowsapp/DS4Windows/releases")
                except Exception:
                    pass
                show_ds4_prompt = True
                pair_instr_timer = 10.0
            mode_select._b_prev = b_pressed
            mode_select._d_prev = d_pressed

        if show_pair_instructions and pair_instr_timer > 0:
            pair_instr_timer -= dt
            panel = pygame.Rect(0, 0, 540, 90)
            panel.center = (sw // 2, 475)
            draw_glass_panel(screen, panel, radius=12)

            title = font_small.render("Bluetooth pairing:", True, GOLD)
            screen.blit(title, title.get_rect(center=(sw // 2, 448)))

            instr_lines = [
                "1. Hold PS button 3 sec until light flashes",
                "2. Windows settings will open -> Click 'Add device'",
                "3. Select 'Wireless Controller' -> Done!",
            ]
            for i, line in enumerate(instr_lines):
                instr_surf = font_tiny.render(line, True, (200, 200, 220))
                screen.blit(instr_surf, instr_surf.get_rect(center=(sw // 2, 468 + i * 15)))

        if show_ds4_prompt and pair_instr_timer > 0:
            pair_instr_timer -= dt
            panel = pygame.Rect(0, 0, 540, 90)
            panel.center = (sw // 2, 475)
            draw_glass_panel(screen, panel, radius=12)

            title = font_small.render("PS4 controller needs a driver:", True, GOLD)
            screen.blit(title, title.get_rect(center=(sw // 2, 448)))

            instr_lines = [
                "DS4Windows opened in your browser - download & install it.",
                "It makes your PS4 controller work with ALL PC games.",
                "After install: plug in controller -> it just works!",
            ]
            for i, line in enumerate(instr_lines):
                color = (180, 255, 180) if i == 2 else (200, 200, 220)
                instr_surf = font_tiny.render(line, True, color)
                screen.blit(instr_surf, instr_surf.get_rect(center=(sw // 2, 468 + i * 15)))

        _mode_guard.draw(screen, font_title, font_btn)

        pygame.display.flip()


def stage_select(screen, font):
    from src.controller import get_connected_controllers
    font_title = pygame.font.Font(None, 42)
    font_btn = pygame.font.Font(None, 30)
    font_small = pygame.font.Font(None, 20)

    stages = [
        {"name": "World 1-1", "path": "assets/levels/world1-1.json", "tileset": "assets/tiles/tileset.png",
         "hazards": {"kamek": True, "bobombs": False, "grrrols": False, "pipe_spawns": False, "npcs": True}},
        {"name": "Factory", "path": "assets/levels/factory.json", "tileset": "assets/tiles/factory_tileset.png",
         "hazards": {"kamek": True, "bobombs": False, "grrrols": False, "pipe_spawns": False, "npcs": True}},
    ]
    sel = 0
    _clock = pygame.time.Clock()

    sw, sh = screen.get_size()

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    fade(screen, _clock, "in")

    while True:
        dt = _clock.tick(60) / 1000.0

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    sel = (sel - 1) % len(stages)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    sel = (sel + 1) % len(stages)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    fade(screen, _clock, "out")
                    return stages[sel]
                elif event.key == pygame.K_ESCAPE:
                    fade(screen, _clock, "out")
                    return None

        if _menu_ctrl.connected and not _mode_guard.blocked:
            if _menu_ctrl.left:
                sel = (sel - 1) % len(stages)
            elif _menu_ctrl.right:
                sel = (sel + 1) % len(stages)
            elif _menu_ctrl.confirm:
                fade(screen, _clock, "out")
                return stages[sel]
            elif _menu_ctrl.cancel:
                fade(screen, _clock, "out")
                return None

        draw_gradient_bg(screen)
        sw = screen.get_width()

        panel_rect = pygame.Rect(0, 0, 500, 320)
        panel_rect.center = (sw // 2, sh // 2)
        draw_glass_panel(screen, panel_rect, radius=22)

        outlined_text(screen, "SELECT STAGE", font_title, (sw // 2, panel_rect.y + 40), (255, 220, 80),
                      outline_width=3, outline_color=(70, 40, 5), center=True)

        for i, stage in enumerate(stages):
            is_sel = (i == sel)
            color = (255, 255, 100) if is_sel else (200, 200, 200)
            bx = sw // 2 - 180
            by = panel_rect.y + 90 + i * 70
            bw, bh = 360, 55
            btn_rect = pygame.Rect(bx, by, bw, bh)
            if is_sel:
                glow_surf = pygame.Surface((bw + 8, bh + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 220, 80, 60), glow_surf.get_rect(), border_radius=10)
                screen.blit(glow_surf, (bx - 4, by - 4))
            pygame.draw.rect(screen, (50, 80, 130) if is_sel else (40, 60, 100), btn_rect, border_radius=8)
            pygame.draw.rect(screen, (120, 180, 240) if is_sel else (80, 110, 160), btn_rect, 2, border_radius=8)

            stage_text = font_btn.render(stage["name"], True, color)
            tx = bx + bw // 2 - stage_text.get_width() // 2
            ty = by + bh // 2 - stage_text.get_height() // 2
            screen.blit(stage_text, (tx, ty))

        footer = font_small.render("ENTER to confirm  |  ESC to go back", True, (180, 180, 180))
        screen.blit(footer, (sw // 2 - footer.get_width() // 2, panel_rect.bottom + 15))

        _mode_guard.draw(screen, font_title, font_btn)

        pygame.display.flip()


def character_select(screen, font, ai_mode=None, ai_char=None,
                     lobby_client=None, is_online=False, is_host=True):
    import os
    import math
    import threading
    from src.ui_sprites import (load_arrow_key, load_stage_frame, load_start_btn,
                                 load_fire_flower, load_mushroom)
    from src.controller import get_connected_controllers

    font_title = pygame.font.Font(None, 48)
    font_normal = pygame.font.Font(None, 26)
    font_small = pygame.font.Font(None, 20)
    font_tiny = pygame.font.Font(None, 16)

    char_fonts = {
        "mario": {"font": pygame.font.Font(None, 30), "color": (220, 40, 40), "shadow": (100, 10, 10)},
        "luigi": {"font": pygame.font.Font(None, 28), "color": (50, 180, 50), "shadow": (20, 80, 20)},
        "yoshi": {"font": pygame.font.Font(None, 32), "color": (50, 160, 220), "shadow": (20, 60, 100)},
        "donkey_kong": {"font": pygame.font.Font(None, 26), "color": (200, 120, 50), "shadow": (90, 50, 20)},
    }

    characters = [
        {"name": "mario", "display": "MARIO", "color": (220, 40, 40), "accent": (255, 100, 100),
         "stats": {"Speed": 3, "Power": 3, "Jump": 3, "Weight": 4}},
        {"name": "luigi", "display": "LUIGI", "color": (40, 160, 40), "accent": (100, 230, 100),
         "stats": {"Speed": 2, "Power": 4, "Jump": 5, "Weight": 2}},
        {"name": "yoshi", "display": "YOSHI", "color": (40, 140, 200), "accent": (100, 200, 255),
         "stats": {"Speed": 5, "Power": 1, "Jump": 2, "Weight": 1}},
        {"name": "donkey_kong", "display": "DK", "color": (180, 100, 40), "accent": (220, 160, 80),
         "stats": {"Speed": 4, "Power": 5, "Jump": 2, "Weight": 3}},
    ]

    GRID_COLS = 3
    GRID_ROWS = 3
    grid = [None] * 9
    for i, ch in enumerate(characters):
        grid[i] = ch

    portrait_paths = [
        os.path.join("mario_assets", "mario_portrait_character_select.png"),
        os.path.join("luigi_assets", "Luigi_character_select_portrait.png"),
        os.path.join("Yoshi_assets", "Yoshi_character_select_portrait.png"),
        os.path.join("Donkey_Kong_assets", "donkey_kong_porrtrait.png"),
    ]
    portraits = {}
    for i, p in enumerate(portrait_paths):
        if os.path.exists(p):
            img = pygame.image.load(p).convert_alpha()
            iw, ih = img.get_size()
            if iw > ih * 1.2:
                scale = min(130 / iw, 120 / ih)
            else:
                scale = min(110 / iw, 130 / ih)
            portraits[i] = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))

    p1_index = 0
    p2_index = 1
    p1_locked = False
    p2_locked = False
    ai_selecting_cpu = False
    anim_timer = 0.0
    _clock = pygame.time.Clock()

    stage_frame = load_stage_frame(3)
    start_n = load_start_btn(False)
    start_h = load_start_btn(True)
    fire_flower_icon = load_fire_flower(3)
    mushroom_icon = load_mushroom(3)

    sw0, sh0 = screen.get_size()

    def find_next(idx, dx, dy):
        col = idx % GRID_COLS
        row = idx // GRID_COLS
        for step in range(1, 9):
            nc = (col + dx * step) % GRID_COLS
            nr = (row + dy * step) % GRID_ROWS
            ni = nr * GRID_COLS + nc
            if grid[ni] is not None:
                return ni
        return idx

    p1_prev_f = False
    p2_prev_j = False

    _has_ctrl = len(get_connected_controllers()) > 0
    if ai_mode is None:
        _mode_guard = None
    else:
        _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    opp_char_name = None
    lobby_poll_timer = 0.0
    lobby_poll_interval = 1.0
    last_sent_char = None

    fade(screen, _clock, "in")

    while True:
        dt = _clock.tick(60) / 1000.0
        anim_timer += dt

        if is_online and lobby_client and lobby_client.room_id:
            lobby_poll_timer += dt
            my_char = characters[p1_index]["name"]
            if my_char != last_sent_char:
                last_sent_char = my_char
                def _send_char(c=my_char, p=1 if is_host else 2):
                    lobby_client.update_character(c, player=p)
                threading.Thread(target=_send_char, daemon=True).start()
            if lobby_poll_timer >= lobby_poll_interval:
                lobby_poll_timer = 0.0
                def _poll_room():
                    nonlocal opp_char_name
                    info = lobby_client.get_room()
                    if info:
                        opp_field = "p2_character" if is_host else "p1_character"
                        opp_char_name = info.get(opp_field, "") or None
                threading.Thread(target=_poll_room, daemon=True).start()

        _menu_ctrl.refresh()

        keys_held = pygame.key.get_pressed()
        p1_f_now = keys_held[pygame.K_f]
        p2_j_now = keys_held[pygame.K_j]
        p1_f_fire = p1_f_now and not p1_prev_f
        p2_j_fire = p2_j_now and not p2_prev_j
        p1_prev_f = p1_f_now
        p2_prev_j = p2_j_now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if _mode_guard and not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    settings_state["fullscreen"] = not settings_state["fullscreen"]
                    pygame.display.toggle_fullscreen()

                if ai_mode and p1_locked and not p2_locked:
                    if not ai_selecting_cpu:
                        ai_selecting_cpu = True
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        p2_index = find_next(p2_index, -1, 0)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        p2_index = find_next(p2_index, 1, 0)
                    elif event.key in (pygame.K_w, pygame.K_UP):
                        p2_index = find_next(p2_index, 0, -1)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        p2_index = find_next(p2_index, 0, 1)
                    elif event.key in (pygame.K_f, pygame.K_SPACE, pygame.K_j, pygame.K_RETURN):
                        p2_locked = True

                elif not p1_locked:
                    if event.key in (pygame.K_a,):
                        p1_index = find_next(p1_index, -1, 0)
                    elif event.key in (pygame.K_d,):
                        p1_index = find_next(p1_index, 1, 0)
                    elif event.key in (pygame.K_w,):
                        p1_index = find_next(p1_index, 0, -1)
                    elif event.key in (pygame.K_s,):
                        p1_index = find_next(p1_index, 0, 1)
                    elif event.key in (pygame.K_f, pygame.K_SPACE):
                        p1_locked = True

                elif not ai_mode and not p2_locked:
                    if event.key in (pygame.K_LEFT,):
                        p2_index = find_next(p2_index, -1, 0)
                    elif event.key in (pygame.K_RIGHT,):
                        p2_index = find_next(p2_index, 1, 0)
                    elif event.key in (pygame.K_UP,):
                        p2_index = find_next(p2_index, 0, -1)
                    elif event.key in (pygame.K_DOWN,):
                        p2_index = find_next(p2_index, 0, 1)
                    elif event.key in (pygame.K_j, pygame.K_RETURN):
                        p2_locked = True

                if p1_locked and p2_locked and event.key in (pygame.K_f, pygame.K_SPACE, pygame.K_j, pygame.K_RETURN):
                    fade(screen, _clock, "out")
                    return characters[p1_index]["name"], characters[p2_index]["name"]

                if event.key == pygame.K_ESCAPE:
                    fade(screen, _clock, "out")
                    return None, None

        if _menu_ctrl.connected and (not _mode_guard or not _mode_guard.blocked):
            if _menu_ctrl.cancel:
                fade(screen, _clock, "out")
                return None, None
            if p1_locked and p2_locked and _menu_ctrl.confirm:
                fade(screen, _clock, "out")
                return characters[p1_index]["name"], characters[p2_index]["name"]
            if not p1_locked:
                if _menu_ctrl.left:
                    p1_index = find_next(p1_index, -1, 0)
                elif _menu_ctrl.right:
                    p1_index = find_next(p1_index, 1, 0)
                elif _menu_ctrl.up:
                    p1_index = find_next(p1_index, 0, -1)
                elif _menu_ctrl.down:
                    p1_index = find_next(p1_index, 0, 1)
                elif _menu_ctrl.confirm:
                    p1_locked = True
            elif ai_mode and p1_locked and not p2_locked:
                if _menu_ctrl.left:
                    p2_index = find_next(p2_index, -1, 0)
                elif _menu_ctrl.right:
                    p2_index = find_next(p2_index, 1, 0)
                elif _menu_ctrl.up:
                    p2_index = find_next(p2_index, 0, -1)
                elif _menu_ctrl.down:
                    p2_index = find_next(p2_index, 0, 1)
                elif _menu_ctrl.confirm:
                    p2_locked = True
            elif not ai_mode and not p2_locked:
                if _menu_ctrl.left:
                    p2_index = find_next(p2_index, -1, 0)
                elif _menu_ctrl.right:
                    p2_index = find_next(p2_index, 1, 0)
                elif _menu_ctrl.up:
                    p2_index = find_next(p2_index, 0, -1)
                elif _menu_ctrl.down:
                    p2_index = find_next(p2_index, 0, 1)
                elif _menu_ctrl.confirm:
                    p2_locked = True

        sw, sh = screen.get_size()

        draw_gradient_bg(screen)

        if ai_mode and p1_locked and not p2_locked:
            title_text = "SELECT CPU CHARACTER"
        else:
            title_text = "SELECT YOUR FIGHTER"
        outlined_text(screen, title_text, font_title, (sw // 2, 40), (255, 220, 80),
                      outline_width=3, outline_color=(70, 40, 5), center=True)

        card_w, card_h = 150, 130
        gap = 12
        grid_w = GRID_COLS * card_w + (GRID_COLS - 1) * gap
        grid_h = GRID_ROWS * card_h + (GRID_ROWS - 1) * gap
        grid_x = sw // 2 - grid_w // 2
        grid_y = 75

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                idx = row * GRID_COLS + col
                cx = grid_x + col * (card_w + gap)
                cy = grid_y + row * (card_h + gap)
                card_rect = pygame.Rect(cx, cy, card_w, card_h)

                ch = grid[idx]
                is_p1 = (p1_index == idx)
                is_p2 = (p2_index == idx)

                if ch is None:
                    lock_pts = draw_angled_panel(screen, card_rect, (18, 18, 30),
                                                  border_color=(45, 45, 65), skew=14,
                                                  border_width=1, shadow=False,
                                                  highlight=False, selected=False)
                    lock_font = pygame.font.Font(None, 36)
                    lock_surf = lock_font.render("?", True, (50, 50, 65))
                    screen.blit(lock_surf, lock_surf.get_rect(center=card_rect.center))
                    continue

                if is_p1 and is_p2:
                    border_color = (255, 200, 50)
                elif is_p1:
                    border_color = (255, 80, 80)
                elif is_p2:
                    border_color = (80, 160, 255)
                else:
                    border_color = (60, 60, 90)

                is_picked = is_p1 or is_p2
                pop = 1.05 if is_picked else 1.0
                pop_w, pop_h = int(card_w * pop), int(card_h * pop)
                pop_rect = pygame.Rect(0, 0, pop_w, pop_h)
                pop_rect.center = card_rect.center

                card_pts = draw_angled_panel(screen, pop_rect, (22, 22, 42),
                                              border_color=border_color, skew=14,
                                              border_width=3 if is_picked else 1,
                                              shadow=True, highlight=False,
                                              selected=is_picked)

                char_idx_list = [i for i, c in enumerate(grid) if c is not None]
                char_idx = char_idx_list.index(idx) if idx in char_idx_list else -1
                portrait = portraits.get(char_idx)
                if portrait:
                    px = pop_rect.centerx - portrait.get_width() // 2
                    py = pop_rect.y + 8
                    screen.blit(portrait, (px, py))

                cf = char_fonts.get(ch["name"], {"font": font_small, "color": (255, 255, 255), "shadow": (40, 40, 40)})
                name_shadow = cf["font"].render(ch["display"], True, cf["shadow"])
                screen.blit(name_shadow, name_shadow.get_rect(center=(cx + card_w // 2 + 2, cy + 100)))
                name_surf = cf["font"].render(ch["display"], True, cf["color"])
                screen.blit(name_surf, name_surf.get_rect(center=(cx + card_w // 2, cy + 98)))

                badge_y = cy + card_h - 22
                if is_p1:
                    p1_bg = pygame.Surface((card_w - 10, 18), pygame.SRCALPHA)
                    pygame.draw.rect(p1_bg, (255, 60, 60, 180), p1_bg.get_rect(), border_radius=4)
                    screen.blit(p1_bg, (cx + 5, badge_y))
                    p1_label = font_tiny.render("P1", True, (255, 255, 255))
                    screen.blit(p1_label, p1_label.get_rect(center=(cx + card_w // 2, badge_y + 9)))
                if is_p2:
                    if ai_mode:
                        label_text = "CPU"
                        label_color_bg = (60, 180, 60, 180)
                    else:
                        label_text = "P2"
                        label_color_bg = (60, 120, 255, 180)
                    p2_bg = pygame.Surface((card_w - 10, 18), pygame.SRCALPHA)
                    pygame.draw.rect(p2_bg, label_color_bg, p2_bg.get_rect(), border_radius=4)
                    screen.blit(p2_bg, (cx + 5, badge_y))
                    p2_label = font_tiny.render(label_text, True, (255, 255, 255))
                    screen.blit(p2_label, p2_label.get_rect(center=(cx + card_w // 2, badge_y + 9)))

        footer_y = grid_y + grid_h + 25
        if p1_locked and p2_locked:
            pulse = math.sin(anim_timer * 5) * 0.3 + 0.7
            btn_img = start_h if pulse > 0.5 else start_n
            if btn_img:
                bx = sw // 2 - btn_img.get_width() // 2
                screen.blit(btn_img, (bx, footer_y))
        else:
            pulse = (math.sin(anim_timer * 4) + 1) / 2
            prompt_alpha = int(140 + 80 * pulse)
            col = (prompt_alpha, prompt_alpha, min(255, prompt_alpha + 30))
            dim = (130, 130, 150)
            if ai_mode and p1_locked and not p2_locked:
                line1 = font_small.render("CPU PICK: WASD/Arrows to move  |  F or J to confirm", True, col)
                line2 = font_small.render("ESC to go back", True, dim)
                screen.blit(line1, line1.get_rect(center=(sw // 2, footer_y + 12)))
                screen.blit(line2, line2.get_rect(center=(sw // 2, footer_y + 30)))
            elif ai_mode:
                line1 = font_small.render("P1: WASD to move  |  F to confirm", True, col)
                line2 = font_small.render("ESC to go back", True, dim)
                screen.blit(line1, line1.get_rect(center=(sw // 2, footer_y + 12)))
                screen.blit(line2, line2.get_rect(center=(sw // 2, footer_y + 30)))
            else:
                line1 = font_small.render("P1: WASD to move + F to confirm", True, col)
                line2 = font_small.render("P2: Arrows to move + J to confirm", True, col)
                line3 = font_small.render("ESC to go back", True, dim)
                screen.blit(line1, line1.get_rect(center=(sw // 2, footer_y + 5)))
                screen.blit(line2, line2.get_rect(center=(sw // 2, footer_y + 22)))
                screen.blit(line3, line3.get_rect(center=(sw // 2, footer_y + 39)))

        if is_online and opp_char_name:
            opp_label = font_tiny.render(f"OPPONENT: {opp_char_name.upper()}", True, (100, 200, 255))
            opp_bg = pygame.Surface((opp_label.get_width() + 16, 22), pygame.SRCALPHA)
            pygame.draw.rect(opp_bg, (0, 0, 0, 140), opp_bg.get_rect(), border_radius=6)
            screen.blit(opp_bg, (sw - opp_bg.get_width() - 15, 15))
            screen.blit(opp_label, (sw - opp_label.get_width() - 7, 20))
        elif is_online:
            spinner_chars = ["|", "/", "-", "\\"]
            spinner = spinner_chars[int(anim_timer * 4) % 4]
            wait_label = font_tiny.render(f"{spinner} Waiting for opponent...", True, (160, 160, 180))
            wait_bg = pygame.Surface((wait_label.get_width() + 16, 22), pygame.SRCALPHA)
            pygame.draw.rect(wait_bg, (0, 0, 0, 140), wait_bg.get_rect(), border_radius=6)
            screen.blit(wait_bg, (sw - wait_bg.get_width() - 15, 15))
            screen.blit(wait_label, (sw - wait_label.get_width() - 7, 20))

        if _mode_guard:
            _mode_guard.draw(screen, font_title, font_normal)

        pygame.display.flip()


def tutorial_screen(screen, font):
    """Character + input selection for tutorial mode."""
    from src.controller import get_connected_controllers
    clock = pygame.time.Clock()
    chars = [("mario", "Mario"), ("luigi", "Luigi"), ("yoshi", "Yoshi"), ("donkey_kong", "DK")]
    sel = 0
    input_mode = 0  # 0 = keyboard, 1 = controller
    pulse_timer = 0.0

    import os
    sw, sh = screen.get_size()
    from src.ui_theme import draw_gradient_bg, draw_panel, draw_glow, outlined_text

    portrait_paths = {
        "mario": os.path.join("mario_assets", "mario_portrait_character_select.png"),
        "luigi": os.path.join("luigi_assets", "Luigi_character_select_portrait.png"),
        "yoshi": os.path.join("Yoshi_assets", "Yoshi_character_select_portrait.png"),
        "donkey_kong": os.path.join("Donkey_Kong_assets", "donkey_kong_porrtrait.png"),
    }
    portraits = {}
    for key, path in portrait_paths.items():
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            iw, ih = img.get_size()
            if iw > ih:
                scale = min(150 / iw, 170 / ih)
            else:
                scale = min(130 / iw, 170 / ih)
            portraits[key] = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))

    focus = 0  # 0 = input mode, 1 = character select

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    while True:
        dt = clock.tick(60) / 1000.0
        pulse_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if focus == 0:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        input_mode = (input_mode - 1) % 2
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        input_mode = (input_mode + 1) % 2
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        focus = 1
                    elif event.key == pygame.K_ESCAPE:
                        return None, None
                else:
                    if event.key == pygame.K_LEFT:
                        sel = (sel - 1) % len(chars)
                    elif event.key == pygame.K_RIGHT:
                        sel = (sel + 1) % len(chars)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return chars[sel][0], input_mode == 1
                    elif event.key == pygame.K_ESCAPE:
                        focus = 0

        draw_gradient_bg(screen)

        title = font.render("TUTORIAL", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(sw // 2, 40)))

        input_y = 100
        input_label = font.render("INPUT:", True, (180, 180, 200))
        screen.blit(input_label, input_label.get_rect(center=(sw // 2 - 100, input_y)))

        for i, label in enumerate(["KEYBOARD", "CONTROLLER"]):
            x = sw // 2 + 20 + i * 160
            is_sel = (i == input_mode) and focus == 0
            col = (255, 220, 80) if is_sel else (150, 150, 170)
            surf = font.render(label, True, col)
            screen.blit(surf, surf.get_rect(center=(x, input_y)))
            if is_sel:
                arrow = font.render("<", True, (255, 220, 80))
                screen.blit(arrow, (x - surf.get_width() // 2 - 20, input_y - 10))

        char_y = 200
        char_title = font.render("SELECT CHARACTER", True, (180, 180, 200))
        screen.blit(char_title, char_title.get_rect(center=(sw // 2, char_y)))

        card_w = 150
        total_w = len(chars) * card_w + (len(chars) - 1) * 20
        start_x = (sw - total_w) // 2

        for i, (key, name) in enumerate(chars):
            x = start_x + i * (card_w + 20)
            y = 250
            is_sel = i == sel and focus == 1
            rect = pygame.Rect(x, y, card_w, 180)

            border_col = (255, 220, 80) if is_sel else (80, 80, 120)
            draw_panel(screen, rect, (30, 30, 50), border=2, radius=8, shadow=is_sel)

            img = portraits.get(key)
            if img:
                iw, ih = img.get_size()
                scale = min((card_w - 20) / iw, (100) / ih)
                new_w, new_h = int(iw * scale), int(ih * scale)
                scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                screen.blit(scaled, (x + (card_w - new_w) // 2, y + 10))

            col = (255, 220, 80) if is_sel else (200, 200, 200)
            name_surf = font.render(name, True, col)
            screen.blit(name_surf, name_surf.get_rect(center=(x + card_w // 2, y + 140)))

        if focus == 0:
            hint = font.render("LEFT/RIGHT to pick input, ENTER to confirm", True, (150, 150, 170))
        else:
            hint = font.render("LEFT/RIGHT to pick, ENTER to start, ESC back", True, (150, 150, 170))
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh - 40)))

        _mode_guard.draw(screen, font, font)

        pygame.display.flip()


def tutorial_sandbox(screen, clock, font, sprite_lookup, char_name, use_controller=False):
    from src.ui_sprites import load_countdown

    font_small = pygame.font.Font(None, 22)
    font_head = pygame.font.Font(None, 28)
    font_body = pygame.font.Font(None, 26)

    tileset_surf = pygame.image.load("assets/tiles/tileset.png").convert()
    tilemap = Tilemap("assets/levels/world1-1.json", tileset_surf)
    solid = tilemap.solid_rects()
    platforms = tilemap.platform_rects()
    bg = Background()

    LEVEL_W = tilemap.level_w or SCREEN_W
    LEVEL_H = tilemap.level_h or SCREEN_H
    camera = Camera(LEVEL_W, LEVEL_H)

    ground_y = 33 * TILE_SIZE * MAP_SCALE
    char_hit_heights = {"mario": 44, "luigi": 32, "yoshi": 32, "donkey_kong": 50}
    spawn_y = ground_y - char_hit_heights.get(char_name, 44)
    player = Player(400, spawn_y, sprite_lookup[char_name], character=char_name, controls=CTRL_P1)
    player.animator.set_state("start_idle", force=True)
    player.facing = 1

    dummy = Player(600, spawn_y, sprite_lookup["mario"], character="mario", controls=CTRL_P2)
    dummy.animator.set_state("start_idle", force=True)
    dummy.facing = -1
    dummy.hearts = 999
    dummy.percentage = 0

    num_joysticks = pygame.joystick.get_count()
    if use_controller and num_joysticks >= 1:
        gamepad1 = GamepadInput(0, ctrl=CTRL_P1)
    else:
        gamepad1 = None
    use_controller_input = use_controller and gamepad1 is not None

    p1_mouse_input = MouseAwareKeys(CTRL_P1)

    particles = ParticleSystem()
    shake = ScreenShake()
    shells = []
    eggs = []
    projectiles = []

    if use_controller_input:
        _char_tutorials = {
            "mario": [
                ("move", "STICK", "Use the left stick to move around the stage."),
                ("light", "SQUARE", "Press Square to do a light attack combo. Try it 3 times!"),
                ("heavy", "CIRCLE", "Press Circle for a heavy attack. It does 2x damage!"),
                ("aerial_f", "SQUARE (air)", "Jump with X, then press Square in the air for an aerial attack."),
                ("aerial_g", "CIRCLE (air)", "Jump with X, then press Circle in the air for a heavy aerial."),
                ("special_e", "TRIANGLE", "Press Triangle to do a Fire Punch! Quick melee fire attack."),
                ("special_fe", "SQUARE then TRIANGLE", "Press Square, then quickly press Triangle for a Fire Punch combo!"),
                ("block", "L1", "Press L1 to raise your shield. It blocks incoming damage."),
                ("dash", "STICK+D-LEFT", "Hold left on the stick to run, then tap left on D-pad to dash forward!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "luigi": [
                ("move", "STICK", "Use the left stick to move around the stage."),
                ("light", "SQUARE", "Press Square to do a light attack combo. Try it 3 times!"),
                ("heavy", "CIRCLE", "Press Circle for a heavy attack. Strong starter!"),
                ("aerial_f", "SQUARE (air)", "Jump with X, then press Square in the air for an aerial."),
                ("aerial_g", "CIRCLE (air)", "Jump with X, then press Circle for a downward spike."),
                ("special_e", "TRIANGLE", "Press Triangle for Head Drill! 18 damage, locks them in!"),
                ("special_fe", "SQUARE then TRIANGLE", "Press Square, then Triangle for a Blastshot projectile!"),
                ("block", "L1", "Press L1 to raise your shield."),
                ("dash", "STICK+D-LEFT", "Hold left on the stick to run, then tap left on D-pad to dash!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "yoshi": [
                ("move", "STICK", "Use the left stick to move around the stage."),
                ("light", "SQUARE", "Press Square to do a light attack combo. Try it 3 times!"),
                ("heavy", "CIRCLE", "Press Circle for a heavy attack. Great after rolling!"),
                ("aerial_f", "SQUARE (air)", "Jump with X, then press Square in the air."),
                ("aerial_g", "CIRCLE (air)", "Jump with X, then press Circle for a spike!"),
                ("special_q", "L1", "Press L1 to throw an Egg projectile!"),
                ("special_e", "TRIANGLE", "Press Triangle to do an Egg Roll! You roll forward damaging foes."),
                ("special_air_e", "TRIANGLE (air)", "Jump with X, then press Triangle in the air to throw an Egg!"),
                ("block", "L1", "Press L1 to use your egg shield counter!"),
                ("dash", "STICK+D-LEFT", "Hold left on the stick to run, then tap left on D-pad to roll!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "donkey_kong": [
                ("move", "STICK", "Use the left stick to move around the stage."),
                ("light", "SQUARE", "Press Square to do a light attack combo. Try it 3 times!"),
                ("heavy", "CIRCLE", "Press Circle for a heavy attack. Devastating knockback!"),
                ("aerial_f", "SQUARE (air)", "Jump with X, then press Square in the air for a long reach attack."),
                ("aerial_g", "CIRCLE (air)", "Jump with X, then press Circle for a slam spike!"),
                ("special_e", "TRIANGLE", "Press Triangle for Barrel Smash! Your strongest kill move!"),
                ("special_fe", "SQUARE then TRIANGLE", "Press Square, then Triangle to throw a rolling barrel!"),
                ("block", "L1", "Press L1 to raise your shield."),
                ("dash", "STICK+D-LEFT", "Hold left on the stick to run, then tap left on D-pad to barrel roll!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
        }
    else:
        _char_tutorials = {
            "mario": [
                ("move", "WASD", "Use WASD to move around the stage."),
                ("light", "F", "Press F to do a light attack combo. Try it 3 times!"),
                ("heavy", "G", "Press G for a heavy attack. It does 2x damage!"),
                ("aerial_f", "F (air)", "Jump with W, then press F in the air for an aerial attack."),
                ("aerial_g", "G (air)", "Jump with W, then press G in the air for a heavy aerial."),
                ("special_e", "E", "Press E to do a Fire Punch! Quick melee fire attack."),
                ("special_fe", "F then E", "Press F, then quickly press E for a Fire Punch combo!"),
                ("block", "Q", "Press Q to raise your shield. It blocks incoming damage."),
                ("dash", "DOWN+D", "Hold D to run, then tap S to dash forward!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "luigi": [
                ("move", "WASD", "Use WASD to move around the stage."),
                ("light", "F", "Press F to do a light attack combo. Try it 3 times!"),
                ("heavy", "G", "Press G for a heavy attack. Strong starter!"),
                ("aerial_f", "F (air)", "Jump with W, then press F in the air for an aerial."),
                ("aerial_g", "G (air)", "Jump with W, then press G for a downward spike."),
                ("special_e", "E", "Press E for Head Drill! 18 damage, locks them in!"),
                ("special_fe", "F then E", "Press F, then E for a Blastshot projectile!"),
                ("block", "Q", "Press Q to raise your shield."),
                ("dash", "DOWN+D", "Hold D to run, then tap S to dash!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "yoshi": [
                ("move", "WASD", "Use WASD to move around the stage."),
                ("light", "F", "Press F to do a light attack combo. Try it 3 times!"),
                ("heavy", "G", "Press G for a heavy attack. Great after rolling!"),
                ("aerial_f", "F (air)", "Jump with W, then press F in the air."),
                ("aerial_g", "G (air)", "Jump with W, then press G for a spike!"),
                ("special_q", "Q", "Press Q to throw an Egg projectile!"),
                ("special_e", "E", "Press E to do an Egg Roll! You roll forward damaging foes."),
                ("special_air_e", "E (air)", "Jump with W, then press E in the air to throw an Egg!"),
                ("block", "Q", "Press Q to use your egg shield counter!"),
                ("dash", "DOWN+D", "Hold D to run, then tap S to roll!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
            "donkey_kong": [
                ("move", "WASD", "Use WASD to move around the stage."),
                ("light", "F", "Press F to do a light attack combo. Try it 3 times!"),
                ("heavy", "G", "Press G for a heavy attack. Devastating knockback!"),
                ("aerial_f", "F (air)", "Jump with W, then press F in the air for a long reach attack."),
                ("aerial_g", "G (air)", "Jump with W, then press G for a slam spike!"),
                ("special_e", "E", "Press E for Barrel Smash! Your strongest kill move!"),
                ("special_fe", "F then E", "Press F, then E to throw a rolling barrel!"),
                ("block", "Q", "Press Q to raise your shield."),
                ("dash", "DOWN+D", "Hold D to run, then tap S to barrel roll!"),
                ("done", "", "You know the basics! Head into a match and fight!"),
            ],
        }

    prompts = _char_tutorials.get(char_name, _char_tutorials["mario"])
    prompt_step = 0
    prompt_action, prompt_key, prompt_text = prompts[0]
    move_count = 0
    moves_needed = {
        "light": 3, "heavy": 2, "aerial_f": 2, "aerial_g": 2,
        "special_e": 2, "special_fe": 1, "special_q": 2,
        "special_air_e": 1,
        "block": 2, "dash": 2, "move": 1,
    }

    prev_attacking = 0
    prev_special_active = 0
    prev_shielding = False
    prev_on_ground = True
    prev_airborne = False
    prev_dashing = False
    was_moving = False

    frame = 0
    hud = MarioHUD()
    dt = 1.0 / FPS

    fade(screen, clock, "in")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    return

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        p1_mouse_input.refresh(keys, mouse_buttons)
        if gamepad1:
            gamepad1.refresh()
            p1_input = gamepad1
        else:
            p1_input = p1_mouse_input

        for p in (player, dummy):
            if p.hitlag > 0:
                p.hitlag -= 1

        frozen = player.hitlag > 0 or dummy.hitlag > 0

        if not frozen:
            player.update(p1_input, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)
            player.special_cooldown = 0
            player.heavy_cooldown = 0
            if dummy.is_dead:
                dummy.respawn(600, ground_y - char_hit_heights.get("mario", 44))
                dummy.hearts = 999
            else:
                dummy.update(keys, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)

        if dummy.hearts <= 0:
            dummy.respawn(600, ground_y - char_hit_heights.get("mario", 44))
            dummy.hearts = 999

        # --- Track move completion ---
        if prompt_step < len(prompts) and prompt_action != "done":
            action = prompt_action
            completed = False

            if action == "move":
                moving = abs(player.vx_int) > 0.5
                if moving and not was_moving:
                    completed = True
                was_moving = moving

            elif action == "light":
                if player.attacking > 0 and not player.heavy_attack:
                    if prev_attacking <= 0:
                        move_count += 1
                if move_count >= moves_needed["light"]:
                    completed = True
                prev_attacking = player.attacking

            elif action == "heavy":
                if player.attacking > 0 and player.heavy_attack:
                    if prev_attacking <= 0:
                        move_count += 1
                if move_count >= moves_needed["heavy"]:
                    completed = True
                prev_attacking = player.attacking

            elif action == "aerial_f":
                if player.attacking > 0 and not player.heavy_attack and not player.on_ground:
                    if prev_attacking <= 0:
                        move_count += 1
                if move_count >= moves_needed["aerial_f"]:
                    completed = True
                prev_attacking = player.attacking
                prev_on_ground = player.on_ground

            elif action == "aerial_g":
                if player.attacking > 0 and not player.on_ground:
                    if prev_attacking <= 0:
                        move_count += 1
                if move_count >= moves_needed["aerial_g"]:
                    completed = True
                prev_attacking = player.attacking

            elif action == "special_e":
                if player.special_active > 0:
                    if prev_special_active <= 0:
                        move_count += 1
                if move_count >= moves_needed["special_e"]:
                    completed = True
                prev_special_active = player.special_active

            elif action == "special_air_e":
                if not player.on_ground and player.special_active > 0 and prev_special_active <= 0:
                    move_count += 1
                if move_count >= moves_needed["special_air_e"]:
                    completed = True
                prev_special_active = player.special_active

            elif action == "special_fe":
                if player.special_active > 0 and prev_special_active <= 0:
                    if player.special_name in ("fire_punch", "blastshot", "barrel_throw"):
                        completed = True
                prev_special_active = player.special_active

            elif action == "special_q":
                if player.special_active > 0:
                    if prev_special_active <= 0:
                        move_count += 1
                if move_count >= moves_needed["special_q"]:
                    completed = True
                prev_special_active = player.special_active

            elif action == "block":
                if player.shielding:
                    if not prev_shielding:
                        move_count += 1
                if move_count >= moves_needed["block"]:
                    completed = True
                prev_shielding = player.shielding

            elif action == "dash":
                if player.dashing and not prev_dashing:
                    move_count += 1
                if move_count >= moves_needed["dash"]:
                    completed = True
                prev_dashing = player.dashing

            if completed:
                prompt_step += 1
                if prompt_step < len(prompts):
                    prompt_action, prompt_key, prompt_text = prompts[prompt_step]
                    move_count = 0

        # --- Melee attacks (ground + aerial, matching main match loop) ---
        attack_landed = False
        for attacker, victim in [(player, dummy)]:
            if (attacker.attacking > 0 and
                attacker.hitstun <= 0 and
                not attacker.hit_this_swing):

                if attacker.heavy_attack:
                    hitbox = attacker.heavy_hitbox()
                    hit_start = attacker.attack_hit_start
                    hit_end = attacker.attack_hit_end
                    current_frame = attacker.attack_frames - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    if (attacker.combo_type == "heavy" and attacker.combo_version > 0):
                        _combo_tables = {"yoshi": YOSHI_HEAVY_COMBO, "mario": MARIO_HEAVY_COMBO, "luigi": LUIGI_HEAVY_COMBO, "donkey_kong": DK_HEAVY_COMBO}
                        table = _combo_tables.get(attacker.char)
                        if table and attacker.combo_version in table:
                            d, bk, kg, fr, hs, he, kb = table[attacker.combo_version]
                            damage = attacker.attack_damage
                            base_kb = attacker.attack_base_kb
                            kb_growth = attacker.attack_kb_growth
                            kb_type = attacker.attack_kb_type
                        else:
                            damage = attacker.get_heavy_damage()
                            base_kb = attacker.get_heavy_base_kb()
                            kb_growth = attacker.get_heavy_kb_growth()
                            kb_type = "straight"
                    else:
                        damage = attacker.get_heavy_damage()
                        base_kb = attacker.get_heavy_base_kb()
                        kb_growth = attacker.get_heavy_kb_growth()
                        kb_type = "straight"
                elif attacker.aerial_attack_stats:
                    hitbox = attacker.aerial_hitbox()
                    hit_start = attacker.aerial_attack_stats[5]
                    hit_end = attacker.aerial_attack_stats[6]
                    current_frame = attacker.aerial_attack_stats[4] - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    damage = attacker.aerial_attack_stats[0]
                    base_kb = attacker.aerial_attack_stats[1]
                    kb_growth = attacker.aerial_attack_stats[2]
                    kb_type = attacker.aerial_attack_stats[7]
                else:
                    hitbox = attacker.attack_hitbox()
                    hit_start = attacker.attack_hit_start
                    hit_end = attacker.attack_hit_end
                    current_frame = attacker.attack_frames - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    if attacker.combo_type == "light" and attacker.combo_version > 0:
                        _combo_tables = {"yoshi": YOSHI_LIGHT_COMBO, "mario": MARIO_LIGHT_COMBO, "luigi": LUIGI_LIGHT_COMBO, "donkey_kong": DK_LIGHT_COMBO}
                        table = _combo_tables.get(attacker.char)
                        if table and attacker.combo_version in table:
                            damage = attacker.attack_damage
                            base_kb = attacker.attack_base_kb
                            kb_growth = attacker.attack_kb_growth
                            kb_type = table[attacker.combo_version][6]
                        else:
                            damage = attacker.attack_damage
                            base_kb = attacker.attack_base_kb
                            kb_growth = attacker.attack_kb_growth
                            kb_type = attacker.attack_kb_type
                    else:
                        damage = attacker.attack_damage
                        base_kb = attacker.attack_base_kb
                        kb_growth = attacker.attack_kb_growth
                        kb_type = attacker.attack_kb_type

                if in_active and hitbox.colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(damage, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(damage, victim.facing)
                            attacker.hit_this_swing = True
                            attack_landed = True
                            shake.trigger(duration=8, intensity=int(2 + victim.percentage * 0.05))
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        damage *= attacker.damage_mult
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        c_mult = 1.0
                        if attacker.combo_type == "light" and attacker.combo_version > 0:
                            c_mult = {1: 0.35, 2: 0.55, 3: 0.75}.get(attacker.combo_version, 1.0)
                        victim.take_damage(
                            base_damage=damage,
                            knockback_growth=kb_growth,
                            base_knockback=base_kb,
                            attacker_facing=attacker.facing,
                            kb_bonus=1.0 * ch_mult,
                            knockback_type=kb_type,
                            di_y=di_y,
                            attacker_percent=attacker.percentage,
                            combo_launch_mult=c_mult
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.hit_this_swing = True
                        attacker.update_combo(damage)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim)
                        attacker_lag = attacker.attack_frames
                        is_true = victim.is_true_combo(damage, attacker_lag, kb_growth, base_kb, 1.0 * ch_mult)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)
                        shake.trigger(duration=10, intensity=int(3 + victim.percentage * 0.08))
                        attack_landed = True

        # --- Special moves ---
        for attacker, victim in [(player, dummy)]:
            # Fire Punch
            if (attacker.special_active > 0 and
                attacker.special_name == "fire_punch" and
                not attacker.special_hit and
                FIRE_PUNCH_HIT_START <= attacker.special_active <= FIRE_PUNCH_HIT_END):
                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(FIRE_PUNCH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(FIRE_PUNCH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=10, intensity=int(3 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=FIRE_PUNCH_DAMAGE * attacker.damage_mult,
                            knockback_growth=FIRE_PUNCH_KNOCKBACK_GROWTH,
                            base_knockback=FIRE_PUNCH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=FIRE_PUNCH_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(FIRE_PUNCH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        shake.trigger(duration=12, intensity=int(3 + victim.percentage * 0.08))
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "hammer_smash" and
                not attacker.special_hit and
                HAMMER_SMASH_HIT_START <= attacker.special_active <= HAMMER_SMASH_HIT_END):
                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(HAMMER_SMASH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(HAMMER_SMASH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=12, intensity=int(4 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=HAMMER_SMASH_DAMAGE * attacker.damage_mult,
                            knockback_growth=HAMMER_SMASH_KNOCKBACK_GROWTH,
                            base_knockback=HAMMER_SMASH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=HAMMER_SMASH_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(HAMMER_SMASH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        shake.trigger(duration=15, intensity=int(4 + victim.percentage * 0.08))
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "head_drill" and
                not attacker.special_hit and
                HEAD_DRILL_HIT_START <= attacker.special_active <= HEAD_DRILL_HIT_END):
                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(HEAD_DRILL_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(HEAD_DRILL_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=12, intensity=int(4 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=HEAD_DRILL_DAMAGE * attacker.damage_mult,
                            knockback_growth=HEAD_DRILL_KNOCKBACK_GROWTH,
                            base_knockback=HEAD_DRILL_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=HEAD_DRILL_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(HEAD_DRILL_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        shake.trigger(duration=15, intensity=int(4 + victim.percentage * 0.08))
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "barrel_smash" and
                not attacker.special_hit and
                BARREL_SMASH_HIT_START <= attacker.special_active <= BARREL_SMASH_HIT_END):
                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(BARREL_SMASH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(BARREL_SMASH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=12, intensity=int(4 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        victim.take_damage(
                            base_damage=BARREL_SMASH_DAMAGE * attacker.damage_mult,
                            knockback_growth=BARREL_SMASH_KNOCKBACK_GROWTH,
                            base_knockback=BARREL_SMASH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=BARREL_SMASH_KB_BONUS,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        attacker.special_hit = True
                        attacker.update_combo(BARREL_SMASH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        shake.trigger(duration=15, intensity=int(4 + victim.percentage * 0.08))
                        attack_landed = True

            # Yoshi egg throw spawn
            if (attacker.special_active > 0 and
                attacker.special_name in ("egg_throw_ground", "egg_throw_air") and
                not attacker.special_spawned and
                attacker.special_active <= EGG_THROW_SPAWN_FRAME):
                offset = 40 * attacker.facing
                egg_x = attacker.rect.centerx + offset
                egg_y = attacker.rect.centery - 10
                egg = EggProjectile(egg_x, egg_y, attacker.facing, attacker,
                                    sprite_lookup[attacker.char], scale=SCALE)
                eggs.append(egg)
                attacker.special_spawned = True

        # --- Blastshot / Barrel spawn (fire_punch is melee) ---
        for attacker, victim in [(player, dummy)]:
            if (attacker.special_active > 0 and not attacker.special_spawned):
                if attacker.special_name == "fire_punch":
                    attacker.special_spawned = True
                elif attacker.special_name == "blastshot":
                    offset = 30 * attacker.facing
                    bx = attacker.rect.centerx + offset
                    by = attacker.rect.centery - 5
                    proj = Blastshot(bx, by, attacker.facing, attacker)
                    projectiles.append(proj)
                    attacker.special_spawned = True
                elif attacker.special_name == "barrel_throw":
                    offset = 30 * attacker.facing
                    bx = attacker.rect.centerx + offset
                    by = attacker.rect.centery - 5
                    proj = Barrel(bx, by, attacker.facing, attacker)
                    projectiles.append(proj)
                    attacker.special_spawned = True

        # --- Yoshi egg roll collision ---
        for attacker, victim in [(player, dummy)]:
            if (attacker.char == "yoshi" and attacker.egg_rolling and
                attacker.egg_roll_hit_interval >= EGG_ROLL_HIT_INTERVAL):
                roll_box = attacker.rect.copy()
                roll_box.width += 20
                if attacker.facing == 1:
                    roll_box.left = attacker.rect.right
                else:
                    roll_box.right = attacker.rect.left
                if roll_box.colliderect(victim.rect):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(EGG_ROLL_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(EGG_ROLL_DAMAGE, victim.facing)
                            attacker.egg_roll_hit_interval = 0
                            shake.trigger(duration=8, intensity=int(2 + victim.percentage * 0.05))
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        victim.take_damage(
                            base_damage=EGG_ROLL_DAMAGE,
                            knockback_growth=EGG_ROLL_KNOCKBACK_GROWTH,
                            base_knockback=EGG_ROLL_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=EGG_ROLL_KB_BONUS,
                            knockback_type=EGG_ROLL_KB_TYPE,
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        attacker.egg_roll_hit_interval = 0
                        attacker.hit_this_swing = True
                        shake.trigger(duration=8, intensity=int(2 + victim.percentage * 0.05))
                        attack_landed = True

        # --- Egg projectile collision ---
        for egg in eggs:
            if egg.active and egg.rect.colliderect(dummy.rect):
                if dummy.shielding and dummy.shield_health > 0:
                    egg.active = False
                else:
                    di_y = get_di_y(keys, dummy.ctrl)
                    dummy.take_damage(
                        base_damage=EGG_DAMAGE,
                        knockback_growth=EGG_KNOCKBACK_GROWTH,
                        base_knockback=EGG_BASE_KNOCKBACK,
                        attacker_facing=egg.facing,
                        kb_bonus=1.0,
                        knockback_type="normal",
                        di_y=di_y,
                        attacker_percent=player.percentage
                    )
                    egg.active = False
                    shake.trigger(duration=6, intensity=3)

        Player.resolve_overlap(player, dummy, solid, skip_stomp=attack_landed)

        if dummy.percentage > 200:
            dummy.die()
            dummy.respawn(600, ground_y - char_hit_heights.get("mario", 44))
            dummy.hearts = 999
            dummy.percentage = 0

        for p in (player, dummy):
            if not p.is_dead:
                if (p.rect.right < -BLAST_ZONE_MARGIN_SIDE or
                    p.rect.left > LEVEL_W + BLAST_ZONE_MARGIN_SIDE or
                    p.rect.top > LEVEL_H + BLAST_ZONE_MARGIN_BOTTOM or
                    p.rect.bottom < -BLAST_ZONE_MARGIN_TOP):
                    p.die()
                    if p == player:
                        player.respawn(400, ground_y - char_hit_heights.get(char_name, 44))

        mid_x = player.rect.centerx
        mid_y = player.rect.centery
        camera.set_zoom(1.0)
        camera.set_shake(shake.update())
        camera.follow(mid_x, mid_y, dt)

        render_w, render_h = camera.get_render_size()
        cam_off = (int(camera.offset.x), int(camera.offset.y))

        world_surf = pygame.Surface((render_w, render_h))
        world_surf.fill((92, 148, 252))
        bg.draw(world_surf, cam_off, LEVEL_W, ground_y, tilemap.tile_px)
        tilemap.draw(world_surf, cam_off, tileset_surf)

        for proj in projectiles:
            proj.update(solid)
            proj.draw(world_surf, cam_off)
        projectiles = [p for p in projectiles if p.active]

        player.draw(world_surf, cam_off)
        dummy.draw(world_surf, cam_off)

        scaled = pygame.transform.smoothscale(world_surf, screen.get_size())
        screen.blit(scaled, (0, 0))

        hud.draw(screen, [
            {"name": f"{player.char.upper()}", "percentage": player.percentage,
             "stocks": player.hearts, "max_stocks": LIVES,
             "shield_pct": player.shield_health / MAX_SHIELD_HEALTH,
             "shielding": player.shielding,
             "color": CHAR_COLORS.get(player.char, (200, 200, 200))},
        ], time_left=0)

        # --- Tutorial prompt box ---
        char_colors_tut = {
            "mario": (229, 37, 33), "luigi": (67, 176, 71),
            "yoshi": (118, 188, 66), "donkey_kong": (180, 100, 40),
        }
        cc = char_colors_tut.get(char_name, (200, 200, 200))

        box_h = 80
        box_y = SCREEN_H - box_h - 10
        prompt_box = pygame.Rect(30, box_y, SCREEN_W - 60, box_h)
        draw_panel(screen, prompt_box, (15, 15, 30), border=2, radius=14, shadow=True)
        pygame.draw.rect(screen, cc, prompt_box, 2, border_radius=14)

        if prompt_action == "done":
            done_text = font.render(prompt_text, True, (100, 255, 100))
            screen.blit(done_text, done_text.get_rect(center=(SCREEN_W // 2, box_y + box_h // 2)))
        else:
            step_text = f"[{prompt_step + 1}/{len(prompts) - 1}]"
            step_surf = font_small.render(step_text, True, (120, 120, 150))
            screen.blit(step_surf, (prompt_box.x + 14, prompt_box.y + 8))

            key_badge = pygame.Rect(prompt_box.x + 14, prompt_box.y + 28, 0, 0)
            key_label = font_head.render(prompt_key, True, (255, 220, 80))
            badge_rect = key_label.get_rect(topleft=(prompt_box.x + 14, prompt_box.y + 28))
            badge_bg = badge_rect.inflate(12, 6)
            draw_panel(screen, badge_bg, (60, 50, 20), border=1, radius=6, shadow=False)
            screen.blit(key_label, (badge_rect.x + 6, badge_rect.y + 3))

            msg_surf = font_body.render(prompt_text, True, (210, 215, 230))
            screen.blit(msg_surf, (badge_bg.right + 12, prompt_box.y + 32))

            if moves_needed.get(prompt_action, 0) > 1:
                prog_w = 120
                prog_h = 6
                prog_x = prompt_box.right - prog_w - 14
                prog_y = prompt_box.y + 12
                pygame.draw.rect(screen, (30, 30, 50), (prog_x, prog_y, prog_w, prog_h), border_radius=3)
                fill = int(prog_w * min(move_count, moves_needed[prompt_action]) / moves_needed[prompt_action])
                pygame.draw.rect(screen, cc, (prog_x, prog_y, fill, prog_h), border_radius=3)

        # Prompt indicator
        if prompt_action != "done":
            blink = int(frame * 0.08) % 2
            if blink:
                arrow_x = prompt_box.right - 20
                arrow_y = prompt_box.centery
                pygame.draw.polygon(screen, (255, 220, 80),
                                   [(arrow_x, arrow_y - 5), (arrow_x + 8, arrow_y),
                                    (arrow_x, arrow_y + 5)])

        # ESC hint
        esc_hint = font_small.render("ESC: back to menu", True, (100, 100, 130))
        screen.blit(esc_hint, (SCREEN_W - esc_hint.get_width() - 15, 12))

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000
        frame += 1


settings_state = {"music_vol": 70, "sfx_vol": 80, "fullscreen": False}


def settings_screen(screen, font):
    from src.ui_sprites import load_arrow_key, _load
    from src.controller import get_connected_controllers
    import math

    font_title = pygame.font.Font(None, 48)
    font_label = pygame.font.Font(None, 30)
    font_small = pygame.font.Font(None, 22)
    font_pct = pygame.font.Font(None, 32)

    opts = ["MUSIC", "SFX", "FULLSCREEN"]
    sel = 0
    _clock = pygame.time.Clock()
    open_timer = 0.0

    bg_snap = screen.copy()
    sw0, sh0 = screen.get_size()

    sound_icon = _load("sound_icon.png", 2)
    settings_icon = _load("settings_icon.png", 3)

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    PURPLE_DARK = (45, 20, 80)
    PURPLE_MID = (90, 40, 150)
    PURPLE_LIGHT = (160, 80, 220)
    ORANGE = (255, 160, 40)
    YELLOW = (255, 220, 60)
    BAR_BG = (30, 15, 55)
    BAR_FILL_MUSIC = (60, 180, 255)
    BAR_FILL_SFX = (255, 140, 60)

    while True:
        dt = _clock.tick(60) / 1000.0
        open_timer = min(1.0, open_timer + dt * 4.0)
        pop = ease_out(open_timer)

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    fade(screen, _clock, "out")
                    return
                if event.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(opts)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(opts)
                elif event.key in (pygame.K_LEFT,):
                    if sel == 0:
                        settings_state["music_vol"] = max(0, settings_state["music_vol"] - 5)
                    elif sel == 1:
                        settings_state["sfx_vol"] = max(0, settings_state["sfx_vol"] - 5)
                elif event.key in (pygame.K_RIGHT,):
                    if sel == 0:
                        settings_state["music_vol"] = min(100, settings_state["music_vol"] + 5)
                    elif sel == 1:
                        settings_state["sfx_vol"] = min(100, settings_state["sfx_vol"] + 5)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if sel == 2:
                        settings_state["fullscreen"] = not settings_state["fullscreen"]
                        pygame.display.toggle_fullscreen()

        if _menu_ctrl.connected and not _mode_guard.blocked:
            if _menu_ctrl.cancel:
                fade(screen, _clock, "out")
                return
            if _menu_ctrl.up:
                sel = (sel - 1) % len(opts)
            elif _menu_ctrl.down:
                sel = (sel + 1) % len(opts)
            elif _menu_ctrl.left:
                if sel == 0:
                    settings_state["music_vol"] = max(0, settings_state["music_vol"] - 5)
                elif sel == 1:
                    settings_state["sfx_vol"] = max(0, settings_state["sfx_vol"] - 5)
            elif _menu_ctrl.right:
                if sel == 0:
                    settings_state["music_vol"] = min(100, settings_state["music_vol"] + 5)
                elif sel == 1:
                    settings_state["sfx_vol"] = min(100, settings_state["sfx_vol"] + 5)
            elif _menu_ctrl.confirm:
                if sel == 2:
                    settings_state["fullscreen"] = not settings_state["fullscreen"]
                    pygame.display.toggle_fullscreen()

        screen.blit(bg_snap, (0, 0))
        draw_vignette(screen, strength=int(150 * pop))

        sw = screen.get_width()
        sh = screen.get_height()

        panel_w = 520
        panel_h = 320
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (sw // 2, sh // 2)
        glass_alpha = int(180 * pop)
        if glass_alpha > 0:
            draw_glass_panel(screen, panel_rect, radius=18, alpha=glass_alpha, tint=(25, 15, 50))

        if pop < 0.05:
            pygame.display.flip()
            continue

        if settings_icon:
            si_y = panel_rect.top - 50
            screen.blit(settings_icon, (sw // 2 - settings_icon.get_width() // 2, si_y))

        outlined_text(screen, "SETTINGS", font_title, (sw // 2, panel_rect.top + 15),
                      YELLOW, outline_width=3, outline_color=(80, 40, 0), center=True)

        row_h = 60
        row_gap = 12
        rows_top = panel_rect.top + 65
        row_w = panel_w - 60

        for i, opt in enumerate(opts):
            is_sel = (i == sel)
            ry = rows_top + i * (row_h + row_gap)
            row_rect = pygame.Rect(panel_rect.x + 30, ry, row_w, row_h)

            if is_sel:
                sel_bg = pygame.Surface((row_w, row_h), pygame.SRCALPHA)
                pygame.draw.rect(sel_bg, (*PURPLE_MID, 200), sel_bg.get_rect(), border_radius=10)
                screen.blit(sel_bg, row_rect.topleft)
                pygame.draw.rect(screen, YELLOW, row_rect, 2, border_radius=10)
            else:
                unsel_bg = pygame.Surface((row_w, row_h), pygame.SRCALPHA)
                pygame.draw.rect(unsel_bg, (*PURPLE_DARK, 140), unsel_bg.get_rect(), border_radius=10)
                screen.blit(unsel_bg, row_rect.topleft)

            icon_x = row_rect.x + 15
            if sound_icon:
                sy = row_rect.centery - sound_icon.get_height() // 2
                screen.blit(sound_icon, (icon_x, sy))

            label_x = icon_x + 38
            label_color = YELLOW if is_sel else (200, 200, 220)
            label = font_label.render(opt, True, label_color)
            screen.blit(label, (label_x, row_rect.centery - label.get_height() // 2))

            if opt in ("MUSIC", "SFX"):
                bar_x = label_x + 100
                bar_w = 180
                bar_h = 14
                bar_y = row_rect.centery - bar_h // 2

                pygame.draw.rect(screen, BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=7)

                vol = settings_state["music_vol"] if opt == "MUSIC" else settings_state["sfx_vol"]
                fill = int(bar_w * vol / 100)
                fill_color = BAR_FILL_MUSIC if opt == "MUSIC" else BAR_FILL_SFX
                if fill > 0:
                    pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill, bar_h), border_radius=7)

                knob_x = bar_x + fill - 4
                knob_y = bar_y - 3
                pygame.draw.rect(screen, YELLOW, (knob_x, knob_y, 8, bar_h + 6), border_radius=3)

                pct = font_pct.render(f"{vol}", True, (220, 220, 240))
                screen.blit(pct, (bar_x + bar_w + 15, row_rect.centery - pct.get_height() // 2))

                if is_sel:
                    arrow_l = load_arrow_key("left", 2)
                    arrow_r = load_arrow_key("right", 2)
                    if arrow_l:
                        screen.blit(arrow_l, (bar_x - 30, row_rect.centery - arrow_l.get_height() // 2))
                    if arrow_r:
                        screen.blit(arrow_r, (bar_x + bar_w + 45, row_rect.centery - arrow_r.get_height() // 2))

            elif opt == "FULLSCREEN":
                state_text = "ON" if settings_state["fullscreen"] else "OFF"
                state_color = (80, 255, 80) if settings_state["fullscreen"] else (255, 80, 80)
                state_surf = font_pct.render(state_text, True, state_color)
                screen.blit(state_surf, (row_rect.right - 60, row_rect.centery - state_surf.get_height() // 2))

        prompt_alpha = int(140 + 80 * ((math.sin(open_timer * 4) + 1) / 2))
        prompt = font_small.render("UP/DOWN to select, LEFT/RIGHT to adjust, ESC to go back", True,
                                    (prompt_alpha, prompt_alpha, min(255, prompt_alpha + 30)))
        screen.blit(prompt, prompt.get_rect(center=(sw // 2, panel_rect.bottom + 25)))

        _mode_guard.draw(screen, font_title, font_small)

        pygame.display.flip()
    return screen


def pause_menu(screen, font):
    from src.ui_sprites import (load_resume_btn, load_restart_btn, load_exit_btn,
                                 load_settings_btn)
    from src.controller import get_connected_controllers
    import math

    font_btn = pygame.font.Font(None, 28)

    options = ["RESUME", "RESTART", "SETTINGS", "QUIT MATCH"]
    sel = 0
    _clock = pygame.time.Clock()
    open_timer = 0.0

    resume_n = load_resume_btn(False)
    resume_p = load_resume_btn(True)
    restart_n = load_restart_btn(False)
    restart_p = load_restart_btn(True)
    settings_n = load_settings_btn(False)
    settings_p = load_settings_btn(True)
    exit_n = load_exit_btn(False)
    exit_p = load_exit_btn(True)

    btn_sprites = [
        (resume_n, resume_p),
        (restart_n, restart_p),
        (settings_n, settings_p),
        (exit_n, exit_p),
    ]

    background_snapshot = screen.copy()

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    while True:
        dt = _clock.tick(60) / 1000.0
        open_timer = min(1.0, open_timer + dt * 4.0)
        pop = ease_out(open_timer)

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    return "resume"
                if event.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return options[sel].lower().replace(" ", "_")

        if _menu_ctrl.connected and not _mode_guard.blocked:
            if _menu_ctrl.cancel:
                return "resume"
            if _menu_ctrl.up:
                sel = (sel - 1) % len(options)
            elif _menu_ctrl.down:
                sel = (sel + 1) % len(options)
            elif _menu_ctrl.confirm:
                return options[sel].lower().replace(" ", "_")

        screen.blit(background_snapshot, (0, 0))
        draw_vignette(screen, strength=int(150 * pop))

        sw = screen.get_width()
        sh = screen.get_height()

        # Glass panel behind the menu, popping in on open
        panel_h = 60 + len(options) * 95
        panel_rect = pygame.Rect(0, 0, 320, panel_h)
        panel_rect.center = (sw // 2, sh // 2 - 10)
        glass_alpha = int(150 * pop)
        if glass_alpha > 0:
            draw_glass_panel(screen, panel_rect, radius=22, alpha=glass_alpha)

        if pop < 0.05:
            _mode_guard.draw(screen, font, font_btn)
            pygame.display.flip()
            continue

        # Title
        outlined_text(screen, "PAUSED", font, (sw // 2, sh // 2 - 120 * pop - 20), (255, 220, 80),
                      outline_width=3, outline_color=(70, 40, 5), center=True)

        # Sprite buttons with spacing and selection glow
        btn_gap = 15
        for i, (opt, (normal, pressed)) in enumerate(zip(options, btn_sprites)):
            is_sel = (i == sel)
            btn_img = pressed if is_sel else normal
            bw = btn_img.get_width() if btn_img else 240
            bh = btn_img.get_height() if btn_img else 50
            bx = sw // 2 - bw // 2
            by = sh // 2 - 80 + i * (bh + btn_gap)
            btn_rect = pygame.Rect(bx, by, bw, bh)
            if btn_img:
                screen.blit(btn_img, (bx, by))
            else:
                _draw_button(screen, btn_rect, opt, font_btn, is_sel)

        _mode_guard.draw(screen, font, font_btn)

        pygame.display.flip()


def victory_screen(screen, font, winner_char, winner_num, stats=None):
    from src.ui_sprites import (load_crown, load_restart_btn, load_exit_btn,
                                 load_mushroom, load_quit_btn)
    from src.controller import get_connected_controllers
    import math

    font_btn = pygame.font.Font(None, 28)
    font_title = pygame.font.Font(None, 52)
    font_stat = pygame.font.Font(None, 24)

    char_colors = {"mario": (220, 40, 40), "luigi": (40, 160, 40), "yoshi": (40, 140, 200),
                   "donkey_kong": (180, 100, 40)}
    winner_color = char_colors.get(winner_char, (255, 220, 80))

    options = ["REMATCH", "CHARACTER SELECT", "MAIN MENU"]
    sel = 0
    _clock = pygame.time.Clock()

    crown_img = load_crown(4)
    restart_n = load_restart_btn(False)
    restart_p = load_restart_btn(True)
    quit_n = load_quit_btn(False)
    quit_p = load_quit_btn(True)
    mushroom = load_mushroom(3)

    btn_sprites = [
        (restart_n, restart_p),
        (restart_n, restart_p),
        (quit_n, quit_p),
    ]

    background_snapshot = screen.copy()
    sw0, sh0 = screen.get_size()
    anim_timer = 0.0

    _has_ctrl = len(get_connected_controllers()) > 0
    _mode_guard = InputModeGuard("controller" if _has_ctrl else "keyboard")

    fade(screen, _clock, "in")

    while True:
        dt = _clock.tick(60) / 1000.0
        anim_timer += dt
        mouse_clicked = False
        mouse_pos = pygame.mouse.get_pos()

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if not _mode_guard.update(event, _menu_ctrl):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    fade(screen, _clock, "out")
                    return options[sel].lower().replace(" ", "_")

        if _menu_ctrl.connected and not _mode_guard.blocked:
            if _menu_ctrl.up:
                sel = (sel - 1) % len(options)
            elif _menu_ctrl.down:
                sel = (sel + 1) % len(options)
            elif _menu_ctrl.confirm:
                fade(screen, _clock, "out")
                return options[sel].lower().replace(" ", "_")

        # Dim overlay
        screen.blit(background_snapshot, (0, 0))
        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 110))
        screen.blit(dim, (0, 0))

        sw = screen.get_width()
        bounce = math.sin(anim_timer * 2.2) * 4

        # Crown with glow
        if crown_img:
            crown_rect = pygame.Rect(sw // 2 - crown_img.get_width() // 2, 40 + int(bounce),
                                      crown_img.get_width(), crown_img.get_height())
            screen.blit(crown_img, crown_rect.topleft)

        # Winner text
        win_text_str = f"P{winner_num} {winner_char.upper()} WINS!"
        outlined_text(screen, win_text_str, font_title, (sw // 2, 120 + int(bounce)),
                      winner_color, outline_width=3, outline_color=(0, 0, 0), center=True)

        # Mushroom decorations
        if mushroom:
            screen.blit(mushroom, (sw // 2 - 220, 110 + int(bounce)))
            screen.blit(mushroom, (sw // 2 + 190, 110 + int(bounce)))

        # Stats in a frosted glass panel
        if stats:
            stat_lines = [
                f"Damage Dealt: {stats.get('damage', 0):.0f}%",
                f"KOs: {stats.get('kos', 0)}",
                f"Time: {stats.get('time', 0)}s",
            ]
            panel_rect = pygame.Rect(0, 0, 260, 32 * len(stat_lines) + 24)
            panel_rect.center = (sw // 2, 180 + (len(stat_lines) - 1) * 16)
            draw_glass_panel(screen, panel_rect, radius=14, alpha=110)
            sy = panel_rect.top + 18
            for line in stat_lines:
                s = font_stat.render(line, True, (220, 225, 245))
                screen.blit(s, s.get_rect(center=(sw // 2, sy)))
                sy += 32

        # Buttons with spacing and selection glow
        btn_gap = 15
        btn_start_y = 300
        for i, opt in enumerate(options):
            normal, pressed = btn_sprites[i]
            is_sel = (i == sel)
            btn_img = pressed if is_sel else normal
            bw = btn_img.get_width() if btn_img else 240
            bh = btn_img.get_height() if btn_img else 45
            bx = sw // 2 - bw // 2
            by = btn_start_y + i * (bh + btn_gap)
            btn_rect = pygame.Rect(bx, by, bw, bh)
            if btn_img:
                screen.blit(btn_img, (bx, by))
            else:
                _draw_button(screen, btn_rect, opt, font_btn, is_sel)

        _mode_guard.draw(screen, font_title, font_btn)

        pygame.display.flip()


def _show_disconnect_screen(screen, font, message="CONNECTION LOST"):
    font_title = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 26)
    clock = pygame.time.Clock()
    timer = 0.0

    while timer < 3.0:
        dt = clock.tick(60) / 1000.0
        timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and timer > 0.5:
                return

        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        screen.blit(dim, (0, 0))

        sw, sh = screen.get_size()
        outlined_text(screen, message, font_title, (sw // 2, sh // 2 - 20),
                      (255, 80, 80), outline_width=3, outline_color=(0, 0, 0), center=True)

        hint = font_small.render("Press any key to continue", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh // 2 + 30)))

        pygame.display.flip()


def main():
    import os
    import time
    import subprocess

    ds4_path = None
    try:
        from setup_controller import find_ds4windows
        ds4_path = find_ds4windows()
    except Exception:
        pass

    ds4_running = False
    if ds4_path:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq DS4Windows.exe"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            ds4_running = "DS4Windows.exe" in result.stdout
        except Exception:
            pass

        if not ds4_running:
            exe = os.path.join(ds4_path, "DS4Windows.exe")
            if os.path.exists(exe):
                subprocess.Popen([exe], cwd=ds4_path,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                time.sleep(6)
                try:
                    result = subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq DS4Windows.exe"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    ds4_running = "DS4Windows.exe" in result.stdout
                except Exception:
                    pass

    pygame.init()
    pygame.joystick.init()

    _sdl = None
    if sys.platform == "win32":
        try:
            _sdl = ctypes.CDLL("SDL2.dll")
            _sdl.SDL_EventState.argtypes = [ctypes.c_uint32, ctypes.c_int]
            _sdl.SDL_EventState.restype = ctypes.c_uint8
            _sdl.SDL_PollEvent.argtypes = [ctypes.c_void_p]
            _sdl.SDL_PollEvent.restype = ctypes.c_int
            _sdl.SDL_FlushEvents.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
            _sdl.SDL_FlushEvents.restype = None

            _sdl.SDL_FlushEvents(0x600, 0x606)
            _sdl.SDL_EventState(0x605, 0)  # JOYDEVICEADDED = SDL_DISABLE
            _sdl.SDL_EventState(0x606, 0)  # JOYDEVICEREMOVED = SDL_DISABLE
        except OSError:
            _sdl = None

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("World 1-1")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    mario_sprites = SpriteLoader("mario_assets", MARIO_FILE_MAP, scale=SCALE)
    luigi_sprites = SpriteLoader("luigi_assets", LUIGI_FILE_MAP, scale=SCALE)
    yoshi_sprites = SpriteLoader("Yoshi_assets", YOSHI_FILE_MAP, scale=SCALE, target_height=38, max_width_ratio=1.0)
    dk_sprites = SpriteLoader("Donkey_Kong_assets", DONKEY_KONG_FILE_MAP, scale=SCALE, flip_x=False)

    sprite_lookup = {"mario": mario_sprites, "luigi": luigi_sprites, "yoshi": yoshi_sprites, "donkey_kong": dk_sprites}

    while True:
        title_screen(screen, clock)
        mode, ai_difficulty = mode_select(screen, font)
        if mode is None:
            continue
        if mode == "tutorial":
            result = tutorial_screen(screen, font)
            if result and result[0]:
                char_name, use_controller = result
                tutorial_sandbox(screen, clock, font, sprite_lookup, char_name, use_controller=use_controller)
            continue
        if mode == "settings":
            settings_screen(screen, font)
            continue
        if mode == "online":
            role, session, lobby_cl = online_lobby(screen, font)
            if session is None:
                continue
            while True:
                char1, char2 = character_select(screen, font, ai_mode=False,
                                                lobby_client=lobby_cl, is_online=True,
                                                is_host=(role == "host"))
                if char1 is None:
                    session.close()
                    break
                stage = stage_select(screen, font)
                if stage is None:
                    continue
                session.send_character_select(char1)
                opp_char = session.recv_character_select()
                if opp_char is None:
                    session.close()
                    break
                stages = ["world1-1", "factory"]
                stage_idx = stages.index(stage) if stage in stages else 0
                session.send_stage_select(stage_idx)
                opp_stage_idx = session.recv_stage_select()
                if opp_stage_idx is None or opp_stage_idx < 0:
                    session.close()
                    break
                if role == "join":
                    stage = stages[opp_stage_idx] if opp_stage_idx < len(stages) else stage
                result = _run_match(screen, clock, font, sprite_lookup, char1, opp_char,
                                    False, None, stage, network_session=session)
                session.close()
                if result == "restart":
                    continue
                elif result == "character_select":
                    continue
                else:
                    break
            continue
        ai_mode = mode == "ai"

        controller_assignment = (0, 1)
        if not ai_mode:
            if _sdl:
                _sdl.SDL_EventState(0x605, 1)  # re-enable JOYDEVICEADDED
                _sdl.SDL_EventState(0x606, 1)  # re-enable JOYDEVICEREMOVED
            result = controller_select(screen, font)
            if result[0] is None:
                continue
            controller_assignment = result

        while True:
            char1, char2 = character_select(screen, font, ai_mode=ai_mode)
            if char1 is None:
                break
            stage = stage_select(screen, font)
            if stage is None:
                continue
            result = _run_match(screen, clock, font, sprite_lookup, char1, char2, ai_mode, ai_difficulty, stage, controller_assignment)
            if result == "restart":
                continue
            elif result == "character_select":
                continue
            elif result == "main_menu":
                continue
            else:
                return

    pygame.quit()


def controller_select(screen, font):
    from src.controller import get_connected_controllers, handle_controller_events, open_bluetooth_settings
    import math

    font_title = pygame.font.Font(None, 42)
    font_btn = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 22)
    font_tiny = pygame.font.Font(None, 18)

    GOLD = (255, 196, 20)
    BRICK = (198, 100, 44)
    GREEN = (46, 138, 60)

    _clock = pygame.time.Clock()
    pulse_timer = 0.0

    ctrls = get_connected_controllers()
    p1_input = 1 if len(ctrls) > 0 else 0
    p2_input = 0
    sel = 0
    done = False
    pairing_mode = False
    pair_timer = 0.0
    need_rescan = False

    fade(screen, _clock, "in")

    while True:
        dt = _clock.tick(60) / 1000.0
        pulse_timer += dt

        if need_rescan:
            need_rescan = False

        _menu_ctrl.refresh()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            ctrl_event = handle_controller_events(event)
            if ctrl_event:
                action, idx, name = ctrl_event
                if action == "connected":
                    need_rescan = True

            if event.type == pygame.KEYDOWN:
                if pairing_mode:
                    if event.key == pygame.K_ESCAPE:
                        pairing_mode = False
                        need_rescan = True
                    continue

                if event.key == pygame.K_ESCAPE:
                    fade(screen, _clock, "out")
                    return None, None

                if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % 4
                elif event.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % 4
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if sel == 0:
                        p1_input = max(0, p1_input - 1)
                    elif sel == 1:
                        p2_input = max(0, p2_input - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    num_ctrls = len(get_connected_controllers())
                    max_input = num_ctrls
                    if sel == 0:
                        p1_input = min(max_input, p1_input + 1)
                    elif sel == 1:
                        p2_input = min(max_input, p2_input + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if sel == 2:
                        open_bluetooth_settings()
                        pairing_mode = True
                        pair_timer = 10.0
                    elif sel == 3:
                        done = True

        if _menu_ctrl.connected:
            if pairing_mode:
                if _menu_ctrl.cancel:
                    pairing_mode = False
                    need_rescan = True
            else:
                if _menu_ctrl.cancel:
                    fade(screen, _clock, "out")
                    return None, None
                if _menu_ctrl.up:
                    sel = (sel - 1) % 4
                elif _menu_ctrl.down:
                    sel = (sel + 1) % 4
                elif _menu_ctrl.left:
                    if sel == 0:
                        p1_input = max(0, p1_input - 1)
                    elif sel == 1:
                        p2_input = max(0, p2_input - 1)
                elif _menu_ctrl.right:
                    num_ctrls = len(get_connected_controllers())
                    max_input = num_ctrls
                    if sel == 0:
                        p1_input = min(max_input, p1_input + 1)
                    elif sel == 1:
                        p2_input = min(max_input, p2_input + 1)
                elif _menu_ctrl.confirm:
                    if sel == 2:
                        open_bluetooth_settings()
                        pairing_mode = True
                        pair_timer = 10.0
                    elif sel == 3:
                        done = True

        draw_gradient_bg(screen)
        sw, sh = screen.get_size()

        panel = pygame.Rect(0, 0, 560, 400)
        panel.center = (sw // 2, sh // 2)
        draw_glass_panel(screen, panel, radius=22)

        outlined_text(screen, "CONTROLLER SETUP", font_title, (sw // 2, sh // 2 - 165), GOLD,
                      outline_width=3, outline_color=(70, 40, 5), center=True)

        controllers = get_connected_controllers()
        num_controllers = len(controllers)

        input_labels = ["KEYBOARD"]
        for _, name, is_ps4 in controllers:
            input_labels.append("CONTROLLER")
        while len(input_labels) < 3:
            input_labels.append("---")

        players = [
            ("PLAYER 1", p1_input),
            ("PLAYER 2", p2_input),
        ]

        for pi, (label, cur_idx) in enumerate(players):
            py = sh // 2 - 80 + pi * 80
            color = (220, 80, 80) if pi == 0 else (80, 130, 220)
            outlined_text(screen, label, font_btn, (sw // 2 - 200, py), color,
                          outline_width=2, outline_color=(20, 10, 5), center=False)

            is_sel = (sel == pi)
            chip_w = 260
            chip_rect = pygame.Rect(sw // 2 - 60, py - 16, chip_w, 32)
            draw_angled_panel(screen, chip_rect, GOLD if is_sel else (40, 40, 60),
                               border_color=GOLD, skew=8, border_width=3, selected=is_sel)

            display = input_labels[cur_idx] if cur_idx < len(input_labels) else "NONE"
            outlined_text(screen, display, font_small, chip_rect.center, (255, 255, 255),
                          outline_width=1, outline_color=(10, 10, 5), center=True)

            arrow_l = font_btn.render("<", True, GOLD if is_sel else (100, 100, 120))
            arrow_r = font_btn.render(">", True, GOLD if is_sel else (100, 100, 120))
            screen.blit(arrow_l, (chip_rect.left - 22, chip_rect.centery - 10))
            screen.blit(arrow_r, (chip_rect.right + 8, chip_rect.centery - 10))

        btn_y = sh // 2 + 110
        pair_rect = pygame.Rect(sw // 2 - 130, btn_y - 16, 260, 32)
        is_sel = (sel == 2)
        draw_angled_panel(screen, pair_rect, GREEN if is_sel else (40, 60, 40),
                           border_color=GOLD, skew=8, border_width=3, selected=is_sel)
        outlined_text(screen, "PAIR BLUETOOTH CONTROLLER", font_small, pair_rect.center, (255, 255, 255),
                      outline_width=1, outline_color=(10, 10, 5), center=True)

        btn_y2 = btn_y + 50
        start_rect = pygame.Rect(sw // 2 - 80, btn_y2 - 16, 160, 32)
        is_sel = (sel == 3)
        draw_angled_panel(screen, start_rect, GOLD if is_sel else (60, 50, 20),
                           border_color=GOLD, skew=8, border_width=3, selected=is_sel)
        outlined_text(screen, "FIGHT!", font_btn, start_rect.center, (255, 255, 255),
                      outline_width=2, outline_color=(10, 10, 5), center=True)

        prompt_alpha = min(255, int(80 + 100 * ((math.sin(pulse_timer * 3) + 1) / 2)))
        prompt = font_tiny.render("ARROWS to change  |  TAB to switch row  |  ENTER to confirm  |  ESC back", True,
                                   (prompt_alpha, prompt_alpha, min(255, prompt_alpha + 40)))
        screen.blit(prompt, prompt.get_rect(center=(sw // 2, sh // 2 + 170)))

        if num_controllers == 0:
            no_ctrl = font_tiny.render("No controllers found - connect via USB or pair Bluetooth", True, (200, 120, 120))
            screen.blit(no_ctrl, no_ctrl.get_rect(center=(sw // 2, sh // 2 - 120)))
        else:
            ctrl_info = font_tiny.render("{} controller(s) detected".format(num_controllers), True, (120, 200, 120))
            screen.blit(ctrl_info, ctrl_info.get_rect(center=(sw // 2, sh // 2 - 120)))

        if pairing_mode and pair_timer > 0:
            pair_timer -= dt
            pair_panel = pygame.Rect(0, 0, 460, 140)
            pair_panel.center = (sw // 2, sh // 2)
            draw_glass_panel(screen, pair_panel, radius=16)

            title = font_btn.render("Bluetooth Pairing", True, GOLD)
            screen.blit(title, title.get_rect(center=(sw // 2, sh // 2 - 48)))

            lines = [
                "1. Hold PS button 3 sec until light flashes",
                "2. Windows Bluetooth settings opened",
                "3. Click 'Add device' -> 'Bluetooth' -> 'Wireless Controller'",
                "4. Press ESC here when done",
            ]
            for i, line in enumerate(lines):
                color = (180, 255, 180) if i == 3 else (200, 200, 220)
                surf = font_tiny.render(line, True, color)
                screen.blit(surf, surf.get_rect(center=(sw // 2, sh // 2 - 20 + i * 20)))

        if done:
            def resolve_joystick_index(input_pos):
                if input_pos == 0:
                    return -1
                ctrls = get_connected_controllers()
                if input_pos - 1 < len(ctrls):
                    return ctrls[input_pos - 1][0]
                return -1
            p1_joy = resolve_joystick_index(p1_input)
            p2_joy = resolve_joystick_index(p2_input)
            fade(screen, _clock, "out")
            return p1_joy, p2_joy

        pygame.display.flip()


def online_lobby(screen, font):
    import os
    from src.network import NetworkSession, DEFAULT_PORT
    from src.server_comm import LobbyClient
    import threading

    font_title = pygame.font.Font(None, 42)
    font_btn = pygame.font.Font(None, 30)
    font_small = pygame.font.Font(None, 22)
    font_tiny = pygame.font.Font(None, 18)

    GOLD = (255, 196, 20)
    OCEAN = (40, 120, 180)
    BRICK = (198, 100, 44)
    GREEN = (46, 138, 60)
    GRAY = (120, 120, 150)

    LOBBY_URL = os.environ.get("WORLD11_LOBBY_URL", "https://world11-lobby.onrender.com")

    state = "connecting"
    sel = 0
    rooms = []
    selected_room = None
    room_name_input = ""
    status_msg = "Connecting to lobby server..."
    session = None
    lobby_client = None
    connect_result = [None]
    cursor_timer = 0.0
    refresh_timer = 0.0
    refresh_interval = 3.0
    server_info = None
    error_msg = ""

    _clock = pygame.time.Clock()
    fade(screen, _clock, "in")

    def check_server_thread():
        nonlocal server_info, state, error_msg
        client = LobbyClient(LOBBY_URL)
        info = client.check_server()
        if info:
            server_info = info
            lobby_client_ref[0] = client
            state = "browse"
        else:
            error_msg = client.last_error or "Server unreachable"
            state = "server_error"

    lobby_client_ref = [None]

    def refresh_rooms_thread():
        nonlocal rooms
        c = lobby_client_ref[0]
        if c:
            rooms = c.list_rooms()

    def host_wait_thread():
        connect_result[0] = session.wait_for_connection(timeout=30.0)

    def join_connect_thread(host, port):
        connect_result[0] = session.join(host, port)

    threading.Thread(target=check_server_thread, daemon=True).start()

    while True:
        dt = _clock.tick(60) / 1000.0
        cursor_timer += dt
        refresh_timer += dt

        if state == "browse" and refresh_timer >= refresh_interval:
            refresh_timer = 0.0
            threading.Thread(target=refresh_rooms_thread, daemon=True).start()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if lobby_client_ref[0]:
                    lobby_client_ref[0].close()
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "browse":
                        if lobby_client_ref[0]:
                            lobby_client_ref[0].close()
                        fade(screen, _clock, "out")
                        return None, None, None
                    elif state == "create_name":
                        state = "browse"
                    elif state in ("host_waiting", "join_connecting"):
                        if session:
                            session.close()
                            session = None
                        if lobby_client_ref[0] and lobby_client_ref[0].room_id:
                            lobby_client_ref[0].delete_room()
                        state = "browse"
                    elif state == "server_error":
                        state = "browse"

                elif state == "browse":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        sel = (sel - 1) % max(1, len(rooms) + 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        sel = (sel + 1) % max(1, len(rooms) + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if sel == 0:
                            state = "create_name"
                            room_name_input = ""
                        elif sel <= len(rooms):
                            selected_room = rooms[sel - 1]
                            state = "join_confirm"
                    elif event.key == pygame.K_r:
                        refresh_timer = 0.0
                        threading.Thread(target=refresh_rooms_thread, daemon=True).start()

                elif state == "create_name":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE) and room_name_input:
                        lc = LobbyClient(LOBBY_URL)
                        session = NetworkSession()
                        addr = session.host()
                        host_port = int(addr.split(":")[1]) if ":" in addr else DEFAULT_PORT
                        result = lc.create_room(
                            name=room_name_input,
                            host_port=host_port,
                            host_name="Host",
                        )
                        if result:
                            lobby_client_ref[0] = lc
                            state = "host_waiting"
                            status_msg = f"Hosting: {room_name_input}\nRoom ID: {result['id']}\nWaiting for opponent..."
                            connect_result[0] = None
                            threading.Thread(target=host_wait_thread, daemon=True).start()
                        else:
                            state = "browse"
                            error_msg = "Failed to create room"
                    elif event.key == pygame.K_BACKSPACE:
                        room_name_input = room_name_input[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(room_name_input) < 20:
                        room_name_input += event.unicode

                elif state == "join_confirm":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        room = selected_room
                        if room:
                            session = NetworkSession()
                            status_msg = f"Connecting to {room['host_name']}..."
                            state = "join_connecting"
                            connect_result[0] = None
                            if lobby_client_ref[0]:
                                lobby_client_ref[0].join_room(room["id"])
                            threading.Thread(
                                target=join_connect_thread,
                                args=(room["host_ip"], room["host_port"]),
                                daemon=True
                            ).start()
                    elif event.key == pygame.K_ESCAPE:
                        state = "browse"

        if state in ("host_waiting", "join_connecting") and connect_result[0] is True:
            state = "ready"
            status_msg = "Connected!"
        elif state in ("host_waiting", "join_connecting") and connect_result[0] is False:
            state = "connect_failed"
            status_msg = "Connection failed"

        if state == "ready":
            fade(screen, _clock, "out")
            role = "host" if session.is_hosting else "join"
            return role, session, lobby_client_ref[0]

        if state == "connect_failed":
            if session:
                session.close()
                session = None
            if lobby_client_ref[0] and lobby_client_ref[0].room_id:
                lobby_client_ref[0].delete_room()
            state = "browse"
            error_msg = ""
            threading.Thread(target=refresh_rooms_thread, daemon=True).start()

        draw_gradient_bg(screen)
        sw, sh = screen.get_size()

        panel_rect = pygame.Rect(0, 0, 600, 480)
        panel_rect.center = (sw // 2, sh // 2)
        draw_glass_panel(screen, panel_rect, radius=22)

        outlined_text(screen, "ONLINE LOBBY", font_title, (sw // 2, panel_rect.y + 30),
                      GOLD, outline_width=3, outline_color=(70, 40, 5), center=True)

        if state == "connecting":
            spinner_chars = ["|", "/", "-", "\\"]
            spinner = spinner_chars[int(cursor_timer * 4) % 4]
            surf = font_small.render(f"{spinner} Connecting to lobby server...", True, (200, 200, 220))
            screen.blit(surf, surf.get_rect(center=(sw // 2, sh // 2)))

        elif state == "server_error":
            err_surf = font_small.render(f"Server Error: {error_msg}", True, (255, 100, 100))
            screen.blit(err_surf, err_surf.get_rect(center=(sw // 2, sh // 2 - 20)))
            hint = font_tiny.render("Press ESC to go back", True, GRAY)
            screen.blit(hint, hint.get_rect(center=(sw // 2, sh // 2 + 20)))

        elif state == "browse":
            create_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 60, 120, 40)
            is_sel = (sel == 0)
            draw_angled_panel(screen, create_rect, GREEN if is_sel else (40, 60, 40),
                              border_color=GOLD, skew=6, border_width=2, selected=is_sel)
            outlined_text(screen, "+ CREATE", font_small, create_rect.center, (255, 255, 255),
                          outline_width=1, outline_color=(10, 10, 5), center=True)

            refresh_rect = pygame.Rect(panel_rect.right - 140, panel_rect.y + 60, 100, 40)
            draw_angled_panel(screen, refresh_rect, OCEAN, border_color=GOLD, skew=6, border_width=2, selected=False)
            outlined_text(screen, "R:REFRESH", font_tiny, refresh_rect.center, (255, 255, 255),
                          outline_width=1, outline_color=(10, 10, 5), center=True)

            room_y = panel_rect.y + 115
            room_h = 55
            max_visible = 6

            if not rooms:
                empty_surf = font_small.render("No rooms available. Create one!", True, GRAY)
                screen.blit(empty_surf, empty_surf.get_rect(center=(sw // 2, room_y + 40)))
            else:
                start_idx = max(0, sel - max_visible)
                visible = rooms[start_idx:start_idx + max_visible]
                for i, room in enumerate(visible):
                    actual_idx = start_idx + i + 1
                    is_sel = (actual_idx == sel)
                    ry = room_y + i * (room_h + 4)
                    room_rect = pygame.Rect(panel_rect.x + 20, ry, panel_rect.w - 40, room_h)

                    if is_sel:
                        draw_angled_panel(screen, room_rect, (60, 60, 80),
                                          border_color=GOLD, skew=4, border_width=2, selected=True)
                    else:
                        pygame.draw.rect(screen, (30, 30, 50), room_rect, border_radius=6)
                        pygame.draw.rect(screen, (60, 60, 80), room_rect, 1, border_radius=6)

                    name_surf = font_btn.render(room.get("name", "Unknown"), True,
                                                GOLD if is_sel else (220, 220, 240))
                    screen.blit(name_surf, (room_rect.x + 12, room_rect.y + 8))

                    info_text = f"{room.get('host_name', 'Host')} | {room.get('players', 1)}/{room.get('max_players', 2)} players"
                    info_surf = font_tiny.render(info_text, True, GRAY)
                    screen.blit(info_surf, (room_rect.x + 12, room_rect.y + 32))

                    age = room.get("age", 0)
                    age_text = f"{age}s ago"
                    age_surf = font_tiny.render(age_text, True, (100, 100, 120))
                    screen.blit(age_surf, (room_rect.right - age_surf.get_width() - 10, room_rect.y + 8))

                if len(rooms) > max_visible:
                    scroll_text = f"{start_idx + 1}-{min(start_idx + max_visible, len(rooms))} of {len(rooms)}"
                    scroll_surf = font_tiny.render(scroll_text, True, GRAY)
                    screen.blit(scroll_surf, scroll_surf.get_rect(center=(sw // 2, panel_rect.bottom - 50)))

        elif state == "create_name":
            prompt = font_small.render("ROOM NAME:", True, GOLD)
            screen.blit(prompt, prompt.get_rect(center=(sw // 2, panel_rect.y + 100)))

            field_rect = pygame.Rect(sw // 2 - 150, panel_rect.y + 130, 300, 40)
            pygame.draw.rect(screen, (20, 20, 40), field_rect, border_radius=6)
            border_color = GOLD if int(cursor_timer * 2) % 2 else (100, 100, 120)
            pygame.draw.rect(screen, border_color, field_rect, 2, border_radius=6)

            display_text = room_name_input + ("|" if int(cursor_timer * 3) % 2 else "")
            name_surf = font_btn.render(display_text, True, (255, 255, 255))
            screen.blit(name_surf, (field_rect.x + 10, field_rect.centery - name_surf.get_height() // 2))

            hint = font_tiny.render("ENTER to create  |  ESC to cancel", True, GRAY)
            screen.blit(hint, hint.get_rect(center=(sw // 2, panel_rect.y + 200)))

        elif state == "join_confirm":
            room = selected_room
            if room:
                prompt = font_small.render(f"Join {room.get('name', 'Room')}?", True, GOLD)
                screen.blit(prompt, prompt.get_rect(center=(sw // 2, panel_rect.y + 100)))

                info_lines = [
                    f"Host: {room.get('host_name', 'Host')}",
                    f"Players: {room.get('players', 1)}/{room.get('max_players', 2)}",
                ]
                for i, line in enumerate(info_lines):
                    surf = font_small.render(line, True, (200, 200, 220))
                    screen.blit(surf, surf.get_rect(center=(sw // 2, panel_rect.y + 140 + i * 25)))

                hint = font_small.render("ENTER to join  |  ESC to cancel", True, GRAY)
                screen.blit(hint, hint.get_rect(center=(sw // 2, panel_rect.y + 220)))

        elif state in ("host_waiting", "join_connecting"):
            spinner_chars = ["|", "/", "-", "\\"]
            spinner = spinner_chars[int(cursor_timer * 4) % 4]
            lines = status_msg.split("\n")
            for i, line in enumerate(lines):
                surf = font_small.render(f"{spinner} {line}" if i == 0 else line, True, (200, 200, 220))
                screen.blit(surf, surf.get_rect(center=(sw // 2, panel_rect.y + 120 + i * 30)))

        if state != "connecting":
            server_text = f"Server: {LOBBY_URL}"
            server_surf = font_tiny.render(server_text, True, GRAY)
            screen.blit(server_surf, (panel_rect.x + 10, panel_rect.bottom - 25))

            prompt_text = "ESC: back  |  R: refresh" if state == "browse" else "ESC: cancel"
            prompt = font_small.render(prompt_text, True, GRAY)
            screen.blit(prompt, prompt.get_rect(center=(sw // 2, panel_rect.bottom - 10)))

        if error_msg and state != "server_error":
            err_surf = font_tiny.render(error_msg, True, (255, 100, 100))
            screen.blit(err_surf, err_surf.get_rect(center=(sw // 2, panel_rect.bottom - 40)))

        pygame.display.flip()


def _run_match(screen, clock, font, sprite_lookup, char1, char2, ai_mode, ai_difficulty, stage=None, controller_assignment=None, network_session=None):
    if stage is None:
        stage = {"name": "World 1-1", "path": "assets/levels/world1-1.json", "tileset": "assets/tiles/tileset.png",
                 "hazards": {"kamek": True, "bobombs": False, "grrrols": False, "pipe_spawns": False, "npcs": True}}
    tileset_surf = pygame.image.load(stage["tileset"]).convert()
    tilemap = Tilemap(stage["path"], tileset_surf)
    solid = tilemap.solid_rects()
    platforms = tilemap.platform_rects()
    bg = Background()
    hazards = stage.get("hazards", {})

    LEVEL_W = tilemap.level_w or SCREEN_W
    LEVEL_H = tilemap.level_h or SCREEN_H
    camera = Camera(LEVEL_W, LEVEL_H)

    ground_y = 33 * TILE_SIZE * MAP_SCALE
    is_factory = "factory" in stage["path"]
    factory_bg = FactoryBackground(LEVEL_W, ground_y, tilemap.tile_px) if is_factory else None
    char_hit_heights = {"mario": 44, "luigi": 32, "yoshi": 32, "donkey_kong": 50}
    spawn_y1 = ground_y - char_hit_heights.get(char1, 44)
    spawn_y2 = ground_y - char_hit_heights.get(char2, 32)
    player1 = Player(150, spawn_y1, sprite_lookup[char1], character=char1, controls=CTRL_P1)
    player2 = Player(LEVEL_W - 150, spawn_y2, sprite_lookup[char2], character=char2, controls=CTRL_P2)
    player1.animator.set_state("start_idle", force=True)
    player2.animator.set_state("start_idle", force=True)
    player1.facing = 1
    player2.facing = -1

    # --- Gamepad setup ---
    num_joysticks = pygame.joystick.get_count()
    if controller_assignment:
        p1_joy_idx, p2_joy_idx = controller_assignment
        gamepad1 = GamepadInput(p1_joy_idx, ctrl=CTRL_P1) if p1_joy_idx >= 0 and num_joysticks > p1_joy_idx else None
        if ai_mode:
            gamepad2 = None
        else:
            gamepad2 = GamepadInput(p2_joy_idx, ctrl=CTRL_P2) if p2_joy_idx >= 0 and num_joysticks > p2_joy_idx else None
    else:
        gamepad1 = GamepadInput(0, ctrl=CTRL_P1) if num_joysticks >= 1 else None
        gamepad2 = GamepadInput(1, ctrl=CTRL_P2) if num_joysticks >= 2 else None

    p1_mouse_input = MouseAwareKeys(CTRL_P1)

    ai_controller = None
    if ai_mode:
        ai_controller = AIController(player2, player1, difficulty=ai_difficulty, controls=CTRL_P2)
        ai_controller.set_stage(LEVEL_W, BLAST_ZONE_MARGIN_SIDE, solid=solid)

    particles = ParticleSystem()
    player1.particles = particles
    player2.particles = particles
    shake = ScreenShake()
    shells = []
    eggs = []
    projectiles = []

    grrrol_frames = load_grrrol_sprites()
    grrrols = []
    grrrol_spawn_timer = 0
    grrrol_next_spawn = random.randint(300, 720)

    bobomb_sprites = load_bobomb_sprites()
    bobombs = []
    bobomb_spawn_timer = 0
    bobomb_next_spawn = random.randint(420, 900)

    kamek_sprites = load_kamek_sprites()
    kameks = []
    kamek_spawn_timer = 0
    kamek_next_spawn = random.randint(600, 1080)
    magic_projectiles = []

    blast_zone_frames = []
    for i in range(1, 4):
        path = f"blast_zone_explosion({i}).png"
        blast_zone_frames.append(pygame.image.load(path).convert_alpha())
    blast_zone_effects = []

    goomba_sprites = load_goomba_sprites()
    koopa_sprites = load_koopa_sprites()
    shyguy_sprites = load_shyguy_sprites()
    buzzy_beetle_sprites = load_buzzy_beetle_sprites()
    bullet_bill_sprites = load_bullet_bill_sprites()
    npcs = []
    npc_spawn_timer = 0
    npc_next_spawn = random.randint(60, 120)
    pipe_positions = [15, 30, 42]
    pipe_spawner_timer = 0
    bullet_bill_spawn_timer = 0
    bullet_bill_next_spawn = random.randint(180, 360)
    bullet_bills = []
    bill_blasters = []
    if "factory" in stage["path"]:
        blaster_positions = [(2, 26, 1), (55, 26, -1)]
        for bx, by, bfacing in blaster_positions:
            world_bx = bx * tilemap.tile_px
            world_by = by * tilemap.tile_px
            bill_blasters.append(BillBlaster(world_bx, world_by, bullet_bill_sprites, facing=bfacing))

    # --- Countdown ---
    countdown_timer = 180  # 3 seconds at 60fps
    countdown_done = False

    # --- Game over ---
    game_over = False
    frame = 0
    winner = None
    victory_timer = 0
    death_zoom_timer = 0
    death_zoom_pos = (0, 0)

    hud = MarioHUD()

    count_font = pygame.font.Font(None, 96)
    go_font = pygame.font.Font(None, 80)
    combo_font = pygame.font.Font(None, 24)
    font_tiny = pygame.font.Font(None, 18)

    # --- Network setup (online mode) ---
    online_mode = network_session is not None
    net_proxy_p1 = None
    net_proxy_p2 = None
    frame_ref = [0]
    ping_timer = 0.0
    ping_interval = 2.0
    connection_quality = ""
    lag_indicator_timer = 0.0
    if online_mode:
        from src.network import NetworkKeyProxy, STATE_SYNC_INTERVAL, compute_state_hash
        net_proxy_p1 = NetworkKeyProxy(
            gamepad1 if gamepad1 else p1_mouse_input,
            network_session, is_local_player=True,
            frame_ref=frame_ref, controls=CTRL_P1
        )
        net_proxy_p2 = NetworkKeyProxy(
            keys, network_session, is_local_player=False,
            frame_ref=frame_ref, controls=CTRL_P2
        )

    dt = 1.0 / FPS

    while True:
        if online_mode and not network_session.is_alive():
            _show_disconnect_screen(screen, font)
            if network_session:
                network_session.close()
            return "main_menu"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    settings_state["fullscreen"] = not settings_state["fullscreen"]
                    pygame.display.toggle_fullscreen()
                if event.key in (pygame.K_ESCAPE, pygame.K_p) and not game_over and countdown_done:
                    result = pause_menu(screen, font)
                    if result == "quit_match":
                        return "main_menu"
                    elif result == "restart":
                        return "restart"
                    elif result == "settings":
                        new_screen = settings_screen(screen, font)
                        if new_screen is not None:
                            screen = new_screen

            ctrl_event = handle_controller_events(event)
            if ctrl_event:
                action, idx, name = ctrl_event
                if action == "connected":
                    if gamepad1 is None:
                        gamepad1 = GamepadInput(idx, ctrl=CTRL_P1)
                    elif gamepad2 is None:
                        gamepad2 = GamepadInput(idx, ctrl=CTRL_P2)
                elif action == "disconnected":
                    if gamepad1 and gamepad1.index == idx:
                        gamepad1 = None
                    elif gamepad2 and gamepad2.index == idx:
                        gamepad2 = None

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        p1_mouse_input.refresh(keys, mouse_buttons)
        if gamepad1:
            if gamepad1.alive:
                gamepad1.refresh()
            else:
                gamepad1 = None
        if gamepad2:
            if gamepad2.alive:
                gamepad2.refresh()
            else:
                gamepad2 = None

        # --- Hitlag freeze: decrement first, then check if frozen ---
        for player in (player1, player2):
            if player.hitlag > 0:
                player.hitlag -= 1

        frozen = player1.hitlag > 0 or player2.hitlag > 0 or death_zoom_timer > 0

        # --- Countdown ---
        if not countdown_done:
            countdown_timer -= 1
            if countdown_timer <= 0:
                countdown_done = True
                for p in (player1, player2):
                    p.vx_int = 0
                    p.vy_int = 0
                    p.vx_ext = 0
                    p.vy_ext = 0
                    p.on_ground = True
                    p.animator.set_state("idle", force=True)

        # --- Death zoom countdown ---
        if death_zoom_timer > 0:
            death_zoom_timer -= 1

        for player in (player1, player2):
            if player.is_dead:
                if not countdown_done:
                    if death_zoom_timer <= 0:
                        player.respawn_timer -= 1
                else:
                    player.apply_gravity()
                    player.rect.y += int(player.vy_int + player.vy_ext)
                    player.pos.y = float(player.rect.y)
                    if death_zoom_timer <= 0:
                        player.respawn_timer -= 1
                if player.hearts <= 0:
                    if not game_over:
                        game_over = True
                        winner = player2 if player == player1 else player1
                        victory_timer = 0
                elif player.respawn_timer <= 0:
                    respawn_x = (LEVEL_W // 2) - 50 if player == player1 else (LEVEL_W // 2) + 50
                    player.respawn(respawn_x, 200)
            elif not frozen and countdown_done and not game_over:
                if online_mode:
                    p1_input = gamepad1 if gamepad1 else p1_mouse_input
                    net_proxy_p1.refresh()
                    net_proxy_p1.send_local_input(frame)
                    player1.update(p1_input, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)
                    net_proxy_p2.refresh()
                    player2.update(net_proxy_p2, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)
                elif ai_controller and player == player2:
                    ai_controller.update(keys, frame)
                    ai_proxy = AIKeyProxy(keys, ai_controller, CTRL_P2)
                    player.update(ai_proxy, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)
                elif player == player1:
                    p1_input = gamepad1 if gamepad1 else p1_mouse_input
                    player.update(p1_input, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)
                else:
                    p2_input = gamepad2 if gamepad2 else keys
                    player.update(p2_input, solid, dt, platforms, level_w=LEVEL_W, level_h=LEVEL_H)

        # --- Victory state ---
        if game_over:
            victory_timer += 1
            if victory_timer == 1:
                winner.animator.set_state("taunt", force=True)
            winner.animator.update(dt)
            victory_frame = winner.animator.get_frame(winner.facing == 1)
            if victory_frame:
                winner.image = victory_frame

        # --- Normal melee attacks (ground and aerial) ---
        attack_landed = False
        for attacker, victim in [(player1, player2), (player2, player1)]:
            if (attacker.attacking > 0 and
                attacker.hitstun <= 0 and
                not attacker.hit_this_swing):

                # Determine hitbox and active frames
                if attacker.heavy_attack:
                    # Heavy attack (ground) — read timing from attacker
                    hitbox = attacker.heavy_hitbox()
                    hit_start = attacker.attack_hit_start
                    hit_end = attacker.attack_hit_end
                    current_frame = attacker.attack_frames - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    # For combo characters, use pre-set values (no double-scaling)
                    if (attacker.combo_type == "heavy" and
                        attacker.combo_version > 0):
                        damage = attacker.attack_damage
                        base_kb = attacker.attack_base_kb
                        kb_growth = attacker.attack_kb_growth
                        kb_type = attacker.attack_kb_type
                    else:
                        damage = attacker.get_heavy_damage()
                        base_kb = attacker.get_heavy_base_kb()
                        kb_growth = attacker.get_heavy_kb_growth()
                        kb_type = "straight"
                    move_id = "heavy"
                elif attacker.aerial_attack_stats:
                    # Aerial attack
                    hitbox = attacker.aerial_hitbox()
                    hit_start = attacker.aerial_attack_stats[5]
                    hit_end = attacker.aerial_attack_stats[6]
                    current_frame = attacker.aerial_attack_stats[4] - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    damage = attacker.aerial_attack_stats[0]
                    base_kb = attacker.aerial_attack_stats[1]
                    kb_growth = attacker.aerial_attack_stats[2]
                    kb_type = attacker.aerial_attack_stats[7]
                    move_id = attacker.aerial_attack_name
                else:
                    # Ground attack
                    hitbox = attacker.attack_hitbox()
                    hit_start = attacker.attack_hit_start
                    hit_end = attacker.attack_hit_end
                    current_frame = attacker.attack_frames - attacker.attacking
                    in_active = hit_start <= current_frame <= hit_end
                    damage = attacker.attack_damage
                    base_kb = attacker.attack_base_kb
                    kb_growth = attacker.attack_kb_growth
                    kb_type = attacker.attack_kb_type
                    move_id = "attack"

                if in_active and hitbox.colliderect(victim.rect) and is_facing(attacker, victim):
                    # Check if victim is shielding
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(damage, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(damage, victim.facing)
                            attacker.record_stale(move_id)
                            attacker.hit_this_swing = True
                            shake.trigger(
                                duration=8,
                                intensity=int(2 + victim.percentage * 0.05)
                            )
                            attack_landed = True
                            particles.shield_hit(victim.rect.centerx, victim.rect.centery)
                    else:
                        stale_mult = attacker.get_stale_multiplier(move_id)
                        di_y = get_di_y(keys, victim.ctrl)

                        # Yoshi heavy-after-roll bonus
                        kb_bonus = 1.0
                        if attacker.just_rolled and attacker.heavy_attack:
                            kb_bonus = attacker.roll_heavy_bonus

                        damage *= attacker.damage_mult

                        # --- Counter-hit check ---
                        is_counter = victim.is_counter_hit_vulnerable()
                        if is_counter:
                            kb_bonus *= COUNTER_HIT_KB_MULT
                            victim.trigger_counter_hit()

                        c_mult = 1.0
                        if attacker.combo_type == "light" and attacker.combo_version > 0:
                            c_mult = {1: 0.35, 2: 0.55, 3: 0.75}.get(attacker.combo_version, 1.0)

                        victim.take_damage(
                            base_damage=damage,
                            knockback_growth=kb_growth,
                            base_knockback=base_kb,
                            attacker_facing=attacker.facing,
                            stale_mult=stale_mult,
                            di_y=di_y,
                            kb_bonus=kb_bonus,
                            knockback_type=kb_type,
                            attacker_percent=attacker.percentage,
                            combo_launch_mult=c_mult
                        )

                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS

                        attacker.record_stale(move_id)
                        attacker.hit_this_swing = True
                        attacker.update_combo(damage)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun

                        # Finisher check
                        attacker.check_finisher(victim)
                        attacker_lag = attacker.attack_frames
                        is_true = victim.is_true_combo(damage, attacker_lag, kb_growth, base_kb, kb_bonus)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)

                        shake.trigger(
                            duration=10,
                            intensity=int(2 + victim.percentage * 0.08)
                        )
                        attack_landed = True
                        particles.hit_spark(victim.rect.centerx, victim.rect.centery, attacker.facing, victim.percentage)

        # --- Special moves ---
        for attacker, victim in [(player1, player2), (player2, player1)]:

            # --- Fire Punch (Mario melee special) ---
            if (attacker.special_active > 0 and
                attacker.special_name == "fire_punch" and
                not attacker.special_hit and
                FIRE_PUNCH_HIT_START <= attacker.special_active <= FIRE_PUNCH_HIT_END):

                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(FIRE_PUNCH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(FIRE_PUNCH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=10, intensity=int(3 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=FIRE_PUNCH_DAMAGE * attacker.damage_mult,
                            knockback_growth=FIRE_PUNCH_KNOCKBACK_GROWTH,
                            base_knockback=FIRE_PUNCH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=FIRE_PUNCH_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(FIRE_PUNCH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        attacker_lag = FIRE_PUNCH_ACTIVE_FRAMES
                        is_true = victim.is_true_combo(FIRE_PUNCH_DAMAGE, attacker_lag, FIRE_PUNCH_KNOCKBACK_GROWTH, FIRE_PUNCH_BASE_KNOCKBACK)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)
                        shake.trigger(duration=12, intensity=int(3 + victim.percentage * 0.08))
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "hammer_smash" and
                not attacker.special_hit and
                HAMMER_SMASH_HIT_START <= attacker.special_active <= HAMMER_SMASH_HIT_END):

                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    # Check if victim is shielding
                    if victim.shielding and victim.shield_health > 0:
                        # Shield hit
                        shield_hit = victim.take_shield_hit(HAMMER_SMASH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(HAMMER_SMASH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(
                                duration=12,
                                intensity=int(4 + victim.percentage * 0.05)
                            )
                            attack_landed = True
                    else:
                        # Normal hit
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=HAMMER_SMASH_DAMAGE * attacker.damage_mult,
                            knockback_growth=HAMMER_SMASH_KNOCKBACK_GROWTH,
                            base_knockback=HAMMER_SMASH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=HAMMER_SMASH_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(HAMMER_SMASH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        attacker_lag = HAMMER_SMASH_ACTIVE_FRAMES
                        is_true = victim.is_true_combo(HAMMER_SMASH_DAMAGE, attacker_lag, HAMMER_SMASH_KNOCKBACK_GROWTH, HAMMER_SMASH_BASE_KNOCKBACK)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)
                        shake.trigger(
                            duration=15,
                            intensity=int(4 + victim.percentage * 0.08)
                        )
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "head_drill" and
                not attacker.special_hit and
                HEAD_DRILL_HIT_START <= attacker.special_active <= HEAD_DRILL_HIT_END):

                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(HEAD_DRILL_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(HEAD_DRILL_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=12, intensity=int(4 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        is_counter, ch_mult = check_counter_hit(attacker, victim)
                        victim.take_damage(
                            base_damage=BARREL_SMASH_DAMAGE * attacker.damage_mult,
                            knockback_growth=BARREL_SMASH_KNOCKBACK_GROWTH,
                            base_knockback=BARREL_SMASH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=BARREL_SMASH_KB_BONUS * ch_mult,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        if is_counter:
                            victim.hitstun += COUNTER_HIT_HITSTUN_BONUS
                        attacker.special_hit = True
                        attacker.update_combo(BARREL_SMASH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        attacker_lag = HEAD_DRILL_ACTIVE_FRAMES
                        is_true = victim.is_true_combo(HEAD_DRILL_DAMAGE, attacker_lag, HEAD_DRILL_KNOCKBACK_GROWTH, HEAD_DRILL_BASE_KNOCKBACK)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)
                        shake.trigger(duration=15, intensity=int(4 + victim.percentage * 0.08))
                        attack_landed = True

            if (attacker.special_active > 0 and
                attacker.special_name == "barrel_smash" and
                not attacker.special_hit and
                BARREL_SMASH_HIT_START <= attacker.special_active <= BARREL_SMASH_HIT_END):

                if attacker.special_hitbox().colliderect(victim.rect) and is_facing(attacker, victim):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(BARREL_SMASH_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(BARREL_SMASH_DAMAGE, victim.facing)
                            attacker.special_hit = True
                            shake.trigger(duration=12, intensity=int(4 + victim.percentage * 0.05))
                            attack_landed = True
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        victim.take_damage(
                            base_damage=BARREL_SMASH_DAMAGE * attacker.damage_mult,
                            knockback_growth=BARREL_SMASH_KNOCKBACK_GROWTH,
                            base_knockback=BARREL_SMASH_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=BARREL_SMASH_KB_BONUS,
                            knockback_type="straight",
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        attacker.special_hit = True
                        attacker.update_combo(BARREL_SMASH_DAMAGE)
                        attacker.advance_combo()
                        attacker.combo_hitstun = victim.hitstun
                        attacker.check_finisher(victim, special_name=attacker.special_name)
                        attacker_lag = BARREL_SMASH_ACTIVE_FRAMES
                        is_true = victim.is_true_combo(BARREL_SMASH_DAMAGE, attacker_lag, BARREL_SMASH_KNOCKBACK_GROWTH, BARREL_SMASH_BASE_KNOCKBACK)
                        if is_true and attacker.combo_counter > 1:
                            attacker.last_combo_hit = (attacker.combo_counter, attacker.combo_damage)
                        shake.trigger(duration=15, intensity=int(4 + victim.percentage * 0.08))
                        attack_landed = True

            # Yoshi egg throw (Q)
            if (attacker.special_active > 0 and
                attacker.special_name in ("egg_throw_ground", "egg_throw_air") and
                not attacker.special_spawned and
                attacker.special_active <= EGG_THROW_SPAWN_FRAME):

                offset = 40 * attacker.facing
                egg_x = attacker.rect.centerx + offset
                egg_y = attacker.rect.centery - 10
                egg = EggProjectile(egg_x, egg_y, attacker.facing, attacker,
                                    sprite_lookup[attacker.char], scale=SCALE)
                eggs.append(egg)
                attacker.special_spawned = True

        # --- Blastshot / Barrel spawn (fire_punch is melee, no projectile) ---
        for attacker, victim in [(player1, player2), (player2, player1)]:
            if (attacker.special_active > 0 and
                not attacker.special_spawned):

                if attacker.special_name == "blastshot":
                    offset = 30 * attacker.facing
                    bx = attacker.rect.centerx + offset
                    by = attacker.rect.centery - 5
                    proj = Blastshot(bx, by, attacker.facing, attacker)
                    projectiles.append(proj)
                    attacker.special_spawned = True
                elif attacker.special_name == "barrel_throw":
                    offset = 30 * attacker.facing
                    bx = attacker.rect.centerx + offset
                    by = attacker.rect.centery - 5
                    proj = Barrel(bx, by, attacker.facing, attacker)
                    projectiles.append(proj)
                    attacker.special_spawned = True

        # --- Yoshi egg roll collision ---
        for attacker, victim in [(player1, player2), (player2, player1)]:
            if (attacker.char == "yoshi" and attacker.egg_rolling and
                attacker.egg_roll_hit_interval >= EGG_ROLL_HIT_INTERVAL):

                roll_box = attacker.rect.copy()
                roll_box.width += 20
                if attacker.facing == 1:
                    roll_box.left = attacker.rect.right
                else:
                    roll_box.right = attacker.rect.left

                if roll_box.colliderect(victim.rect):
                    if victim.shielding and victim.shield_health > 0:
                        shield_hit = victim.take_shield_hit(EGG_ROLL_DAMAGE, attacker.facing)
                        if shield_hit:
                            attacker.apply_shield_pushback_to_attacker(EGG_ROLL_DAMAGE, victim.facing)
                            attacker.egg_roll_hit_interval = 0
                            particles.hit_spark(attacker.rect.centerx, attacker.rect.centery)
                            shake.trigger(duration=8, intensity=int(2 + victim.percentage * 0.05))
                    else:
                        di_y = get_di_y(keys, victim.ctrl)
                        victim.take_damage(
                            base_damage=EGG_ROLL_DAMAGE,
                            knockback_growth=EGG_ROLL_KNOCKBACK_GROWTH,
                            base_knockback=EGG_ROLL_BASE_KNOCKBACK,
                            attacker_facing=attacker.facing,
                            kb_bonus=EGG_ROLL_KB_BONUS,
                            knockback_type=EGG_ROLL_KB_TYPE,
                            di_y=di_y,
                            attacker_percent=attacker.percentage
                        )
                        attacker.egg_roll_hit_interval = 0
                        attacker.record_stale("egg_roll")
                        particles.hit_spark(attacker.rect.centerx, attacker.rect.centery)
                        shake.trigger(duration=10, intensity=int(2 + victim.percentage * 0.08))

        # --- Update shells ---
        if not frozen:
            for shell in shells:
                shell.update(solid)
                if shell.active and shell.grace_frames <= 0:
                    for player in (player1, player2):
                        if shell.owner != player and shell.rect.colliderect(player.rect):
                            # Check if player is shielding
                            if player.shielding and player.shield_health > 0:
                                # Shield hit
                                shield_hit = player.take_shield_hit(SHELL_DAMAGE, shell.facing)
                                if shield_hit:
                                    shell.owner.apply_shield_pushback_to_attacker(SHELL_DAMAGE, player.facing)
                                    shell.active = False
                                    particles.hit_spark(shell.rect.centerx, shell.rect.centery)
                                    shake.trigger(
                                        duration=10,
                                        intensity=int(4 + player.percentage * 0.05)
                                    )
                                    break
                            else:
                                # Normal hit
                                di_y = get_di_y(keys, player.ctrl)
                                player.take_damage(
                                    base_damage=SHELL_DAMAGE,
                                    knockback_growth=SHELL_KNOCKBACK_GROWTH,
                                    base_knockback=SHELL_BASE_KNOCKBACK,
                                    attacker_facing=shell.facing,
                                    kb_bonus=SHELL_THROW_KB_BONUS,
                                    knockback_type="upward",
                                    di_y=di_y,
                                    attacker_percent=shell.owner.percentage
                                )
                                shell.active = False
                                particles.hit_spark(shell.rect.centerx, shell.rect.centery)
                                shell.owner.update_combo(SHELL_DAMAGE)
                                shell.owner.advance_combo()
                                shell.owner.combo_hitstun = player.hitstun
                                shell.owner.check_finisher(player)
                                shake.trigger(
                                    duration=12,
                                    intensity=int(4 + player.percentage * 0.08)
                                )
                                break

        shells = [s for s in shells if s.active]

        # --- Update eggs ---
        if not frozen:
            for egg in eggs:
                egg.update(solid)
                if egg.active:
                    for player in (player1, player2):
                        if egg.owner != player and egg.rect.colliderect(player.rect):
                            if player.shielding and player.shield_health > 0:
                                shield_hit = player.take_shield_hit(egg.damage, egg.facing)
                                if shield_hit:
                                    egg.owner.apply_shield_pushback_to_attacker(egg.damage, player.facing)
                                    egg.active = False
                                    particles.hit_spark(egg.rect.centerx, egg.rect.centery)
                                    shake.trigger(duration=8, intensity=int(2 + player.percentage * 0.05))
                                    break
                            else:
                                di_y = get_di_y(keys, player.ctrl)
                                player.take_damage(
                                    base_damage=egg.damage,
                                    knockback_growth=egg.kb_growth,
                                    base_knockback=egg.base_kb,
                                    attacker_facing=egg.facing,
                                    kb_bonus=egg.kb_bonus,
                                    knockback_type="normal",
                                    di_y=di_y,
                                    attacker_percent=egg.owner.percentage
                                )
                                egg.active = False
                                particles.hit_spark(egg.rect.centerx, egg.rect.centery)
                                egg.owner.record_stale("egg_throw")
                                egg.owner.update_combo(egg.damage)
                                egg.owner.advance_combo()
                                egg.owner.combo_hitstun = player.hitstun
                                egg.owner.check_finisher(player)
                                shake.trigger(duration=10, intensity=int(2 + player.percentage * 0.08))
                                break
        eggs = [e for e in eggs if e.active]

        # --- Update projectiles (fireball / blastshot) ---
        if not frozen:
            for proj in projectiles:
                proj.update(solid)
                if proj.active:
                    for player in (player1, player2):
                        if proj.owner != player and proj.rect.colliderect(player.rect):
                            if player.shielding and player.shield_health > 0:
                                shield_hit = player.take_shield_hit(proj.damage, proj.facing)
                                if shield_hit:
                                    proj.owner.apply_shield_pushback_to_attacker(proj.damage, player.facing)
                                    proj.active = False
                                    particles.hit_spark(proj.rect.centerx, proj.rect.centery)
                                    shake.trigger(duration=8, intensity=int(2 + player.percentage * 0.05))
                                    break
                            else:
                                di_y = get_di_y(keys, player.ctrl)
                                player.take_damage(
                                    base_damage=proj.damage,
                                    knockback_growth=proj.kb_growth,
                                    base_knockback=proj.base_kb,
                                    attacker_facing=proj.facing,
                                    knockback_type="normal",
                                    di_y=di_y,
                                    attacker_percent=proj.owner.percentage
                                )
                                proj.active = False
                                particles.hit_spark(proj.rect.centerx, proj.rect.centery)
                                proj.owner.record_stale(proj.__class__.__name__.lower())
                                proj.owner.update_combo(proj.damage)
                                proj.owner.advance_combo()
                                proj.owner.combo_hitstun = player.hitstun
                                proj.owner.check_finisher(player, special_name=proj.__class__.__name__.lower())
                                shake.trigger(duration=10, intensity=int(2 + player.percentage * 0.08))
                                break
        projectiles = [p for p in projectiles if p.active]

        # --- Grrrol spawning and update ---
        if hazards.get("grrrols") and not frozen and countdown_done and not game_over:
            grrrol_spawn_timer += 1
            if grrrol_spawn_timer >= grrrol_next_spawn and len(grrrols) < 3:
                spawn_side = 1 if frame % 2 == 0 else -1
                spawn_x = 50 if spawn_side == 1 else LEVEL_W - 50
                grrrol = Grrrol(spawn_x, ground_y - GRRROL_SIZE - 4, roll_frames=grrrol_frames)
                grrrol.vel.x = spawn_side * GRRROL_SPEED
                grrrols.append(grrrol)
                grrrol_spawn_timer = 0
                grrrol_next_spawn = random.randint(300, 720)

            for grrrol in grrrols:
                grrrol.update(solid, dt)
                grrrol.check_blast_zone(LEVEL_W, LEVEL_H)
                for player in (player1, player2):
                    grrrol.check_player_hit(player)
                    grrrol.check_player_attack(player)

            grrrols = [g for g in grrrols if g.alive]

        # --- Bob-omb spawning and update ---
        if hazards.get("bobombs") and not frozen and countdown_done and not game_over:
            bobomb_spawn_timer += 1
            if bobomb_spawn_timer >= bobomb_next_spawn and len(bobombs) < 2:
                spawn_x = random.randint(100, LEVEL_W - 100)
                bob = BobOmb(spawn_x, -30, sprites=bobomb_sprites, targets=[player1, player2])
                bobombs.append(bob)
                bobomb_spawn_timer = 0
                bobomb_next_spawn = random.randint(420, 900)

            for bob in bobombs:
                bob.update(solid)
                for player in (player1, player2):
                    bob.check_hit(player)

            bobombs = [b for b in bobombs if b.alive]

        # --- Kamek spawning and update ---
        if hazards.get("kamek") and not frozen and countdown_done and not game_over:
            kamek_spawn_timer += 1
            if kamek_spawn_timer >= kamek_next_spawn and len(kameks) < 1:
                near_player = random.choice([player1, player2])
                spawn_side = random.choice([-1, 1])
                spawn_x = near_player.rect.centerx + spawn_side * random.randint(150, 300)
                spawn_x = max(50, min(LEVEL_W - 50, spawn_x))
                spawn_y = ground_y - random.randint(400, 550)
                spawn_y = max(KAMEK_FLY_MIN_Y, min(KAMEK_FLY_MAX_Y, spawn_y))
                kameks.append(Kamek(spawn_x, spawn_y, sprites=kamek_sprites))
                kamek_spawn_timer = 0
                kamek_next_spawn = random.randint(KAMEK_SPAWN_INTERVAL_MIN, KAMEK_SPAWN_INTERVAL_MAX)

            for kamek in kameks:
                kamek.update([player1, player2], LEVEL_W, LEVEL_H)
                if kamek.state in ("attack", "windup"):
                    bolt = kamek.fire_magic([player1, player2])
                    if bolt:
                        magic_projectiles.append(bolt)
                kamek.check_player_attack(player1)
                kamek.check_player_attack(player2)

            for mp in magic_projectiles:
                was_alive = mp.alive
                mp.update()
                mp.check_player_hit(player1)
                mp.check_player_hit(player2)
                if was_alive and not mp.alive:
                    particles.magic_impact(mp.rect.centerx, mp.rect.centery)
            magic_projectiles = [m for m in magic_projectiles if m.alive]

            kameks = [k for k in kameks if k.alive]

        # --- NPC spawning and update ---
        if hazards.get("npcs") and not frozen and countdown_done and not game_over:
            npc_spawn_timer += 1
            goomba_count = sum(1 for n in npcs if isinstance(n, Goomba) and n.alive)
            koopa_count = sum(1 for n in npcs if isinstance(n, Koopa) and n.alive)
            shyguy_count = sum(1 for n in npcs if isinstance(n, ShyGuy) and n.alive)
            buzzy_count = sum(1 for n in npcs if isinstance(n, BuzzyBeetle) and n.alive)
            if npc_spawn_timer >= npc_next_spawn and len(npcs) < 6:
                pipe_x = random.choice(pipe_positions)
                spawn_x = pipe_x * tilemap.tile_px + tilemap.tile_px // 2
                spawn_y = ground_y - tilemap.tile_px
                if is_factory:
                    factory_safe_positions = [5, 10, 20, 25, 35, 40, 50]
                    spawn_x = random.choice(factory_safe_positions) * tilemap.tile_px + tilemap.tile_px // 2
                    spawn_y = ground_y - tilemap.tile_px
                    npc = BuzzyBeetle(spawn_x, spawn_y, buzzy_beetle_sprites, facing=random.choice([-1, 1]))
                else:
                    enemy_type = random.choice(["goomba", "goomba", "koopa"])
                    if enemy_type == "goomba" and goomba_count < 6:
                        npc = Goomba(spawn_x, spawn_y, goomba_sprites, facing=random.choice([-1, 1]))
                    elif enemy_type == "koopa" and koopa_count < 3:
                        npc = Koopa(spawn_x, spawn_y, koopa_sprites, facing=random.choice([-1, 1]))
                    else:
                        npc = Goomba(spawn_x, spawn_y, goomba_sprites, facing=random.choice([-1, 1]))
                npcs.append(npc)
                npc_spawn_timer = 0
                npc_next_spawn = random.randint(120, 240)

            for npc in npcs:
                npc.update(solid, dt, level_w=LEVEL_W)

            for npc in npcs:
                for player in (player1, player2):
                    if not player.is_dead and npc.alive and npc.rect.colliderect(player.rect) and player.hitstun <= 0 and player.hitlag <= 0:
                        if isinstance(npc, Goomba) and npc.stomp_timer <= 0:
                            if player.vy_int > 0 and player.rect.bottom <= npc.rect.centery + 5:
                                npc.stomp()
                                player.vy_int = JUMP_FORCE
                            else:
                                player.take_damage(
                                    base_damage=1, knockback_growth=0.0,
                                    base_knockback=1, attacker_facing=npc.facing,
                                    knockback_type="normal"
                                )
                                push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                player.rect.x += push_dir * 20
                                player.pos.x = float(player.rect.x)
                                npc.facing *= -1
                                npc.pos_x = float(npc.rect.x)
                        elif isinstance(npc, ShyGuy) and npc.stomp_timer <= 0:
                            if player.vy_int > 0 and player.rect.bottom <= npc.rect.centery + 5:
                                npc.stomp()
                                player.vy_int = JUMP_FORCE
                            else:
                                player.take_damage(
                                    base_damage=5, knockback_growth=0.5,
                                    base_knockback=3, attacker_facing=npc.facing,
                                    knockback_type="normal"
                                )
                                push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                player.rect.x += push_dir * 20
                                player.pos.x = float(player.rect.x)
                                npc.facing *= -1
                                npc.pos_x = float(npc.rect.x)
                        elif isinstance(npc, BuzzyBeetle):
                            if npc.state == "walk" and npc.stomp_timer <= 0:
                                if player.vy_int > 0 and player.rect.bottom <= npc.rect.centery + 5:
                                    from_left = player.rect.centerx < npc.rect.centerx
                                    npc.stomp(from_left=from_left)
                                    player.vy_int = JUMP_FORCE
                                else:
                                    player.take_damage(
                                        base_damage=10, knockback_growth=0.8,
                                        base_knockback=4, attacker_facing=npc.facing,
                                        knockback_type="normal"
                                    )
                                    push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                    player.rect.x += push_dir * 15
                                    player.pos.x = float(player.rect.x)
                                    npc.facing *= -1
                                    npc.pos_x = float(npc.rect.x)
                            elif npc.state == "spin" and npc.stomp_timer <= 0:
                                if player.vy_int > 0 and player.rect.bottom <= npc.rect.centery + 5:
                                    npc.stomp()
                                    player.vy_int = JUMP_FORCE
                                else:
                                    player.take_damage(
                                        base_damage=12, knockback_growth=0.9,
                                        base_knockback=5, attacker_facing=npc.facing,
                                        knockback_type="normal"
                                    )
                                    push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                    player.rect.x += push_dir * 10
                                    player.pos.x = float(player.rect.x)
                                    npc.alive = False
                        elif isinstance(npc, Koopa):
                            if npc.state == "walk":
                                if player.vy_int > 0 and player.rect.bottom <= npc.rect.centery + 5:
                                    from_left = player.rect.centerx < npc.rect.centerx
                                    npc.stomp(from_left=from_left)
                                    player.vy_int = JUMP_FORCE
                                else:
                                    player.take_damage(
                                        base_damage=8, knockback_growth=0.8,
                                        base_knockback=4, attacker_facing=npc.facing,
                                        knockback_type="normal"
                                    )
                                    push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                    player.rect.x += push_dir * 15
                                    player.pos.x = float(player.rect.x)
                                    npc.facing *= -1
                                    npc.pos_x = float(npc.rect.x)
                            elif npc.state == "kicked":
                                player.take_damage(
                                    base_damage=12, knockback_growth=0.9,
                                    base_knockback=5, attacker_facing=npc.facing,
                                    knockback_type="normal"
                                )
                                push_dir = 1 if player.rect.centerx >= npc.rect.centerx else -1
                                player.rect.x += push_dir * 10
                                player.pos.x = float(player.rect.x)
                                npc.alive = False

            for npc in npcs:
                if isinstance(npc, (Koopa, BuzzyBeetle)) and npc.state in ("kicked", "spin"):
                    for other in npcs:
                        if other is not npc and other.alive:
                            if npc.check_kill_enemy(other):
                                pass

            npcs = [n for n in npcs if n.alive]

        # --- Bullet Bill spawning (Factory) ---
        if hazards.get("npcs") and is_factory and not frozen and countdown_done and not game_over:
            for blaster in bill_blasters:
                new_bullet = blaster.try_fire()
                if new_bullet and sum(1 for b in bullet_bills if b.alive) < 3:
                    bullet_bills.append(new_bullet)

            for b in bullet_bills:
                b.update(solid, dt, level_w=LEVEL_W)
            bullet_bills = [b for b in bullet_bills if b.alive]

            for b in bullet_bills:
                if not b.alive:
                    continue
                for blaster in bill_blasters:
                    if blaster is not bill_blasters[0 if b.facing == 1 else 1] and b.rect.colliderect(blaster.rect):
                        b.alive = False
                        break
                for player in (player1, player2):
                    if not player.is_dead and b.alive and b.rect.colliderect(player.rect) and player.hitstun <= 0 and player.hitlag <= 0:
                        player.take_damage(
                            base_damage=15, knockback_growth=1.0,
                            base_knockback=6, attacker_facing=b.facing,
                            knockback_type="normal"
                        )
                        push_dir = 1 if player.rect.centerx >= b.rect.centerx else -1
                        player.rect.x += push_dir * 10
                        player.pos.x = float(player.rect.x)
                        b.alive = False

        # --- Pipe spawner (Factory) ---
            pipe_spawner_timer += 1
            if pipe_spawner_timer >= 240 and len(bobombs) < 3:
                spawn_pipe_x = random.choice(pipe_positions) * tilemap.tile_px + tilemap.tile_px
                bob = BobOmb(spawn_pipe_x, ground_y - tilemap.tile_px * 3, sprites=bobomb_sprites, targets=[player1, player2])
                bobombs.append(bob)
                pipe_spawner_timer = 0

        particles.update()
        for bz in blast_zone_effects:
            bz.update()
        blast_zone_effects = [bz for bz in blast_zone_effects if bz.alive]

        # --- Player-player overlap & stomps ---
        Player.resolve_overlap(player1, player2, solid, skip_stomp=attack_landed)

        # --- Blast-zone check ---
        if not game_over:
            for i, p in enumerate((player1, player2)):
                if not p.is_dead and (
                    p.rect.right < -BLAST_ZONE_MARGIN_SIDE or
                    p.rect.left > LEVEL_W + BLAST_ZONE_MARGIN_SIDE or
                    p.rect.top > LEVEL_H + BLAST_ZONE_MARGIN_BOTTOM or
                    p.rect.bottom < -BLAST_ZONE_MARGIN_TOP):
                    particles.ko_explosion(p.rect.centerx, p.rect.centery)
                    blast_zone_effects.append(BlastZoneExplosion(p.rect.centerx, p.rect.centery, blast_zone_frames))
                    death_zoom_timer = 90
                    death_zoom_pos = (p.rect.centerx, p.rect.centery)
                    p.die()

        # --- Camera: Smash-style midpoint + zoom ---
        if game_over:
            cam_x = winner.rect.centerx
            cam_y = winner.rect.centery
            camera.set_zoom(1.4)
            camera.set_shake(shake.update())
            camera.follow(cam_x, cam_y, dt)
        elif death_zoom_timer > 0:
            camera.set_zoom(1.6)
            camera.set_shake(shake.update())
            camera.follow(death_zoom_pos[0], death_zoom_pos[1], dt)
        else:
            mid_x = (player1.rect.centerx + player2.rect.centerx) // 2
            mid_y = (player1.rect.centery + player2.rect.centery) // 2

            dx = abs(player1.rect.centerx - player2.rect.centerx)
            dy = abs(player1.rect.centery - player2.rect.centery)
            zoom_target = min(1.0,
                              SCREEN_W * 0.75 / max(dx, 100),
                              SCREEN_H * 0.75 / max(dy, 100))
            camera.set_zoom(zoom_target)
            camera.set_shake(shake.update())
            camera.follow(mid_x, mid_y, dt)

        render_w, render_h = camera.get_render_size()
        cam_off = (int(camera.offset.x), int(camera.offset.y))

        # --- Network state sync (online mode) ---
        if online_mode and countdown_done and not game_over:
            if frame % STATE_SYNC_INTERVAL == 0 and frame > 0:
                p1_hash_state = {
                    "x": player1.rect.x, "y": player1.rect.y,
                    "vx": player1.vx_int, "vy": player1.vy_int,
                    "percentage": player1.percentage,
                    "hearts": player1.hearts, "facing": player1.facing,
                    "attacking": player1.attacking,
                    "on_ground": int(player1.on_ground),
                }
                p2_hash_state = {
                    "x": player2.rect.x, "y": player2.rect.y,
                    "vx": player2.vx_int, "vy": player2.vy_int,
                    "percentage": player2.percentage,
                    "hearts": player2.hearts, "facing": player2.facing,
                    "attacking": player2.attacking,
                    "on_ground": int(player2.on_ground),
                }
                local_hash = compute_state_hash(frame, p1_hash_state, p2_hash_state)
                network_session.send_state_hash(frame, local_hash)
                if network_session.check_desync(frame, local_hash):
                    lag_indicator_timer = 120
            # Ping update
            ping_timer += dt
            if ping_timer >= ping_interval:
                ping_timer = 0.0
                network_session.send_ping()
            if network_session.update_rtt():
                lag_indicator_timer = 60
            if lag_indicator_timer > 0:
                lag_indicator_timer -= 1

        # Render world to a temporary surface, then scale to screen
        world_surf = pygame.Surface((render_w, render_h))
        if is_factory:
            world_surf.fill((40, 40, 50))
        else:
            world_surf.fill((92, 148, 252))
            bg.draw(world_surf, cam_off, LEVEL_W, ground_y, tilemap.tile_px)
        tilemap.draw(world_surf, cam_off, tileset_surf)

        for shell in shells:
            shell.draw(world_surf, cam_off)

        for egg in eggs:
            egg.draw(world_surf, cam_off)

        for proj in projectiles:
            proj.draw(world_surf, cam_off)

        player1.draw(world_surf, cam_off)
        player2.draw(world_surf, cam_off)

        for npc in npcs:
            npc.draw(world_surf, cam_off)

        for grrrol in grrrols:
            grrrol.draw(world_surf, cam_off)

        for bob in bobombs:
            bob.draw(world_surf, cam_off)

        for kamek in kameks:
            kamek.draw(world_surf, cam_off)

        for b in bullet_bills:
            b.draw(world_surf, cam_off)

        for blaster in bill_blasters:
            blaster.draw(world_surf, cam_off)

        for mp in magic_projectiles:
            mp.draw(world_surf, cam_off)

        particles.draw(world_surf, cam_off)
        for bz in blast_zone_effects:
            bz.draw(world_surf, cam_off)

        # --- Countdown display ---
        if not countdown_done:
            from src.ui_sprites import load_countdown
            seconds_left = (countdown_timer + 59) // 60
            if seconds_left > 0:
                count_img = load_countdown(seconds_left)
            else:
                count_img = load_countdown("GO!")
            if count_img:
                cx = render_w // 2 - count_img.get_width() // 2
                cy = render_h // 3 - count_img.get_height() // 2
                world_surf.blit(count_img, (cx, cy))
            else:
                if seconds_left > 0:
                    count_text = str(seconds_left)
                else:
                    count_text = "GO!"
                count_surf = count_font.render(count_text, True, (255, 255, 255))
                count_shadow = count_font.render(count_text, True, (0, 0, 0))
                cx = render_w // 2 - count_surf.get_width() // 2
                cy = render_h // 3 - count_surf.get_height() // 2
                world_surf.blit(count_shadow, (cx + 3, cy + 3))
                world_surf.blit(count_surf, (cx, cy))

        # --- Game over text ---
        if game_over:
            win_num = 1 if winner == player1 else 2
            win_text = f"P{win_num} {winner.char.upper()} WINS!"
            win_surf = go_font.render(win_text, True, (255, 215, 0))
            win_shadow = go_font.render(win_text, True, (0, 0, 0))
            wx = render_w // 2 - win_surf.get_width() // 2
            wy = render_h // 4 - win_surf.get_height() // 2
            world_surf.blit(win_shadow, (wx + 3, wy + 3))
            world_surf.blit(win_surf, (wx, wy))

            # After 3 seconds, show victory screen
            if victory_timer == 180:
                stats = {
                    "damage": max(player1.percentage, player2.percentage),
                    "kos": max(0, LIVES - (player2.hearts if winner == player1 else player1.hearts)),
                    "time": frame // FPS,
                }
                # Show victory on top of current screen
                scaled = pygame.transform.smoothscale(world_surf, screen.get_size())
                screen.blit(scaled, (0, 0))
                pygame.display.flip()
                result = victory_screen(screen, font, winner.char, win_num, stats)
                if result == "rematch":
                    return "restart"
                elif result == "character_select":
                    return "character_select"
                else:
                    return "main_menu"

        scaled = pygame.transform.smoothscale(world_surf, screen.get_size())
        screen.blit(scaled, (0, 0))

        # --- HUD (screen-space) ---
        match_time = max(0, (MATCH_TIME - frame) / FPS) if not game_over else 0
        p1_input_type = "Keyboard"
        if gamepad1 and gamepad1.alive:
            p1_input_type = "Gamepad"
        p2_input_type = "AI" if ai_mode else ("Keyboard" if not gamepad2 or not gamepad2.alive else "Gamepad")
        hud.draw(screen, [
            {"name": f"P1 {player1.char.upper()}", "percentage": player1.percentage,
             "stocks": player1.hearts, "max_stocks": LIVES,
             "shield_pct": player1.shield_health / MAX_SHIELD_HEALTH,
             "shielding": player1.shielding,
             "combo": {"count": player1.combo_counter, "damage": player1.combo_damage,
                       "hot": bool(player1.last_combo_hit)} if player1.combo_counter > 1 else None,
             "color": CHAR_COLORS.get(player1.char, (200, 200, 200)),
             "input_type": p1_input_type},
            {"name": f"P2 {player2.char.upper()}", "percentage": player2.percentage,
             "stocks": player2.hearts, "max_stocks": LIVES,
             "shield_pct": player2.shield_health / MAX_SHIELD_HEALTH,
             "shielding": player2.shielding,
             "combo": {"count": player2.combo_counter, "damage": player2.combo_damage,
                       "hot": bool(player2.last_combo_hit)} if player2.combo_counter > 1 else None,
             "color": CHAR_COLORS.get(player2.char, (200, 200, 200)),
             "input_type": p2_input_type},
        ], time_left=match_time)

        # --- Combo counters ---
        if player1.combo_counter > 1:
            combo_color = (255, 255, 100) if player1.last_combo_hit else (200, 200, 200)
            combo_text = f"P1 COMBO: {player1.combo_counter} ({player1.combo_damage:.0f}%)"
            combo_surf = combo_font.render(combo_text, True, combo_color)
            screen.blit(combo_surf, (30, SCREEN_H - 110))
        if player2.combo_counter > 1:
            combo_color = (255, 255, 100) if player2.last_combo_hit else (200, 200, 200)
            combo_text = f"P2 COMBO: {player2.combo_counter} ({player2.combo_damage:.0f}%)"
            combo_surf = combo_font.render(combo_text, True, combo_color)
            screen.blit(combo_surf, (SCREEN_W - combo_surf.get_width() - 30, SCREEN_H - 110))

        # --- Connection quality indicator (online mode) ---
        if online_mode:
            quality_text = ""
            if network_session.rtt_ms > 0:
                quality_text = f"Ping: {int(network_session.rtt_ms)}ms"
                if network_session.rtt_ms < 50:
                    quality_color = (100, 255, 100)
                elif network_session.rtt_ms < 100:
                    quality_color = (255, 255, 100)
                elif network_session.rtt_ms < 200:
                    quality_color = (255, 165, 0)
                else:
                    quality_color = (255, 80, 80)
            else:
                quality_text = "Connecting..."
                quality_color = (180, 180, 180)
            q_surf = font_tiny.render(quality_text, True, quality_color)
            screen.blit(q_surf, (SCREEN_W - q_surf.get_width() - 10, 10))
            if lag_indicator_timer > 0:
                lag_text = "LAG" if lag_indicator_timer > 60 else "SYNC"
                lag_color = (255, 80, 80) if lag_indicator_timer > 60 else (255, 200, 50)
                lag_surf = font_tiny.render(lag_text, True, lag_color)
                screen.blit(lag_surf, (SCREEN_W - lag_surf.get_width() - 10, 30))

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000
        frame += 1
        if online_mode:
            frame_ref[0] = frame

# FIX: This was missing — main() was never called!
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
