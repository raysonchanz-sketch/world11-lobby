import pygame
import math
import random
from constants import *
from src.animation import Animator, MARIO_ANIMATIONS, LUIGI_ANIMATIONS, YOSHI_ANIMATIONS, DONKEY_KONG_ANIMATIONS

KNOCKBACK_FRICTION = 0.051
HELPLESS_SPECIALS = set()  # Specials that cause helplessness (e.g. recovery up-B)

def apply_knockback_decay(vx_ext, vy_ext):
    magnitude = math.sqrt(vx_ext**2 + vy_ext**2)
    if magnitude <= 0:
        return 0.0, 0.0
    new_magnitude = max(0.0, magnitude - KNOCKBACK_FRICTION)
    scale = new_magnitude / magnitude
    return vx_ext * scale, vy_ext * scale

def calculate_hitlag(damage):
    return math.floor(4 + damage / 4.0)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_loader, character="mario", controls=None):
        super().__init__()
        char_anims = {
            "mario": (MARIO_ANIMATIONS, 24, 44),
            "luigi": (LUIGI_ANIMATIONS, 24, 32),
            "yoshi": (YOSHI_ANIMATIONS, 24, 32),
            "donkey_kong": (DONKEY_KONG_ANIMATIONS, 30, 50),
        }
        anims, hit_w, hit_h = char_anims.get(character, (MARIO_ANIMATIONS, 12, 22))
        self.animator = Animator(sprite_loader, anims)

        self.animator.set_state("idle")
        self.char = character

        stats = CHARACTER_STATS.get(character, CHARACTER_STATS["mario"])
        self.weight              = stats["weight"]
        self.run_speed           = stats["run_speed"]
        self.char_friction       = stats["friction"]
        weight_factor = 100.0 / self.weight
        self.air_speed           = stats["air_speed"] * weight_factor
        self.air_friction        = stats["air_friction"]
        self.air_accel           = stats["air_accel"] * weight_factor
        self.jump_force          = stats["jump_force"]
        self.double_jump_force   = stats["double_jump_force"]
        self.max_jumps           = stats["max_jumps"]
        self.char_gravity        = stats["gravity"]
        self.max_fall            = stats["max_fall"]
        self.fast_fall_speed     = stats["fast_fall_speed"]
        self.attack_damage       = stats["attack_damage"]
        self.attack_base_kb      = stats["attack_base_knockback"]
        self.attack_kb_growth    = stats["attack_knockback_growth"]
        self.attack_range        = stats["attack_range"]
        self.attack_frames       = stats["attack_frames"]
        self.attack_hit_start    = stats["attack_hit_start"]
        self.attack_hit_end      = stats["attack_hit_end"]
        self.attack_kb_type      = "normal"  # Per-version knockback type for combos
        
        # Aerial attack stats
        self.aerial_neutral = stats["aerial_neutral"]
        self.aerial_forward = stats["aerial_forward"]
        self.aerial_back    = stats["aerial_back"]
        self.aerial_up      = stats["aerial_up"]
        self.aerial_down    = stats["aerial_down"]
        
        # Aerial attack state
        self.aerial_attack_name = None  # Which aerial: "nair", "fair", "bair", "uair", "dair"
        self.aerial_attack_stats = None  # Current aerial's (damage, base_kb, kb_growth, range, frames, hit_start, hit_end, kb_type)
        self.aerial_lag_base = 0  # Base landing lag for current aerial

        self.pos = pygame.math.Vector2(x, y)
        self.vx_int = 0.0
        self.vy_int = 0.0
        self.vx_ext = 0.0
        self.vy_ext = 0.0
        self.on_ground = True
        self.was_on_ground = True
        self.land_timer = 0
        self.block_anim_timer = 0
        self.facing = 1
        self.jump_buffer = 0
        self.coyote_time = 6
        self.jumps_left = self.max_jumps
        self.jump_key_held = False
        self.jump_hold_frames = 0
        self.is_fast_falling = False
        self.just_double_jumped = False

        self.is_dead = False
        self.respawn_timer = 0
        self.respawn_invuln = 0
        self.hearts = LIVES
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.stomp_cooldown = 0
        self.idle_timer = 0
        self.star_timer = 0
        self.p_meter = 0
        self.counter_hit_timer = 0
        self.hit_pause_timer = 0
        self.pending_kb_vx = 0.0
        self.pending_kb_vy = 0.0
        self.hurt_buffer = 0

        self.normal_hit_h = hit_h
        self.normal_hit_w = hit_w

        self.percentage = 0
        self.attacking = 0
        self.hit_this_swing = False
        self.attack_key_held = False
        self.crouch_key_held = False

        self.special_cooldown = 0
        self.special_max_cooldown = 0
        self.special_active = 0
        self.special_name = None
        self.special_hit = False
        self.special_spawned = False
        self.special_key_held = False

        self.stale_queue = []

        # Heavy attack state
        self.heavy_attack = False      # True when doing heavy attack
        self.heavy_cooldown = 0        # Frames until heavy can be used again

        # Yoshi-specific: roll combo system
        self.roll_kb_type = stats.get("roll_kb_type", "normal")
        self.roll_heavy_bonus = stats.get("roll_heavy_bonus", 1.0)
        self.just_rolled = False       # True if roll just finished, can chain heavy
        self.just_rolled_timer = 0     # Frames left to chain heavy

        # Combo system
        self.combo_version = 0         # 0=none, 1=v1, 2=v2, 3=v3
        self.combo_type = None         # "light" or "heavy"
        self.combo_hitstun = 0         # Frames of victim hitstun remaining for combo
        self.pending_combo_version = 0 # Version to advance to when current attack ends
        self.pending_combo_type = None # Type to set when current attack ends
        self.particles = None

        # Yoshi egg roll state
        self.egg_rolling = False
        self.egg_roll_timer = 0
        self.egg_roll_hit_interval = 0

        # Yoshi player throw state
        self.grabbing = False
        self.grab_timer = 0
        self.grabbed_player = None

        # Ledge grab state
        self.ledge_grabbing = False
        self.ledge_hang_timer = 0
        self.ledge_side = 0          # +1 = grabbed left ledge (faces right), -1 = right ledge (faces left)
        self.ledge_invuln = 0
        self.ledge_action = None     # None, "getup", "jump", "drop", "attack"
        self.ledge_action_timer = 0

        # Input buffering: store next attack input during endlag
        self.input_buffer = []       # List of (frame, input_type) tuples
        self.input_buffer_max = 8    # Buffer window in frames

        # Combo tracking
        self.combo_counter = 0       # Number of hits in current combo
        self.combo_damage = 0.0      # Total damage in current combo
        self.combo_timer = 0         # Frames until combo drops
        self.last_combo_hit = None   # (frame, damage, hitstun, attacker_lag)

        # Status effects
        self.status_effects = []     # List of {"type": ..., "timer": ..., "data": {...}}
        self.speed_mult = 1.0        # Multiplied by character ground_speed/air_speed
        self.damage_mult = 1.0       # Multiplied to outgoing damage
        self.damage_taken_mult = 1.0 # Multiplied to incoming damage
        self.kb_taken_mult = 1.0     # Multiplied to incoming knockback

        # Finisher tracking
        self.last_attack_type = None # "light", "heavy", or "fireball"/"blastshot"/etc

        self.hitstun = 0
        self.hitlag = 0
        self.flash_timer = 0

        self.landing_lag = 0
        self.l_cancel_buffer = 0
        self.helpless = False
        self.just_finished_aerial = 0
        self.gravity_skip = 0
        
        # Shield state
        self.shield_health = MAX_SHIELD_HEALTH
        self.shielding = False
        self.shield_key_held = False
        self.shield_stun = 0
        self.shield_broken = False

        # Air dodge state
        self.air_dodging = False
        self.air_dodge_timer = 0

        # Platform pass-through state
        self.drop_through = False    # True = skip platform collision this frame
        self.drop_through_key_held = False
        self.ghosting = False        # True = holding down while falling, pass through platforms

        self.rect = pygame.Rect(x, y, hit_w, self.normal_hit_h)
        self.image = None
        self.image_offset = (0, 0)

        self.ctrl = controls if controls is not None else CTRL_P1
        self.controls = self.ctrl

    def attack_hitbox(self, reach=None):
        if reach is None:
            reach = self.attack_range
        box = self.rect.copy()
        if self.facing == 1:
            box.width += reach
            box.left = self.rect.left
        else:
            box.width += reach
            box.left = self.rect.left - reach
        return box

    def special_hitbox(self, reach=55):
        box = self.rect.copy()
        box.height = int(self.rect.height * 1.4)
        box.y = self.rect.y - int(self.rect.height * 0.2)
        if self.facing == 1:
            box.width = self.rect.width + reach
            box.left = self.rect.left
        else:
            box.width = self.rect.width + reach
            box.left = self.rect.left - reach
        return box

    def aerial_hitbox(self):
        if not self.aerial_attack_stats:
            return self.rect.copy()
        reach = self.aerial_attack_stats[3]
        kb_type = self.aerial_attack_stats[7]
        box = self.rect.copy()
        if kb_type == "upward":
            box.height = self.rect.height + reach
            box.bottom = self.rect.bottom
        elif kb_type == "spike":
            box.height = self.rect.height + reach
            box.top = self.rect.top
        else:
            if self.facing == 1:
                box.width = self.rect.width + reach
                box.left = self.rect.left
            else:
                box.width = self.rect.width + reach
                box.left = self.rect.left - reach
        return box

    def heavy_hitbox(self):
        reach = int(self.attack_range * HEAVY_ATTACK_RANGE_MULT)
        box = self.rect.copy()
        if self.facing == 1:
            box.width += reach
            box.left = self.rect.left
        else:
            box.width += reach
            box.left = self.rect.left - reach
        return box

    def get_heavy_damage(self):
        return self.attack_damage * HEAVY_ATTACK_DAMAGE_MULT

    def get_heavy_base_kb(self):
        return self.attack_base_kb * HEAVY_ATTACK_KB_MULT

    def get_heavy_kb_growth(self):
        return self.attack_kb_growth * HEAVY_ATTACK_KB_MULT

    def get_aerial_attack_data(self, keys):
        if not self.on_ground and self.attacking == 0 and self.special_active == 0:
            up = keys[self.ctrl["jump"]]
            down = keys[self.ctrl["crouch"]]
            left = keys[self.ctrl["left"]]
            right = keys[self.ctrl["right"]]
            if down:
                return "dair", self.aerial_down, AERIAL_LAG_DOWN
            elif up:
                return "uair", self.aerial_up, AERIAL_LAG_UP
            elif left:
                if self.facing == -1:
                    return "fair", self.aerial_forward, AERIAL_LAG_FORWARD
                else:
                    return "bair", self.aerial_back, AERIAL_LAG_BACK
            elif right:
                if self.facing == 1:
                    return "fair", self.aerial_forward, AERIAL_LAG_FORWARD
                else:
                    return "bair", self.aerial_back, AERIAL_LAG_BACK
            else:
                return "nair", self.aerial_neutral, AERIAL_LAG_NEUTRAL
        return None, None, 0

    def get_stale_multiplier(self, move_id="attack"):
        if not self.stale_queue:
            return STALE_FRESH_BONUS
        total_reduction = 0.0
        for i, queued_id in enumerate(self.stale_queue):
            if queued_id == move_id and i < len(STALE_SLOT_MULTIPLIERS):
                total_reduction += STALE_SLOT_MULTIPLIERS[i]
        return max(STALE_MIN_MULT, 1.0 - total_reduction)

    def record_stale(self, move_id="attack"):
        self.stale_queue.append(move_id)
        if len(self.stale_queue) > 9:
            self.stale_queue.pop(0)

    def take_damage(self, base_damage, knockback_growth, base_knockback,
                    attacker_facing, weight=None, stale_mult=1.0, di_y=0,
                    kb_bonus=1.0, knockback_type="normal", attacker_percent=0,
                    combo_launch_mult=1.0):

        if self.star_timer > 0:
            return

        if self.respawn_invuln > 0:
            return

        # Release ledge when hit
        if self.ledge_grabbing:
            self.ledge_grabbing = False
            self.ledge_hang_timer = 0
            self.ledge_invuln = 0
            self.ledge_action = None
            self.ledge_action_timer = 0

        # Air dodge invincibility
        if self.air_dodging:
            elapsed = AIR_DODGE_DURATION - self.air_dodge_timer
            if AIR_DODGE_INVULN_START <= elapsed <= AIR_DODGE_INVULN_END:
                return

        self.special_active = 0
        self.special_name = None
        self.special_spawned = False
        self.special_hit = False
        self.attacking = 0
        self.hit_this_swing = False

        pd = base_damage * stale_mult
        pd *= self.damage_taken_mult
        self.percentage += pd

        P = self.percentage
        D = pd
        W = weight if weight is not None else self.weight
        S = knockback_growth
        B = base_knockback

        KB = (((2 * P + D) / 20.0) * (200.0 / (W + 100.0)) * 1.4 + 18) * S + B

        rage = 1.0 + min(attacker_percent / 100.0, 1.0) * RAGE_SCALE
        rage = min(rage, RAGE_MAX_MULT)
        KB *= rage * kb_bonus * self.kb_taken_mult

        launch_speed = min(KB * LAUNCH_SPEED_SCALE * combo_launch_mult, 25.0)

        angle = 45.0
        if di_y != 0:
            launch_angle = 45.0
            stick_angle = 90.0 if di_y < 0 else 270.0
            delta = math.sin(math.radians(stick_angle - launch_angle))
            angle += delta * DI_MAX_ANGLE
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        if knockback_type == "straight":
            self.pending_kb_vx = launch_speed * attacker_facing
            self.pending_kb_vy = 0
        elif knockback_type == "upward":
            self.pending_kb_vx = 0
            self.pending_kb_vy = -launch_speed
        else:
            self.pending_kb_vx = launch_speed * cos_a * attacker_facing
            self.pending_kb_vy = -launch_speed * sin_a

        self.hit_pause_timer = HIT_PAUSE_FRAMES
        self.hitlag = calculate_hitlag(pd)
        weight_modifier = self.weight / 100.0
        hitstun_from_damage = math.floor(pd * 0.4 * weight_modifier + 12)
        hitstun_from_kb = max(4, int(KB * 0.4))
        self.hitstun = max(self.hitstun, max(hitstun_from_damage, hitstun_from_kb))
        self.flash_timer = 8
        self.dashing = False
        self.is_fast_falling = False
        if KB >= KB_LAUNCH_THRESHOLD or knockback_type in ("upward", "spike"):
            self.on_ground = False
        self.jumps_left = self.max_jumps
        self.helpless = False

    def take_hit(self, damage=5):
        self.take_damage(damage, 0.8, 8, -self.facing, self.weight)

    def is_true_combo(self, damage, attacker_lag, knockback_growth=0, base_knockback=0, kb_bonus=1.0):
        """Check if attacker's next attack is a true combo on this defender.
        
        True combo = defender hitstun > attacker total lock time.
        Frame advantage = hitstun - attacker_lag
        Uses max of damage-based and knockback-based hitstun (matches take_damage).
        """
        weight_modifier = self.weight / 100.0
        hitstun_from_damage = math.floor(damage * 0.4 * weight_modifier + 12)
        P = self.percentage
        D = damage
        W = self.weight
        KB = (((2 * P + D) / 20.0) * (200.0 / (W + 100.0)) * 1.4 + 18) * knockback_growth + base_knockback
        hitstun_from_kb = max(4, int(KB * 0.4)) if knockback_growth > 0 else 0
        hitstun = max(hitstun_from_damage, hitstun_from_kb)
        advantage = hitstun - attacker_lag
        return advantage >= 0

    def is_counter_hit_vulnerable(self):
        """Return True if this player is in attack startup (before impact frame).
        Getting hit during this state triggers a counter-hit on the attacker."""
        if self.attacking <= 0 or self.hitstun > 0:
            return False
        if self.aerial_attack_stats:
            total_frames = self.aerial_attack_stats[4]
            hit_start = self.aerial_attack_stats[5]
            current = total_frames - self.attacking
            return current < hit_start
        else:
            total_frames = self.attack_frames
            hit_start = self.attack_hit_start
            current = total_frames - self.attacking
            return current < hit_start

    def trigger_counter_hit(self):
        """Flash the player to show they got counter-hit."""
        self.counter_hit_timer = COUNTER_HIT_VISUAL_DURATION

    def buffer_input(self, input_type):
        """Store an input during endlag to be consumed on first actionable frame."""
        self.input_buffer = [(age + 1, itype) for age, itype in self.input_buffer]
        self.input_buffer = [(age, itype) for age, itype in self.input_buffer if age < self.input_buffer_max]
        self.input_buffer.append((0, input_type))

    def consume_buffered_input(self):
        """Check and consume buffered inputs when becoming actionable."""
        if self.input_buffer:
            _, input_type = self.input_buffer.pop(0)
            return input_type
        return None

    def update_combo(self, damage):
        """Track combo state. Call when landing a hit."""
        if self.combo_timer > 0:
            self.combo_counter += 1
        else:
            self.combo_counter = 1
            self.combo_damage = 0.0
        self.combo_damage += damage
        self.combo_timer = 45

    def advance_combo(self):
        """Advance combo version when a hit connects. Called from main.py.
        Stores pending advance — applied when current attack ends."""
        combo_tables = {"yoshi": (YOSHI_LIGHT_COMBO, YOSHI_HEAVY_COMBO),
                        "mario": (MARIO_LIGHT_COMBO, MARIO_HEAVY_COMBO),
                        "luigi": (LUIGI_LIGHT_COMBO, LUIGI_HEAVY_COMBO),
                        "donkey_kong": (DK_LIGHT_COMBO, DK_HEAVY_COMBO)}
        if self.char not in combo_tables:
            return
        next_ver = min(self.combo_version + 1, 3)
        if next_ver > self.combo_version:
            self.pending_combo_version = next_ver
            self.pending_combo_type = self.combo_type

    def check_finisher(self, victim, special_name=None):
        """Check if the last attack + current attack triggers a finisher effect."""
        if not self.last_attack_type or self.char not in FINISHER_EFFECTS:
            return
        table = FINISHER_EFFECTS[self.char]
        if self.combo_type == "light" and self.last_attack_type == "heavy":
            key = ("heavy", "light")
            if key in table:
                victim.apply_status(table[key])
            # Yoshi extra: heavy+light also applies damage amp
            extra_key = ("heavy", "light_extra")
            if extra_key in table:
                victim.apply_status(table[extra_key])
        elif special_name:
            key = (self.last_attack_type, special_name)
            if key in table:
                victim.apply_status(table[key])

    def apply_status(self, effect):
        """Apply a status effect from a finisher."""
        effect_type = effect["type"]
        if effect_type == "stun":
            duration = effect.get("duration", 20)
            self.hitstun = max(self.hitstun, duration)
            self.vx_ext = 0
            self.vy_ext = 0
            extra = effect.get("extra_hitstun", 0)
            if extra > 0:
                self.hitstun += extra
        elif effect_type == "slow":
            self.status_effects.append({
                "type": "slow",
                "timer": effect["duration"],
                "data": {"speed_mult": effect["speed_mult"], "damage_mult": effect.get("damage_mult", 1.0)},
            })
        elif effect_type == "fire_dot":
            self.status_effects.append({
                "type": "fire_dot",
                "timer": effect["total_ticks"] * effect["tick_interval"],
                "data": {
                    "damage_per_tick": effect["damage_per_tick"],
                    "tick_interval": effect["tick_interval"],
                    "total_ticks": effect["total_ticks"],
                    "ticks_done": 0,
                    "tick_timer": 0,
                    "kb_mult": effect.get("kb_mult", 1.0),
                },
            })
        elif effect_type == "kb_amp":
            self.status_effects.append({
                "type": "kb_amp",
                "timer": effect["duration"],
                "data": {"kb_taken_mult": effect["kb_taken_mult"]},
            })
        elif effect_type == "damage_amp":
            self.status_effects.append({
                "type": "damage_amp",
                "timer": effect["duration"],
                "data": {"damage_taken_mult": effect["damage_taken_mult"]},
            })
        elif effect_type == "hitstun_amp":
            self.status_effects.append({
                "type": "hitstun_amp",
                "timer": effect["duration"],
                "data": {
                    "extra_hitstun": effect["extra_hitstun"],
                    "damage_dealt_mult": effect.get("damage_dealt_mult", 1.0),
                },
            })

    def update_status_effects(self):
        """Process active status effects each frame. Called from update()."""
        self.speed_mult = 1.0
        self.damage_mult = 1.0
        self.damage_taken_mult = 1.0
        self.kb_taken_mult = 1.0

        remaining = []
        for eff in self.status_effects:
            eff["timer"] -= 1
            if eff["timer"] <= 0:
                continue
            etype = eff["type"]
            d = eff["data"]
            if etype == "slow":
                self.speed_mult *= d["speed_mult"]
                self.damage_mult *= d["damage_mult"]
            elif etype == "fire_dot":
                d["tick_timer"] += 1
                if d["tick_timer"] >= d["tick_interval"]:
                    d["tick_timer"] = 0
                    d["ticks_done"] += 1
                    self.percentage += d["damage_per_tick"]
                    self.flash_timer = 4
            elif etype == "kb_amp":
                self.kb_taken_mult *= d["kb_taken_mult"]
            elif etype == "damage_amp":
                self.damage_taken_mult *= d["damage_taken_mult"]
            elif etype == "hitstun_amp":
                self.damage_mult *= d.get("damage_dealt_mult", 1.0)
            remaining.append(eff)
        self.status_effects = remaining
    
    def take_shield_hit(self, damage, attacker_facing):
        if not self.shielding or self.shield_health <= 0:
            return False
        
        # Reduce shield health based on damage
        self.shield_health = max(0, self.shield_health - damage)
        
        # Calculate shield stun
        ground_stun = math.floor(damage * SHIELD_STUN_GROUND_MULT) + SHIELD_STUN_BASE
        shield_stun = max(ground_stun, SHIELD_STUN_MIN)
        
        # Apply shield stun
        self.shield_stun = shield_stun
        self.hitstun = shield_stun
        
        # Calculate shield pushback
        pushback = (damage * SHIELD_PUSHBACK_DEFENDER) + 2
        self.vx_ext = pushback * attacker_facing
        
        # Check if shield breaks
        if self.shield_health <= 0:
            self.shield_broken = True
            self.shield_stun = SHIELD_BREAK_STUN
            self.hitstun = SHIELD_BREAK_STUN
            self.shielding = False
        
        return True
    
    def apply_shield_pushback_to_attacker(self, damage, defender_facing):
        pushback = (damage * SHIELD_PUSHBACK_ATTACKER) + 2
        self.vx_ext = pushback * defender_facing
        # Attacker also gets shield stun (frame advantage system)
        ground_stun = math.floor(damage * SHIELD_STUN_GROUND_MULT) + SHIELD_STUN_BASE
        shield_stun = max(ground_stun, SHIELD_STUN_MIN)
        self.hitstun = max(self.hitstun, shield_stun)

    def start_air_dodge(self, keys):
        self.air_dodging = True
        self.air_dodge_timer = AIR_DODGE_DURATION
        self.helpless = True
        self.attacking = 0
        self.hit_this_swing = False
        self.special_active = 0
        self.special_name = None
        
        # Directional boost from stick
        dodge_vx = 0.0
        dodge_vy = 0.0
        if keys[self.ctrl["left"]]:
            dodge_vx = -AIR_DODGE_SPEED
        elif keys[self.ctrl["right"]]:
            dodge_vx = AIR_DODGE_SPEED
        if keys[self.ctrl["jump"]]:
            dodge_vy = -AIR_DODGE_SPEED
        elif keys[self.ctrl["crouch"]]:
            dodge_vy = AIR_DODGE_SPEED * 0.5
        
        self.vx_int = dodge_vx
        self.vy_int = dodge_vy

    def handle_input(self, keys):
        if self.is_dead:
            return

        # --- Ledge actions ---
        if self.ledge_grabbing and self.ledge_action is None:
            jump_pressed = keys[self.ctrl["jump"]]
            down_pressed = keys[self.ctrl["crouch"]]
            special_pressed = keys[self.ctrl["special"]]
            attack_pressed = keys[self.ctrl["attack"]] or keys[self.ctrl["attack_alt"]]
            if jump_pressed:
                self._ledge_getup()
                return
            elif special_pressed:
                self._ledge_jump()
                return
            elif down_pressed:
                self._ledge_drop()
                return
            elif attack_pressed:
                self._ledge_attack()
                return
            return  # Block all other input while on ledge

        is_normal_attack = keys[self.ctrl["attack"]]
        is_heavy_attack = keys[self.ctrl["attack_alt"]]
        any_attack = is_normal_attack or is_heavy_attack
        shield_pressed = keys[self.ctrl["shield"]]
        crouch_pressed = keys[self.ctrl["crouch"]]
        crouch_just_pressed = crouch_pressed and not self.crouch_key_held
        self.crouch_key_held = crouch_pressed

        if self.l_cancel_buffer > 0:
            self.l_cancel_buffer -= 1
        trigger_pressed = (keys[self.ctrl["attack"]] or keys[self.ctrl["attack_alt"]])
        if trigger_pressed:
            self.l_cancel_buffer = 8

        if self.landing_lag > 0:
            self.landing_lag -= 1
            self.vx_int = 0
            self.jump_buffer = max(0, self.jump_buffer - 1)
            self.attack_key_held = any_attack
            self.shield_key_held = shield_pressed
            if keys[self.ctrl["attack"]]:
                self.buffer_input("attack")
            elif keys[self.ctrl["attack_alt"]]:
                self.buffer_input("heavy")
            elif keys[self.ctrl["special"]]:
                self.buffer_input("special")
            return
        
        # During air dodge, only allow air dodge timer to tick
        if self.air_dodging:
            self.jump_buffer = max(0, self.jump_buffer - 1)
            self.attack_key_held = any_attack
            self.shield_key_held = shield_pressed
            return

        # Shield / Yoshi block (Q key)
        if self.char == "yoshi":
            # Yoshi block: works ground + air
            if (shield_pressed and
                not self.shield_key_held and
                self.hitstun <= 0 and
                self.attacking == 0 and
                self.special_active == 0 and
                not self.egg_rolling and
                not self.helpless):
                if self.shield_health > 0 and not self.shield_broken:
                    self.shielding = True
                    self.block_anim_timer = 10
            if not shield_pressed and self.shield_key_held:
                self.shielding = False
        else:
            if (shield_pressed and 
                not self.shield_key_held and 
                self.hitstun <= 0 and
                self.attacking == 0 and
                self.special_active == 0 and
                not self.air_dodging and
                not self.helpless):
                
                if self.on_ground and self.shield_health > 0 and not self.shield_broken:
                    self.shielding = True
                    self.block_anim_timer = 10
                elif not self.on_ground:
                    self.start_air_dodge(keys)
            
            if not shield_pressed and self.shield_key_held:
                self.shielding = False
        
        self.shield_key_held = shield_pressed
        
        # Shield health management
        if self.shielding:
            if self.shield_health > 0:
                self.shield_health = max(0, self.shield_health - SHIELD_DECAY_RATE)
            else:
                # Shield breaks
                self.shielding = False
                self.shield_broken = True
                self.shield_stun = SHIELD_BREAK_STUN
                self.hitstun = SHIELD_BREAK_STUN
        else:
            # Regenerate shield health when not shielding
            if self.shield_health < MAX_SHIELD_HEALTH:
                self.shield_health = min(MAX_SHIELD_HEALTH, self.shield_health + SHIELD_REGEN_RATE)
        
        # Shield stun
        if self.shield_stun > 0:
            self.shield_stun -= 1
            if self.shield_stun <= 0:
                self.shield_broken = False
            self.attack_key_held = any_attack
            self.shield_key_held = shield_pressed
            return
        
        # If shielding, prevent movement (except for shield button release which is handled above)
        if self.shielding:
            self.vx_int = 0  # Stop horizontal movement when shielding
            self.jump_buffer = max(0, self.jump_buffer - 1)
            return

        if self.helpless:
            if not self.on_ground:
                x_stick = 0.0
                if keys[self.ctrl["left"]]:
                    x_stick = -1.0
                    self.facing = -1
                elif keys[self.ctrl["right"]]:
                    x_stick = 1.0
                    self.facing = 1
                if abs(x_stick) > AIR_DRIFT_DEADZONE:
                    effective_air_speed = self.air_speed * self.speed_mult
                    if x_stick > 0:
                        if self.vx_int < effective_air_speed:
                            self.vx_int = min(self.vx_int + self.air_accel, effective_air_speed)
                    elif x_stick < 0:
                        if self.vx_int > -effective_air_speed:
                            self.vx_int = max(self.vx_int - self.air_accel, -effective_air_speed)
                else:
                    if self.vx_int > 0:
                        self.vx_int = max(0, self.vx_int - self.air_friction)
                    elif self.vx_int < 0:
                        self.vx_int = min(0, self.vx_int + self.air_friction)
                self.jump_buffer = max(0, self.jump_buffer - 1)
                return
            else:
                self.helpless = False

        if self.hitstun > 0:
            if self.on_ground:
                self.vx_int *= self.char_friction
                if abs(self.vx_int) < 0.1:
                    self.vx_int = 0
            else:
                if self.vx_int > 0:
                    self.vx_int = max(0, self.vx_int - self.air_friction)
                elif self.vx_int < 0:
                    self.vx_int = min(0, self.vx_int + self.air_friction)
            self.jump_buffer = max(0, self.jump_buffer - 1)
            self.attack_key_held = any_attack
            self.shield_key_held = shield_pressed
            return

        special_pressed = keys[self.ctrl["special"]]
        if (special_pressed and
            not self.special_key_held and
            self.special_cooldown <= 0 and
            self.special_active == 0):

            if self.char == "mario":
                if self.last_attack_type == "light":
                    self.special_name = "fire_punch"
                    self.special_active = FIRE_PUNCH_ACTIVE_FRAMES
                    self.special_hit = False
                    self.special_cooldown = FIRE_PUNCH_COOLDOWN
                    self.special_max_cooldown = FIRE_PUNCH_COOLDOWN
                    self.last_attack_type = "fire_punch"
                else:
                    self.special_name = "hammer_smash"
                    self.special_active = HAMMER_SMASH_ACTIVE_FRAMES
                    self.special_hit = False
                    self.special_cooldown = HAMMER_SMASH_COOLDOWN
                    self.special_max_cooldown = HAMMER_SMASH_COOLDOWN
                    self.last_attack_type = "hammer_smash"
            elif self.char == "luigi":
                if self.last_attack_type == "light":
                    self.special_name = "blastshot"
                    self.special_active = 10
                    self.special_hit = False
                    self.special_cooldown = 30
                    self.special_max_cooldown = 30
                    self.last_attack_type = "blastshot"
                else:
                    self.special_name = "head_drill"
                    self.special_active = HEAD_DRILL_ACTIVE_FRAMES
                    self.special_hit = False
                    self.special_cooldown = HEAD_DRILL_COOLDOWN
                    self.special_max_cooldown = HEAD_DRILL_COOLDOWN
                    self.last_attack_type = "head_drill"
            elif self.char == "donkey_kong":
                if self.last_attack_type == "light":
                    self.special_name = "barrel_throw"
                    self.special_active = BARREL_THROW_ACTIVE_FRAMES
                    self.special_hit = False
                    self.special_cooldown = BARREL_THROW_COOLDOWN
                    self.special_max_cooldown = BARREL_THROW_COOLDOWN
                    self.last_attack_type = "barrel_throw"
                else:
                    self.special_name = "barrel_smash"
                    self.special_active = BARREL_SMASH_ACTIVE_FRAMES
                    self.special_hit = False
                    self.special_cooldown = BARREL_SMASH_COOLDOWN
                    self.special_max_cooldown = BARREL_SMASH_COOLDOWN
                    self.last_attack_type = "barrel_smash"

        # Yoshi egg roll (grounded) / egg throw (airborne) — E key / special
        if (self.char == "yoshi" and
            keys[self.ctrl["special"]] and
            not self.special_key_held and
            not self.egg_rolling and
            self.special_cooldown <= 0 and
            self.attacking == 0 and
            self.special_active == 0):
            if self.on_ground:
                self.egg_rolling = True
                self.egg_roll_timer = EGG_ROLL_ACTIVE_FRAMES
                self.egg_roll_hit_interval = 0
                self.special_cooldown = EGG_ROLL_COOLDOWN
                self.special_max_cooldown = EGG_ROLL_COOLDOWN
                self.attacking = EGG_ROLL_ACTIVE_FRAMES
                self.last_attack_type = "egg_roll"
            else:
                self.special_name = "egg_throw_air"
                self.special_active = EGG_THROW_ACTIVE_FRAMES
                self.special_hit = False
                self.special_spawned = False
                self.special_cooldown = EGG_THROW_COOLDOWN
                self.special_max_cooldown = EGG_THROW_COOLDOWN
                self.last_attack_type = "egg_throw_air"

        self.special_key_held = special_pressed

        # Consume buffered input if available
        buffered = self.consume_buffered_input()

        if ((any_attack and
            not self.attack_key_held and
            self.attacking == 0 and
            self.special_active == 0 and
            not self.egg_rolling) or
            (buffered in ("attack", "heavy") and self.attacking == 0)):

            # Update facing toward movement direction when attacking
            if keys[self.ctrl["left"]]:
                self.facing = -1
            elif keys[self.ctrl["right"]]:
                self.facing = 1

            # Heavy attack combo
            if is_heavy_attack and self.on_ground and self.heavy_cooldown <= 0:
                combo_tables = {"yoshi": YOSHI_HEAVY_COMBO, "mario": MARIO_HEAVY_COMBO, "luigi": LUIGI_HEAVY_COMBO, "donkey_kong": DK_HEAVY_COMBO}
                heavy_table = combo_tables.get(self.char)
                if heavy_table:
                    if self.combo_version == 0:
                        self.combo_version = random.randint(1, 3)
                    self.combo_type = "heavy"
                    self.last_attack_type = "heavy"
                    self.heavy_cooldown = HEAVY_ATTACK_COOLDOWN
                    combo_stats = heavy_table[self.combo_version]
                    self.attack_damage    = combo_stats[0]
                    self.attack_base_kb   = combo_stats[1]
                    self.attack_kb_growth = combo_stats[2]
                    self.attack_frames    = combo_stats[3]
                    self.attack_hit_start = combo_stats[4]
                    self.attack_hit_end   = combo_stats[5]
                    self.attack_kb_type   = combo_stats[6]
                else:
                    self.attack_frames    = HEAVY_ATTACK_FRAMES
                    self.attack_hit_start = HEAVY_ATTACK_HIT_START
                    self.attack_hit_end   = HEAVY_ATTACK_HIT_END
                self.attacking = self.attack_frames
                self.hit_this_swing = False
                self.heavy_attack = True
                self.dashing = False
                self.heavy_cooldown = HEAVY_ATTACK_COOLDOWN
                self.aerial_attack_name = None
                self.aerial_attack_stats = None
                self.aerial_lag_base = 0

            # Aerial attack
            elif not self.on_ground:
                # Update facing toward movement direction
                if keys[self.ctrl["left"]]:
                    self.facing = -1
                elif keys[self.ctrl["right"]]:
                    self.facing = 1
                aerial_name, aerial_stats, aerial_lag = self.get_aerial_attack_data(keys)
                if aerial_stats:
                    self.attacking = aerial_stats[4]
                    self.hit_this_swing = False
                    self.aerial_attack_name = aerial_name
                    self.aerial_attack_stats = aerial_stats
                    self.aerial_lag_base = aerial_lag
                else:
                    self.attacking = self.aerial_neutral[4]
                    self.hit_this_swing = False
                    self.aerial_attack_name = "nair"
                    self.aerial_attack_stats = self.aerial_neutral
                    self.aerial_lag_base = AERIAL_LAG_NEUTRAL
                self.heavy_attack = False

            # Normal ground attack (combo system)
            elif self.on_ground:
                combo_tables = {"yoshi": YOSHI_LIGHT_COMBO, "mario": MARIO_LIGHT_COMBO, "luigi": LUIGI_LIGHT_COMBO, "donkey_kong": DK_LIGHT_COMBO}
                light_table = combo_tables.get(self.char)
                if light_table:
                    if self.combo_version == 0:
                        self.combo_version = random.randint(1, 3)
                    self.combo_type = "light"
                    self.last_attack_type = "light"
                    combo_stats = light_table[self.combo_version]
                    self.attack_damage    = combo_stats[0]
                    self.attack_base_kb   = combo_stats[1]
                    self.attack_kb_growth = combo_stats[2]
                    self.attack_frames    = combo_stats[3]
                    self.attack_hit_start = combo_stats[4]
                    self.attack_hit_end   = combo_stats[5]
                    self.attack_kb_type   = combo_stats[6]
                self.attacking = self.attack_frames
                self.hit_this_swing = False
                self.heavy_attack = False
                self.dashing = False  # Cancel dash so attack animation plays
                self.aerial_attack_name = None
                self.aerial_attack_stats = None
                self.aerial_lag_base = 0

        self.attack_key_held = any_attack

        if self.special_active > 0:
            if self.on_ground:
                self.vx_int *= self.char_friction
            else:
                if self.vx_int > 0:
                    self.vx_int = max(0, self.vx_int - self.air_friction)
                elif self.vx_int < 0:
                    self.vx_int = min(0, self.vx_int + self.air_friction)
            self.jump_buffer = max(0, self.jump_buffer - 1)
            self.jump_key_held = keys[self.ctrl["jump"]]
            return

        # Freeze movement during ground attacks (can't run or flip facing)
        if self.attacking > 0 and self.on_ground and not self.dashing:
            self.vx_int *= 0.5
            if abs(self.vx_int) < 0.2:
                self.vx_int = 0
            self.jump_buffer = max(0, self.jump_buffer - 1)
            # Platform drop-through still works during attacks
            down_pressed = keys[self.ctrl["crouch"]]
            if self.on_ground and down_pressed and not self.drop_through_key_held:
                self.drop_through = True
            if not down_pressed:
                self.drop_through_key_held = False
            self.ghosting = not self.on_ground and down_pressed
            self.attack_key_held = any_attack
            self.shield_key_held = shield_pressed
            return

        base_speed = self.run_speed
        top_speed = (base_speed + (2 if self.p_meter == 100 else 0)) * self.speed_mult

        if self.on_ground and crouch_just_pressed and abs(self.vx_int) > 1.0 and not self.dashing and self.dash_cooldown <= 0:
            self.dashing = True
            self.dash_timer = 25
            self.dash_cooldown = 40  # Cooldown between slides
            if self.particles:
                self.particles.dash_dust(self.rect.centerx, self.rect.bottom, self.facing)

        if self.dashing:
            self.vx_int = 8.0 * self.facing
            self.dash_timer -= 1
            if self.dash_timer <= 0 or keys[self.ctrl["jump"]] or abs(self.vx_int) < 0.2:
                self.dashing = False
                self.hit_this_swing = False
                # Yoshi: track roll end for heavy combo window
                if self.roll_kb_type != "normal":
                    self.just_rolled = True
                    self.just_rolled_timer = 20
        else:
            if self.on_ground:
                if keys[self.ctrl["left"]]:
                    self.vx_int = max(self.vx_int - 0.4, -top_speed)
                    self.facing = -1
                elif keys[self.ctrl["right"]]:
                    self.vx_int = min(self.vx_int + 0.4, top_speed)
                    self.facing = 1
                else:
                    self.vx_int *= self.char_friction
                    if abs(self.vx_int) < 0.1:
                        self.vx_int = 0
            else:
                x_stick = 0.0
                if keys[self.ctrl["left"]]:
                    x_stick = -1.0
                    self.facing = -1
                elif keys[self.ctrl["right"]]:
                    x_stick = 1.0
                    self.facing = 1

                if abs(x_stick) > AIR_DRIFT_DEADZONE:
                    effective_air_speed = self.air_speed * self.speed_mult
                    if self.attacking > 0 and self.aerial_attack_stats:
                        effective_air_speed = self.air_speed * AERIAL_DRIFT_MULT * self.speed_mult
                    if x_stick > 0:
                        if self.vx_int < effective_air_speed:
                            self.vx_int = min(self.vx_int + self.air_accel, effective_air_speed)
                    elif x_stick < 0:
                        if self.vx_int > -effective_air_speed:
                            self.vx_int = max(self.vx_int - self.air_accel, -effective_air_speed)
                else:
                    if self.vx_int > 0:
                        self.vx_int = max(0, self.vx_int - self.air_friction)
                    elif self.vx_int < 0:
                        self.vx_int = min(0, self.vx_int + self.air_friction)

        # Platform drop-through: press down on soft platform to fall through
        down_pressed = keys[self.ctrl["crouch"]]
        if self.on_ground and down_pressed and not self.drop_through_key_held:
            self.drop_through = True
        if not down_pressed:
            self.drop_through_key_held = False

        # Platform ghosting: hold down while falling to pass through platforms
        self.ghosting = not self.on_ground and down_pressed

        if not self.on_ground and self.vy_int >= 0 and down_pressed:
            if not self.is_fast_falling:
                self.is_fast_falling = True

        jump_pressed = keys[self.ctrl["jump"]]

        if jump_pressed and not self.jump_key_held:
            self.jump_buffer = 8
            self.jump_hold_frames = 0

        if jump_pressed and self.jump_key_held:
            self.jump_hold_frames += 1

        self.jump_key_held = jump_pressed

        if self.jump_buffer > 0:
            if self.coyote_time > 0 and self.jumps_left == self.max_jumps:
                if self.jump_hold_frames <= SHORT_HOP_FRAMES and not jump_pressed:
                    self.vy_int = self.jump_force * SHORT_HOP_FORCE_MULT
                else:
                    self.vy_int = self.jump_force
                self.on_ground = False
                self.jumps_left -= 1
                self.jump_buffer = 0
                self.coyote_time = 0
                self.gravity_skip = 1  # Skip gravity on first jump frame
                ground_speed = abs(self.vx_int)
                clamped = ground_speed * JUMP_MOMENTUM_MULT
                if abs(self.vx_int) > clamped:
                    self.vx_int = clamped * (1 if self.vx_int > 0 else -1)
            elif self.jumps_left > 0 and not self.on_ground:
                self.vy_int = 0
                self.vy_int = self.double_jump_force
                self.jumps_left -= 1
                self.jump_buffer = 0
                self.just_double_jumped = True

        if not jump_pressed:
            if self.vy_int < -4 and self.jumps_left > 0:
                self.vy_int += 0.35

        self.jump_buffer = max(0, self.jump_buffer - 1)

        if abs(self.vx_int) >= self.run_speed - 0.1 and not self.dashing:
            self.p_meter = min(100, self.p_meter + 2)
        else:
            self.p_meter = max(0, self.p_meter - 4)

    def apply_gravity(self):
        if self.gravity_skip > 0:
            self.gravity_skip -= 1
            return
        if not self.on_ground:
            gravity = self.char_gravity
            if self.is_fast_falling:
                gravity *= FAST_FALL_MULT
            self.vy_int = min(self.vy_int + gravity, self.max_fall)
        else:
            self.vy_int = 0

    def _check_ledge_grab(self, tiles):
        """Check if player can grab a ledge. Called when airborne."""
        if self.ledge_grabbing or self.on_ground or self.hitstun > 0:
            return
        if self.helpless and not self.air_dodging:
            return

        px, py = self.rect.centerx, self.rect.centery
        hw, hh = self.rect.w // 2, self.rect.h // 2

        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile

            # Check left edge of solid tile
            test_left = pygame.Rect(rect.x - 1, rect.y, 2, rect.h)
            open_left = not any(
                (t[0] if isinstance(t, (list, tuple)) else t).colliderect(test_left)
                for t in tiles
            )
            if open_left:
                ledge_x = rect.x
                ledge_y = rect.y
                if (abs(px - (ledge_x - hw)) < LEDGE_GRAB_RANGE_X and
                    abs(py - ledge_y) < LEDGE_GRAB_RANGE_Y and
                    px > ledge_x):
                    self._snap_to_ledge(ledge_x, ledge_y, 1)
                    return

            # Check right edge of solid tile
            test_right = pygame.Rect(rect.right - 1, rect.y, 2, rect.h)
            open_right = not any(
                (t[0] if isinstance(t, (list, tuple)) else t).colliderect(test_right)
                for t in tiles
            )
            if open_right:
                ledge_x = rect.right
                ledge_y = rect.y
                if (abs(px - (ledge_x + hw)) < LEDGE_GRAB_RANGE_X and
                    abs(py - ledge_y) < LEDGE_GRAB_RANGE_Y and
                    px < ledge_x):
                    self._snap_to_ledge(ledge_x, ledge_y, -1)
                    return

    def _snap_to_ledge(self, ledge_x, ledge_y, side):
        """Snap player to ledge and enter hang state."""
        self.ledge_grabbing = True
        self.ledge_hang_timer = LEDGE_HANG_MAX
        self.ledge_invuln = LEDGE_GRAB_INVULN
        self.ledge_side = side
        self.ledge_action = None
        self.ledge_action_timer = 0
        self.facing = -side  # Face toward the stage

        # Snap position: hang with hands on ledge edge
        if side == 1:  # Left edge
            self.rect.right = ledge_x + 2
        else:  # Right edge
            self.rect.left = ledge_x - 2
        self.rect.top = ledge_y - 4
        self.pos.x = float(self.rect.x)
        self.pos.y = float(self.rect.y)

        # Zero out all velocity
        self.vx_int = 0
        self.vy_int = 0
        self.vx_ext = 0
        self.vy_ext = 0
        self.jumps_left = self.max_jumps
        self.helpless = False
        self.air_dodging = False
        self.air_dodge_timer = 0
        self.is_fast_falling = False
        self.on_ground = False

        # Cancel any current attack/special
        self.attacking = 0
        self.hit_this_swing = False
        self.heavy_attack = False
        self.special_active = 0
        self.special_name = None
        self.special_spawned = False
        self.dashing = False

    def move_and_collide(self, tiles, platforms=None, level_w=None, level_h=None):
        self.vx_ext, self.vy_ext = apply_knockback_decay(self.vx_ext, self.vy_ext)

        total_vx = self.vx_int + self.vx_ext
        total_vy = self.vy_int + self.vy_ext

        self.pos.x += total_vx
        self.rect.x = int(self.pos.x)
        self._collide_x(tiles, total_vx)

        prev_bottom = self.rect.bottom

        self.pos.y += total_vy
        self.rect.y = int(self.pos.y)
        was_on_ground = self.on_ground
        self._collide_y(tiles, platforms, prev_bottom, total_vy)

        if was_on_ground and not self.on_ground:
            self.coyote_time = 6
        elif self.on_ground:
            if not was_on_ground:
                # Clear air dodge on landing
                self.air_dodging = False
                self.air_dodge_timer = 0
                self.drop_through = False
                self.drop_through_key_held = False
                self.ghosting = False
                self.just_double_jumped = False
            
            if not was_on_ground and (self.attacking > 0 or self.just_finished_aerial > 0):
                if self.attacking <= 0 and self.just_finished_aerial > 0:
                    self.landing_lag = self.aerial_lag_base if self.aerial_lag_base > 0 else 6
                    self.just_finished_aerial = 0
                else:
                    is_auto_cancel = False
                    if self.aerial_attack_stats:
                        ac_start = self.aerial_attack_stats[8]
                        ac_end = self.aerial_attack_stats[9]
                        current_frame = self.aerial_attack_stats[4] - self.attacking
                        if current_frame <= ac_start or current_frame >= (self.aerial_attack_stats[4] - ac_end):
                            is_auto_cancel = True

                    if is_auto_cancel:
                        self.landing_lag = AUTO_CANCEL_LAG
                    elif self.aerial_attack_stats:
                        normal_lag = self.aerial_lag_base
                        if self.l_cancel_buffer > 0:
                            self.landing_lag = max(2, int(normal_lag * L_CANCEL_LAG_MULT))
                        else:
                            self.landing_lag = normal_lag
                    elif self.heavy_attack:
                        self.landing_lag = HEAVY_ATTACK_FRAMES // 2
                    else:
                        normal_lag = max(4, self.attack_frames // 2)
                        if self.l_cancel_buffer > 0:
                            self.landing_lag = max(2, int(normal_lag * L_CANCEL_LAG_MULT))
                        else:
                            self.landing_lag = normal_lag
                self.attacking = 0
                self.hit_this_swing = False
                self.heavy_attack = False
                self.aerial_attack_name = None
                self.aerial_attack_stats = None
                self.aerial_lag_base = 0
            self.coyote_time = 6
            self.jumps_left = self.max_jumps
            self.is_fast_falling = False
        else:
            self.coyote_time = max(0, self.coyote_time - 1)

    def _collide_x(self, tiles, total_vx):
        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                if total_vx > 0:
                    self.rect.right = rect.left
                elif total_vx < 0:
                    self.rect.left = rect.right
                self.vx_int = 0
                self.vx_ext *= -0.6  # Bounce with 60% knockback
                self.pos.x = float(self.rect.x)

    def _collide_y(self, tiles, platforms=None, prev_bottom=0, total_vy=0):
        self.on_ground = False

        collisions = []
        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                collisions.append(rect)

        if total_vy > 0:
            best_top = float('inf')
            floor_rect = None
            for r in collisions:
                if r.top < best_top:
                    best_top = r.top
                    floor_rect = r
            if floor_rect:
                self.rect.bottom = floor_rect.top
                self.on_ground = True
                self.vy_int = 0
                self.vy_ext = 0
                self.pos.y = float(self.rect.y)
        elif total_vy < 0:
            best_bottom = -float('inf')
            ceil_rect = None
            for r in collisions:
                if r.bottom > best_bottom:
                    best_bottom = r.bottom
                    ceil_rect = r
            if ceil_rect:
                self.rect.top = ceil_rect.bottom
                self.vy_int = 0
                self.vy_ext = 0
                self.pos.y = float(self.rect.y)

        if not self.on_ground and total_vy >= 0:
            ground_probe = self.rect.move(0, 2)
            for tile in tiles:
                rect = tile[0] if isinstance(tile, (list, tuple)) else tile
                if ground_probe.colliderect(rect):
                    self.on_ground = True
                    break

        # Platform pass-through: only land on platforms if not dropping through
        # Also supports "ghosting" — holding down while falling passes through
        if platforms and not self.drop_through and not self.ghosting:
            for plat in platforms:
                if self.rect.colliderect(plat):
                    feet_were_above = prev_bottom <= plat.top + 2
                    if feet_were_above and total_vy >= 0:
                        self.rect.bottom = plat.top
                        self.on_ground = True
                        self.vy_int = 0
                        self.vy_ext = 0
                        self.pos.y = float(self.rect.y)
                        break

        # Clear drop-through after one frame
        if self.drop_through:
            self.drop_through = False
            self.drop_through_key_held = True

    def _pick_animation(self, keys):
        if self.hitstun > 0 or self.hurt_buffer > 0:
            if "hurt" in self.animator.defs:
                self.animator.set_state("hurt")
            else:
                self.animator.set_state("jump")
            return

        if self.ledge_grabbing:
            if self.ledge_action == "attack":
                self.animator.set_state("light_v1")
            elif "ledge_grab" in self.animator.defs:
                self.animator.set_state("ledge_grab")
            elif "air_block" in self.animator.defs:
                self.animator.set_state("air_block")
            else:
                self.animator.set_state("jump")
            return

        if self.char == "yoshi" and self.egg_rolling:
            self.animator.set_state("egg_roll")
            return

        if self.special_active > 0 and self.special_name:
            self.animator.set_state(self.special_name)
            return

        if self.attacking > 0:
            if self.heavy_attack and self.combo_type == "heavy":
                self.animator.set_state(f"heavy_v{self.combo_version}")
            elif self.aerial_attack_name:
                if self.aerial_attack_name in ("nair", "fair", "bair"):
                    self.animator.set_state("air_light")
                elif self.aerial_attack_name in ("uair", "dair"):
                    self.animator.set_state("air_heavy")
                else:
                    self.animator.set_state("air_light")
            elif self.combo_type == "light":
                self.animator.set_state(f"light_v{self.combo_version}")
            elif self.heavy_attack:
                self.animator.set_state(f"heavy_v{self.combo_version}")
            elif self.char == "mario":
                self.animator.set_state("light_v1")
            else:
                self.animator.set_state("light_v1")
            return

        if self.dashing:
            if self.char in ("yoshi", "donkey_kong") and "roll" in self.animator.defs:
                self.animator.set_state("roll")
            elif "dash" in self.animator.defs:
                self.animator.set_state("dash")
            else:
                self.animator.set_state("run")
            return
        
        if self.shielding:
            if self.block_anim_timer > 0:
                self.block_anim_timer -= 1
                if self.on_ground:
                    self.animator.set_state("block")
                else:
                    self.animator.set_state("air_block")
            else:
                self.animator.set_state("idle")
            return

        if self.just_double_jumped and not self.on_ground:
            self.animator.set_state("double_jump")
            return

        if self.land_timer > 0 and self.on_ground and self.hitstun <= 0:
            self.animator.set_state("land")
            return

        if not self.on_ground:
            if self.vy_int > 2 and "fall" in self.animator.defs:
                self.animator.set_state("fall")
            else:
                self.animator.set_state("jump")
        elif abs(self.vx_int) > 0.3:
            self.animator.set_state("run")
            self.idle_timer = 0
        else:
            self.animator.set_state("idle")
            self.idle_timer += 1

    def update(self, keys, tiles, dt, platforms=None, level_w=None, level_h=None):
        if self.star_timer > 0: self.star_timer -= 1
        if self.respawn_invuln > 0: self.respawn_invuln -= 1

        if self.hitlag > 0:
            return

        # Hit pause: freeze in place with hurt anim before launch
        if self.hit_pause_timer > 0:
            self.hit_pause_timer -= 1
            if self.hit_pause_timer <= 0:
                # Launch: apply the pending knockback
                self.vx_ext = self.pending_kb_vx
                self.vy_ext = self.pending_kb_vy
            self._pick_animation(keys)
            self.animator.update(dt)
            frame = self.animator.get_frame(self.facing == 1)
            if frame:
                self.image = frame
            return

        # --- Ledge hang state ---
        if self.ledge_grabbing:
            self.ledge_hang_timer -= 1
            if self.ledge_invuln > 0:
                self.ledge_invuln -= 1
            # Force getup if hang timer expires
            if self.ledge_hang_timer <= 0 and self.ledge_action is None:
                self._ledge_getup()
            # Execute ledge action
            if self.ledge_action is not None:
                self.ledge_action_timer -= 1
                if self.ledge_action == "attack":
                    self.attacking = self.ledge_action_timer
                if self.ledge_action_timer <= 0:
                    self._finish_ledge_action()
            # Freeze in place while hanging
            self.vx_int = 0
            self.vy_int = 0
            self.vx_ext = 0
            self.vy_ext = 0
            self._pick_animation(keys)
            self.animator.update(dt)
            frame = self.animator.get_frame(self.facing == 1)
            if frame:
                self.image = frame
            return

        self.update_status_effects()

        if self.attacking > 0:
            self.attacking -= 1
            if self.attacking == 0:
                # Attack ended — apply pending combo advance
                if self.pending_combo_version > 0:
                    self.combo_version = self.pending_combo_version
                    self.combo_type = self.pending_combo_type
                    combo_tables = {"yoshi": (YOSHI_LIGHT_COMBO, YOSHI_HEAVY_COMBO),
                                    "mario": (MARIO_LIGHT_COMBO, MARIO_HEAVY_COMBO),
                                    "luigi": (LUIGI_LIGHT_COMBO, LUIGI_HEAVY_COMBO),
                                    "donkey_kong": (DK_LIGHT_COMBO, DK_HEAVY_COMBO)}
                    light_t, heavy_t = combo_tables.get(self.char, (None, None))
                    table = heavy_t if self.combo_type == "heavy" else light_t
                    if table:
                        stats = table[self.combo_version]
                    self.attack_damage    = stats[0]
                    self.attack_base_kb   = stats[1]
                    self.attack_kb_growth = stats[2]
                    self.attack_frames    = stats[3]
                    self.attack_hit_start = stats[4]
                    self.attack_hit_end   = stats[5]
                    self.attack_kb_type   = stats[6]
                    self.pending_combo_version = 0
                    self.pending_combo_type = None
                if not self.on_ground and self.aerial_attack_stats:
                    self.just_finished_aerial = 3  # Grace window for landing lag
        if self.just_finished_aerial > 0:
            self.just_finished_aerial -= 1
        if self.heavy_cooldown > 0: self.heavy_cooldown -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.stomp_cooldown > 0: self.stomp_cooldown -= 1
        if self.combo_hitstun > 0:
            self.combo_hitstun -= 1
            if self.combo_hitstun <= 0:
                self.combo_version = 0  # Victim escaped hitstun — combo reset
                self.pending_combo_version = 0
                self.pending_combo_type = None
                self.last_attack_type = None
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.last_combo_hit = None
        if self.just_rolled_timer > 0:
            self.just_rolled_timer -= 1
            if self.just_rolled_timer <= 0:
                self.just_rolled = False
        if self.special_cooldown > 0: self.special_cooldown -= 1
        if self.special_active > 0:
            self.special_active -= 1
            if self.special_active <= 0:
                if not self.on_ground and self.special_name in HELPLESS_SPECIALS:
                    self.helpless = True
                self.special_name = None
                self.special_spawned = False
        if self.hitstun > 0:
            self.hitstun -= 1
            if self.hitstun <= 0:
                self.hurt_buffer = 6  # Grace frames to keep hurt anim after hitstun ends
        if self.hurt_buffer > 0: self.hurt_buffer -= 1
        if self.flash_timer > 0: self.flash_timer -= 1
        if self.counter_hit_timer > 0: self.counter_hit_timer -= 1
        if self.shield_stun > 0: self.shield_stun -= 1
        
        # Air dodge timer
        if self.air_dodging:
            self.air_dodge_timer -= 1
            if self.air_dodge_timer <= 0:
                self.air_dodging = False
                if not self.on_ground:
                    self.helpless = True

        self.handle_input(keys)
        self.apply_gravity()

        # Yoshi egg roll movement
        if self.egg_rolling:
            test_rect = self.rect.move(EGG_ROLL_SPEED * self.facing, 0)
            blocked = False
            for tile in tiles:
                rect = tile[0] if isinstance(tile, (list, tuple)) else tile
                if test_rect.colliderect(rect):
                    blocked = True
                    break
            if blocked:
                self.vx_int = 0
                self.egg_rolling = False
                self.attacking = 0
            else:
                self.vx_int = EGG_ROLL_SPEED * self.facing
            self.egg_roll_timer -= 1
            self.egg_roll_hit_interval += 1
            if self.egg_roll_timer <= 0:
                self.egg_rolling = False
                self.attacking = 0

        self.was_on_ground = self.on_ground
        self.move_and_collide(tiles, platforms, level_w=level_w, level_h=level_h)

        # Ledge grab detection (when airborne, not in hitstun, not already on ledge)
        if not self.on_ground and not self.ledge_grabbing and self.hitstun <= 0:
            self._check_ledge_grab(tiles)

        # Landing detection: just landed on ground from air
        # Skip during hitstun to prevent hurt/land animation flicker
        if self.on_ground and not self.was_on_ground and self.hitstun <= 0:
            self.land_timer = 8  # frames to show land anim
            self.helpless = False
            if self.particles:
                self.particles.dust(self.rect.centerx, self.rect.bottom)

        if self.land_timer > 0:
            self.land_timer -= 1

        self._pick_animation(keys)
        self.animator.update(dt)

        frame = self.animator.get_frame(self.facing == 1)
        if frame:
            self.image = frame

    def _ledge_getup(self):
        """Normal getup from ledge."""
        self.ledge_action = "getup"
        self.ledge_action_timer = LEDGE_GETUP_LAG
        # Move player onto the platform
        if self.ledge_side == 1:  # Left edge
            self.rect.x += 12
        else:  # Right edge
            self.rect.x -= 12
        self.rect.y -= 4
        self.pos.x = float(self.rect.x)
        self.pos.y = float(self.rect.y)

    def _ledge_jump(self):
        """Jump from ledge."""
        self.ledge_action = "jump"
        self.ledge_action_timer = 8
        self.ledge_grabbing = False
        self.vx_int = LEDGE_JUMP_VX * -self.ledge_side  # Jump toward stage
        self.vy_int = LEDGE_JUMP_VY
        self.on_ground = False
        self.jumps_left = self.max_jumps - 1

    def _ledge_drop(self):
        """Drop from ledge."""
        self.ledge_action = "drop"
        self.ledge_action_timer = 4
        self.ledge_grabbing = False
        self.vy_int = LEDGE_DROP_VY
        self.vx_int = -self.ledge_side * 1.5  # Slight drift toward stage
        self.on_ground = False

    def _ledge_attack(self):
        """Ledge attack."""
        self.ledge_action = "attack"
        self.ledge_action_timer = LEDGE_ATTACK_FRAMES
        self.attacking = LEDGE_ATTACK_FRAMES
        self.attack_damage = LEDGE_ATTACK_DAMAGE
        self.attack_base_kb = LEDGE_ATTACK_KB
        self.attack_kb_growth = 0.6
        self.attack_frames = LEDGE_ATTACK_FRAMES
        self.attack_hit_start = LEDGE_ATTACK_HIT_START
        self.attack_hit_end = LEDGE_ATTACK_HIT_END
        self.attack_kb_type = "straight"
        self.hit_this_swing = False
        # Move slightly onto stage during attack
        if self.ledge_side == 1:
            self.rect.x += 6
        else:
            self.rect.x -= 6
        self.pos.x = float(self.rect.x)

    def _finish_ledge_action(self):
        """Finish the current ledge action."""
        action = self.ledge_action
        self.ledge_action = None
        self.ledge_action_timer = 0
        self.ledge_grabbing = False
        if action == "getup":
            self.on_ground = True
            self.land_timer = LEDGE_GETUP_LAG
        elif action == "attack":
            self.attacking = 0
            self.on_ground = True
            self.land_timer = LEDGE_GETUP_LAG // 2
        elif action == "drop":
            pass  # Already handled in _ledge_drop
        elif action == "jump":
            pass  # Already handled in _ledge_jump

    def die(self):
        self.is_dead = True
        self.hearts -= 1
        self.vy_int = JUMP_FORCE
        self.respawn_timer = 60
        self.animator.set_state("death", force=True)
        self.combo_hitstun = 0
        self.combo_version = 0
        self.combo_type = None
        self.combo_counter = 0
        self.combo_damage = 0.0
        self.combo_timer = 0
        self.last_combo_hit = None
        self.pending_combo_version = 0
        self.pending_combo_type = None
        self.counter_hit_timer = 0
        self.hit_pause_timer = 0
        self.hurt_buffer = 0
        self.ledge_grabbing = False
        self.ledge_hang_timer = 0
        self.ledge_invuln = 0
        self.ledge_action = None
        self.ledge_action_timer = 0

    def respawn(self, x, y):
        self.percentage = 0
        self.stale_queue.clear()
        self.rect.center = (x, y)
        self.pos.x = float(self.rect.x)
        self.pos.y = float(self.rect.y)
        self.vx_int = 0.0
        self.vy_int = 0.0
        self.vx_ext = 0.0
        self.vy_ext = 0.0
        self.hitstun = 0
        self.hitlag = 0
        self.flash_timer = 0
        self.attacking = 0
        self.hit_this_swing = False
        self.heavy_attack = False
        self.heavy_cooldown = 0
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.stomp_cooldown = 0
        self.combo_hitstun = 0
        self.combo_version = 0
        self.combo_type = None
        self.combo_counter = 0
        self.combo_damage = 0.0
        self.combo_timer = 0
        self.last_combo_hit = None
        self.pending_combo_version = 0
        self.pending_combo_type = None
        self.last_attack_type = None
        self.status_effects.clear()
        self.speed_mult = 1.0
        self.damage_mult = 1.0
        self.damage_taken_mult = 1.0
        self.kb_taken_mult = 1.0
        self.is_dead = False
        self.respawn_timer = 0
        self.special_active = 0
        self.special_name = None
        self.special_hit = False
        self.special_spawned = False
        self.special_cooldown = 0
        self.special_max_cooldown = 0
        self.hit_pause_timer = 0
        self.pending_kb_vx = 0.0
        self.pending_kb_vy = 0.0
        self.hurt_buffer = 0
        self.ledge_grabbing = False
        self.ledge_hang_timer = 0
        self.ledge_invuln = 0
        self.ledge_action = None
        self.ledge_action_timer = 0
        self.egg_rolling = False
        self.egg_roll_timer = 0
        self.respawn_invuln = 90
        self.egg_roll_hit_interval = 0
        self.grabbing = False
        self.grab_timer = 0
        self.grabbed_player = None
        stats = CHARACTER_STATS.get(self.char, CHARACTER_STATS["mario"])
        self.attack_damage    = stats["attack_damage"]
        self.attack_base_kb   = stats["attack_base_knockback"]
        self.attack_kb_growth = stats["attack_knockback_growth"]
        self.attack_frames    = stats["attack_frames"]
        self.attack_hit_start = stats["attack_hit_start"]
        self.attack_hit_end   = stats["attack_hit_end"]
        self.attack_kb_type   = "normal"
        self.on_ground = False
        self.coyote_time = 0
        self.jump_buffer = 0
        self.jumps_left = self.max_jumps
        self.jump_key_held = False
        self.jump_hold_frames = 0
        self.is_fast_falling = False
        self.just_double_jumped = False
        self.just_finished_aerial = 0
        self.gravity_skip = 0
        self.landing_lag = 0
        self.l_cancel_buffer = 0
        self.helpless = False
        self.p_meter = 0
        self.star_timer = 0
        self.attack_key_held = False
        self.special_key_held = False
        
        # Reset shield
        self.shield_health = MAX_SHIELD_HEALTH
        self.shielding = False
        self.shield_key_held = False
        self.shield_stun = 0
        self.shield_broken = False
        self.air_dodging = False
        self.air_dodge_timer = 0
        if self.rect.height != self.normal_hit_h:
            old_bottom = self.rect.bottom
            self.rect.height = self.normal_hit_h
            self.rect.bottom = old_bottom
            self.pos.y = float(self.rect.y)
        if self.rect.width != self.normal_hit_w:
            old_centerx = self.rect.centerx
            self.rect.width = self.normal_hit_w
            self.rect.centerx = old_centerx
            self.pos.x = float(self.rect.x)

        self.animator.set_state("idle", force=True)

    @staticmethod
    def resolve_overlap(a, b, tiles=None, skip_stomp=False):
        if not a.rect.colliderect(b.rect):
            return
        if a.is_dead or b.is_dead:
            return

        if not skip_stomp:
            tolerance = 6
            a_total_vy = a.vy_int + a.vy_ext
            b_total_vy = b.vy_int + b.vy_ext
            a_stomps = a_total_vy > 0 and a.rect.bottom < b.rect.centery + tolerance
            b_stomps = b_total_vy > 0 and b.rect.bottom < a.rect.centery + tolerance

            # Dash counter: stomper hits a dashing player → launched upward
            if a_stomps and b.dashing:
                a.take_damage(SLIDE_COUNTER_DAMAGE, SLIDE_COUNTER_KB_GROWTH, SLIDE_COUNTER_KB,
                              attacker_facing=b.facing, kb_bonus=1.0,
                              knockback_type="upward", attacker_percent=b.percentage)
                a.vy_int = SLIDE_COUNTER_BOUNCE
                a.jumps_left = a.max_jumps
                b.dashing = False
                b.dash_timer = 0
                return
            elif b_stomps and a.dashing:
                b.take_damage(SLIDE_COUNTER_DAMAGE, SLIDE_COUNTER_KB_GROWTH, SLIDE_COUNTER_KB,
                              attacker_facing=a.facing, kb_bonus=1.0,
                              knockback_type="upward", attacker_percent=a.percentage)
                b.vy_int = SLIDE_COUNTER_BOUNCE
                b.jumps_left = b.max_jumps
                a.dashing = False
                a.dash_timer = 0
                return

            if a_stomps and not b_stomps and b.stomp_cooldown <= 0:
                b.take_damage(STOMP_DAMAGE, STOMP_KNOCKBACK_GROWTH, STOMP_BASE_KNOCKBACK,
                              attacker_facing=a.facing)
                a.vy_int = -10
                a.jumps_left = a.max_jumps
                b.stomp_cooldown = STOMP_COOLDOWN
                return
            elif b_stomps and not a_stomps and a.stomp_cooldown <= 0:
                a.take_damage(STOMP_DAMAGE, STOMP_KNOCKBACK_GROWTH, STOMP_BASE_KNOCKBACK,
                              attacker_facing=b.facing)
                b.vy_int = -10
                b.jumps_left = b.max_jumps
                a.stomp_cooldown = STOMP_COOLDOWN
                return

        # Dash contact: dashing player bumps into standing opponent → minor upward damage
        # Yoshi's roll deals downward knockback
        if a.dashing and not b.dashing:
            if not b.hitlag and not a.hit_this_swing:
                slide_kb_type = a.roll_kb_type if a.roll_kb_type != "normal" else "upward"
                b.take_damage(SLIDE_DAMAGE_IDLE, SLIDE_KB_GROWTH_IDLE, SLIDE_BASE_KB_IDLE,
                              attacker_facing=a.facing, kb_bonus=0.8,
                              knockback_type=slide_kb_type, attacker_percent=a.percentage)
                a.hit_this_swing = True
        elif b.dashing and not a.dashing:
            if not a.hitlag and not b.hit_this_swing:
                slide_kb_type = b.roll_kb_type if b.roll_kb_type != "normal" else "upward"
                a.take_damage(SLIDE_DAMAGE_IDLE, SLIDE_KB_GROWTH_IDLE, SLIDE_BASE_KB_IDLE,
                              attacker_facing=b.facing, kb_bonus=0.8,
                              knockback_type=slide_kb_type, attacker_percent=b.percentage)
                b.hit_this_swing = True

        a_left_of_b = a.rect.centerx < b.rect.centerx
        overlap = (a.rect.right - b.rect.left) if a_left_of_b else (b.rect.right - a.rect.left)
        half = overlap // 2 + 1

        def would_hit_wall(player, dx):
            if tiles is None:
                return False
            test_rect = player.rect.move(dx, 0)
            for tile in tiles:
                rect = tile[0] if isinstance(tile, (list, tuple)) else tile
                if test_rect.colliderect(rect):
                    return True
            return False

        a_blocked = would_hit_wall(a, -half if a_left_of_b else half)
        b_blocked = would_hit_wall(b, half if a_left_of_b else -half)

        if a_blocked and b_blocked:
            a.vx_int = 0; a.vx_ext = 0
            b.vx_int = 0; b.vx_ext = 0
        elif a_blocked:
            if a_left_of_b:
                b.rect.x += overlap + 2
            else:
                b.rect.x -= overlap + 2
            b.pos.x = b.rect.x
            b.vx_int = 0; b.vx_ext = 0
            a.vx_int = 0; a.vx_ext = 0
        elif b_blocked:
            if a_left_of_b:
                a.rect.x -= overlap + 2
            else:
                a.rect.x += overlap + 2
            a.pos.x = a.rect.x
            b.vx_int = 0; b.vx_ext = 0
            a.vx_int = 0; a.vx_ext = 0
        else:
            if a_left_of_b:
                a.rect.x -= half
                b.rect.x += half
            else:
                a.rect.x += half
                b.rect.x -= half
            a.pos.x = a.rect.x
            b.pos.x = b.rect.x
            a.vx_int = 0; a.vx_ext = 0
            b.vx_int = 0; b.vx_ext = 0

    def draw(self, surface, camera_offset):
        if self.image:
            img = self.image
            draw_x = self.rect.centerx - img.get_width() // 2 - camera_offset[0] + self.image_offset[0]
            draw_y = self.rect.bottom - camera_offset[1] - img.get_height()

            # Idle breathing: subtle sine bob (centered on resting position)
            if self.animator.state == "idle" and self.on_ground and self.hitstun <= 0:
                bob = math.sin(self.idle_timer * 0.08) * 1
                draw_y += bob

            # Landing squash: compress vertically for a few frames
            if self.land_timer > 0:
                squash = 1.0 - (self.land_timer / 8.0) * 0.15
                w, h = img.get_size()
                img = pygame.transform.smoothscale(img, (int(w * 1.08), int(h * squash)))
                draw_y += h - img.get_height()

            # Run lean: slight horizontal tilt based on speed
            if abs(self.vx_int) > 1.0 and self.on_ground:
                lean = min(abs(self.vx_int) * 0.02, 0.06) * (1 if self.facing == 1 else -1)
                w, h = img.get_size()
                offset_x = int(lean * h)
                draw_x += offset_x

            if self.flash_timer > 0 and self.flash_timer % 2 == 0:
                flash = self.image.copy()
                flash.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (draw_x, draw_y))
            elif self.counter_hit_timer > 0 and self.counter_hit_timer % 2 == 0:
                flash = self.image.copy()
                flash.fill((255, 80, 80, 140), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (draw_x, draw_y))
            elif self.air_dodging:
                elapsed = AIR_DODGE_DURATION - self.air_dodge_timer
                if elapsed <= 6:
                    # Flash white during initial invincibility
                    flash = self.image.copy()
                    flash.fill((200, 200, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)
                    surface.blit(flash, (draw_x, draw_y))
                else:
                    surface.blit(self.image, (draw_x, draw_y))
            elif self.ledge_invuln > 0 and self.ledge_invuln % 3 == 0:
                flash = self.image.copy()
                flash.fill((100, 255, 100, 100), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (draw_x, draw_y))
            elif self.star_timer > 0 and self.star_timer % 4 >= 2:
                pass
            elif self.respawn_invuln > 0 and self.respawn_invuln % 6 < 3:
                surface.blit(self.image, (draw_x, draw_y))
            else:
                surface.blit(self.image, (draw_x, draw_y))
        
        # Draw shield bubble
        if self.shielding and self.shield_health > 0:
            shield_center_x = self.rect.centerx - camera_offset[0]
            shield_center_y = self.rect.centery - camera_offset[1]
            
            # Shield size scales with health (smaller when low)
            health_ratio = self.shield_health / MAX_SHIELD_HEALTH
            shield_radius = int(SHIELD_VISUAL_RADIUS * (0.5 + 0.5 * health_ratio))
            
            # Create shield surface with alpha
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, SHIELD_VISUAL_COLOR, (shield_radius, shield_radius), shield_radius)
            
            # Draw shield
            surface.blit(shield_surf, (shield_center_x - shield_radius, shield_center_y - shield_radius))

        # Draw status effect indicators
        if self.status_effects:
            indicator_x = self.rect.centerx - camera_offset[0]
            indicator_y = self.rect.top - camera_offset[1] - 10
            for i, eff in enumerate(self.status_effects):
                etype = eff["type"]
                if etype == "slow":
                    color = (100, 100, 255)
                elif etype == "fire_dot":
                    color = (255, 120, 20)
                elif etype == "kb_amp":
                    color = (255, 50, 50)
                elif etype == "damage_amp":
                    color = (255, 200, 0)
                elif etype == "hitstun_amp":
                    color = (200, 100, 255)
                else:
                    color = (200, 200, 200)
                pygame.draw.circle(surface, color, (indicator_x + i * 12, indicator_y), 4)
