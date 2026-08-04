import pygame
import os

_UI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "UI", "sprites")

_cache = {}


def _load(name, scale=2):
    """Load a sprite from UI/sprites/ and scale it up with nearest-neighbor."""
    key = (name, scale)
    if key not in _cache:
        path = os.path.join(_UI_DIR, name)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            if scale != 1:
                w, h = img.get_size()
                img = pygame.transform.scale(img, (w * scale, h * scale))
        else:
            img = None
        _cache[key] = img
    return _cache[key]


def load_start_btn(hovered=False):
    return _load("start_hovered.png" if hovered else "start_btn.png", 3)

def load_start_btn_pressed():
    return _load("start_btn_pressed.png", 3)


def load_resume_btn(pressed=False):
    return _load("resume_btn_pressed.png" if pressed else "resume_btn.png", 3)

def load_restart_btn(pressed=False):
    return _load("restart_btn_pressed(menu).png" if pressed else "restart_btn(pause_menu).png", 3)

def load_exit_btn(pressed=False):
    return _load("exit_btn(pause_menu)_pressed.png" if pressed else "exit_btn(pause_menu).png", 3)

def load_quit_btn(hovered=False, pressed=False):
    if pressed:
        return _load("quit_btn_pressed.png", 3)
    return _load("quit_btn_hovered.png" if hovered else "quit_btn.png", 3)

def load_settings_btn(hovered=False, pressed=False):
    if pressed:
        return _load("settings_btn_pressed.png", 3)
    return _load("settings_btn_hovered.png" if hovered else "settings_btn.png", 3)


def load_crown(scale=3):
    return _load("crown_icon.png", scale)

def load_mushroom(scale=2):
    return _load("mushroom_icon_normal.png", scale)

def load_yellow_mushroom(scale=2):
    return _load("yellow_mushroom_icon.png", scale)

def load_question_block(scale=3):
    return _load("question_mark_block.png", scale)

def load_coin(frame=1, scale=2):
    name = f"coin({frame}).png"
    return _load(name, scale)

def load_fire_flower(scale=2):
    return _load("fire_flower_icon.png", scale)

def load_flame(scale=2):
    return _load("flame_icon.png", scale)

def load_star(scale=2):
    return _load("star_icon.png", scale)


def load_arrow_key(direction, scale=2):
    name = f"arrow_key_{direction}.png"
    return _load(name, scale)

def load_stage_frame(scale=2):
    return _load("stage_select_frame.png", scale)


def load_countdown(num):
    if num == "GO!":
        return _load("countdown_GO!.png", 4)
    return _load(f"countdown_num{num}.png", 4)


def load_panel_large(scale=3):
    return _load("large_horizontal_panel.png", scale)

def load_panel_square(scale=3):
    return _load("large_square_panel.png", scale)

def load_panel_medium(scale=3):
    return _load("medium_horizontal_panel.png", scale)


def load_tick(scale=2):
    return _load("tick_icon.png", scale)

def load_x(scale=2):
    return _load("x_icon.png", scale)

def load_sound_icon(scale=2):
    return _load("sound_icon.png", scale)

def load_settings_icon(scale=2):
    return _load("settings_icon.png", scale)

def load_thin_vertical(scale=2):
    return _load("thin_vertical_slip.png", scale)

def load_small_square_h(scale=2):
    return _load("Small square(horizontal).png", scale)

def load_small_square_v(scale=2):
    return _load("Small square(vertical).png", scale)

def load_medium_panel(scale=3):
    return _load("medium_horizontal_panel.png", scale)
