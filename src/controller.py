import pygame
import subprocess
import sys

AXIS_DEADZONE = 0.3
AXIS_THRESHOLD = 0.3

_XBOX_ACTIONS = {
    0: "jump",         # A
    1: "attack_alt",   # B → heavy attack
    2: "attack",       # X → light attack
    3: "special",      # Y
    4: "shield",       # LB
    5: "right",        # RB
}

_PS4_ACTIONS = {
    0: "jump",         # X (cross)
    1: "attack_alt",   # O (circle) → heavy attack
    2: "attack",       # [] (square) → light attack
    3: "special",      # Triangle
    4: "shield",       # L1
    5: "right",        # R1
    11: "jump",        # D-pad Up
    12: "crouch",      # D-pad Down
    13: "left",        # D-pad Left
    14: "right",       # D-pad Right
}

_PS4_KEYWORDS = ["ps4", "dualshock", "wireless controller", "sony", "ps5", "dualsense"]


def _is_ps4_controller(name):
    name_lower = name.lower()
    return any(kw in name_lower for kw in _PS4_KEYWORDS)


def open_bluetooth_settings():
    try:
        if sys.platform == "win32":
            subprocess.Popen(["cmd", "/c", "start", "ms-settings:bluetooth"], shell=True)
            return True
    except Exception:
        pass
    return False


def get_connected_controllers():
    raw = []
    for i in range(pygame.joystick.get_count()):
        try:
            j = pygame.joystick.Joystick(i)
            name = j.get_name()
            raw.append((i, name, _is_ps4_controller(name)))
        except Exception:
            pass

    has_virtual = any("xbox" in n.lower() or "360" in n.lower() for _, n, _ in raw)
    if has_virtual:
        return [(i, n, ps4) for i, n, ps4 in raw if not ps4]
    return raw


def handle_controller_events(event):
    if event.type == pygame.JOYDEVICEADDED:
        idx = event.device_index
        try:
            j = pygame.joystick.Joystick(idx)
            j.init()
            return ("connected", idx, j.get_name())
        except Exception:
            return ("connected", idx, "Unknown")
    elif event.type == pygame.JOYDEVICEREMOVED:
        return ("disconnected", event.instance_id, "Unknown")
    return None


class GamepadInput:
    def __init__(self, joystick_index=0, ctrl=None):
        if joystick_index >= pygame.joystick.get_count():
            raise ValueError("No controller at index {}".format(joystick_index))
        self.joy = pygame.joystick.Joystick(joystick_index)
        self.joy.init()
        self.index = joystick_index
        self.name = self.joy.get_name()
        self.is_ps4 = _is_ps4_controller(self.name)
        self.alive = True
        self._prev_buttons = [False] * self.joy.get_numbuttons()
        self._raw_state = {}
        self.ctrl = ctrl or {}

    def refresh(self):
        self._raw_state.clear()

        try:
            num_axes = self.joy.get_numaxes()
            num_buttons = self.joy.get_numbuttons()
            num_hats = self.joy.get_numhats()
        except pygame.error:
            self.alive = False
            return

        action_map = _PS4_ACTIONS if self.is_ps4 else _XBOX_ACTIONS

        for i in range(num_axes):
            try:
                val = self.joy.get_axis(i)
            except pygame.error:
                continue

            if i == 0:
                if val < -AXIS_THRESHOLD:
                    key = self.ctrl.get("left")
                    if key: self._raw_state[key] = True
                elif val > AXIS_THRESHOLD:
                    key = self.ctrl.get("right")
                    if key: self._raw_state[key] = True
            elif i == 1:
                if val < -AXIS_THRESHOLD:
                    key = self.ctrl.get("jump")
                    if key: self._raw_state[key] = True
                elif val > AXIS_THRESHOLD:
                    key = self.ctrl.get("crouch")
                    if key: self._raw_state[key] = True

        for i in range(num_buttons):
            try:
                pressed = self.joy.get_button(i) > 0.5
            except pygame.error:
                continue
            just_pressed = pressed and not self._prev_buttons[i]
            self._prev_buttons[i] = pressed

            action = action_map.get(i)
            if action:
                key = self.ctrl.get(action)
                if key and (just_pressed or pressed):
                    self._raw_state[key] = True

        if num_hats > 0:
            try:
                hat = self.joy.get_hat(0)
            except pygame.error:
                hat = (0, 0)
            if hat[0] < 0:
                key = self.ctrl.get("left")
                if key: self._raw_state[key] = True
            elif hat[0] > 0:
                key = self.ctrl.get("right")
                if key: self._raw_state[key] = True
            if hat[1] > 0:
                key = self.ctrl.get("jump")
                if key: self._raw_state[key] = True
            elif hat[1] < 0:
                key = self.ctrl.get("crouch")
                if key: self._raw_state[key] = True

    def __getitem__(self, key):
        return self._raw_state.get(key, False)

    def __len__(self):
        return 1


class MenuController:
    """Provides menu navigation from the first connected gamepad.
    X (button 0) = cancel/back, O (button 1) = confirm/go.
    D-pad or left stick for navigation. Includes repeat delay."""

    INITIAL_DELAY = 0.5
    REPEAT_DELAY = 0.12

    def __init__(self):
        self._prev_buttons = {}
        self.confirm = False
        self.cancel = False
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.any_button = False
        self._joy = None
        self._connected = False
        self._dir_state = {"left": False, "right": False, "up": False, "down": False}
        self._dir_timer = {"left": 0.0, "right": 0.0, "up": 0.0, "down": 0.0}
        self._last_tick = 0.0

    def refresh(self):
        self.confirm = False
        self.cancel = False
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.any_button = False

        count = pygame.joystick.get_count()
        if count == 0:
            self._connected = False
            self._joy = None
            return

        if self._joy is None or not self._joy.get_init():
            try:
                self._joy = pygame.joystick.Joystick(0)
                self._joy.init()
                self._connected = True
                self._prev_buttons = {}
                self._dir_state = {"left": False, "right": False, "up": False, "down": False}
                self._dir_timer = {"left": 0.0, "right": 0.0, "up": 0.0, "down": 0.0}
                self._last_tick = 0.0
            except Exception:
                self._connected = False
                self._joy = None
                return

        joy = self._joy
        now = pygame.time.get_ticks() / 1000.0
        dt = now - self._last_tick if self._last_tick > 0 else 0.0
        self._last_tick = now
        try:
            num_buttons = joy.get_numbuttons()
            num_axes = joy.get_numaxes()
            num_hats = joy.get_numhats()
        except pygame.error:
            self._connected = False
            self._joy = None
            return

        for i in range(num_buttons):
            try:
                pressed = joy.get_button(i) > 0.5
            except pygame.error:
                continue
            was_pressed = self._prev_buttons.get(i, False)
            just_pressed = pressed and not was_pressed
            self._prev_buttons[i] = pressed

            if just_pressed:
                self.any_button = True
                if i == 0:
                    self.cancel = True
                elif i == 1:
                    self.confirm = True

        raw_dir = {"left": False, "right": False, "up": False, "down": False}

        for i in range(num_axes):
            try:
                val = joy.get_axis(i)
            except pygame.error:
                continue
            if i == 0:
                if val < -AXIS_THRESHOLD:
                    raw_dir["left"] = True
                elif val > AXIS_THRESHOLD:
                    raw_dir["right"] = True
            elif i == 1:
                if val < -AXIS_THRESHOLD:
                    raw_dir["up"] = True
                elif val > AXIS_THRESHOLD:
                    raw_dir["down"] = True

        if num_hats > 0:
            try:
                hat = joy.get_hat(0)
            except pygame.error:
                hat = (0, 0)
            if hat[0] < 0:
                raw_dir["left"] = True
            elif hat[0] > 0:
                raw_dir["right"] = True
            if hat[1] > 0:
                raw_dir["up"] = True
            elif hat[1] < 0:
                raw_dir["down"] = True

        for d in ("left", "right", "up", "down"):
            held = raw_dir[d]
            was_held = self._dir_state[d]
            self._dir_state[d] = held

            if held and not was_held:
                setattr(self, d, True)
                self._dir_timer[d] = 0.0
            elif held and was_held:
                self._dir_timer[d] += dt
                if self._dir_timer[d] >= self.INITIAL_DELAY:
                    if self._dir_timer[d] - dt < self.INITIAL_DELAY:
                        setattr(self, d, True)
                    elif self._dir_timer[d] >= self.INITIAL_DELAY + self.REPEAT_DELAY:
                        setattr(self, d, True)
                        self._dir_timer[d] = self.INITIAL_DELAY
            else:
                self._dir_timer[d] = 0.0

    @property
    def connected(self):
        return self._connected


class InputModePopup:
    """Confirmation popup when switching input modes (keyboard <-> controller).
    Returns True if confirmed, False if cancelled, None if still open."""

    def __init__(self, message="Switch to keyboard mode?"):
        self.message = message
        self._sel = 0
        self._done = False
        self._result = None

    def handle_event(self, event, menu_ctrl=None):
        if self._done:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._sel = 0
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._sel = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._result = self._sel == 0
                self._done = True
            elif event.key in (pygame.K_ESCAPE, pygame.K_n):
                self._result = False
                self._done = True
            elif event.key == pygame.K_y:
                self._result = True
                self._done = True
        if menu_ctrl:
            if menu_ctrl.left:
                self._sel = 0
            elif menu_ctrl.right:
                self._sel = 1
            elif menu_ctrl.confirm:
                self._result = self._sel == 0
                self._done = True
            elif menu_ctrl.cancel:
                self._result = False
                self._done = True

    def update(self):
        if self._done:
            return self._result
        return None

    @property
    def is_open(self):
        return not self._done

    def draw(self, surface, font_title, font_btn):
        from src.ui_theme import draw_glass_panel, outlined_text
        import math

        sw, sh = surface.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pw, ph = 440, 180
        panel = pygame.Rect(0, 0, pw, ph)
        panel.center = (sw // 2, sh // 2)
        draw_glass_panel(surface, panel, radius=18)

        outlined_text(surface, self.message, font_title, (sw // 2, sh // 2 - 50),
                      (255, 255, 255), outline_width=2, outline_color=(10, 10, 30), center=True)

        btn_w, btn_h = 120, 36
        btns = [("YES", 0), ("NO", 1)]
        for label, idx in btns:
            bx = sw // 2 - 70 + idx * 140
            by = sh // 2 + 20
            btn_rect = pygame.Rect(0, 0, btn_w, btn_h)
            btn_rect.center = (bx, by)
            is_sel = self._sel == idx
            bg = (80, 180, 80) if idx == 0 and is_sel else (180, 60, 60) if idx == 1 and is_sel else (60, 60, 80)
            border_c = (255, 220, 50) if is_sel else (100, 100, 120)
            bw = 3 if is_sel else 2
            pygame.draw.rect(surface, bg, btn_rect, border_radius=10)
            pygame.draw.rect(surface, border_c, btn_rect, bw, border_radius=10)
            txt_c = (255, 255, 255) if is_sel else (180, 180, 180)
            outlined_text(surface, label, font_btn, btn_rect.center, txt_c,
                          outline_width=1, outline_color=(10, 10, 10), center=True)

        hint_f = pygame.font.SysFont("arial", 14)
        hint = hint_f.render("ARROWS to select  |  ENTER confirm  |  ESC cancel", True, (140, 140, 160))
        surface.blit(hint, hint.get_rect(center=(sw // 2, sh // 2 + 65)))

        return self._result
