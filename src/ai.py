import pygame
import math
import random


DIFFICULTY_CONFIGS = {
    "easy": {
        "reaction_delay": 25,
        "approach_chance": 0.20,
        "attack_chance": 0.15,
        "shield_chance": 0.0,
        "jump_chance": 0.05,
        "aerial_chance": 0.0,
        "combo_max_version": 0,
        "heavy_chance": 0.02,
        "special_chance": 0.01,
        "chase_accuracy": 0.15,
        "retreat_threshold": 999,
        "di_strength": 0.0,
        "platform_usage": 0.0,
        "edge_guard": False,
        "dash_dance_chance": 0.0,
        "fast_fall_chance": 0.0,
        "l_cancel_chance": 0.0,
        "offense_bias": 0.2,
        "whiff_punish": 0.0,
        "cross_up_chance": 0.0,
        "ledge_guard_chance": 0.0,
        "fast_fall_ground_return": 0.9,
        "whiff_commit": 0.15,
    },
    "normal": {
        "reaction_delay": 16,
        "approach_chance": 0.35,
        "attack_chance": 0.25,
        "shield_chance": 0.08,
        "jump_chance": 0.10,
        "aerial_chance": 0.05,
        "combo_max_version": 1,
        "heavy_chance": 0.05,
        "special_chance": 0.03,
        "chase_accuracy": 0.25,
        "retreat_threshold": 100,
        "di_strength": 0.15,
        "platform_usage": 0.08,
        "edge_guard": False,
        "dash_dance_chance": 0.03,
        "fast_fall_chance": 0.05,
        "l_cancel_chance": 0.0,
        "offense_bias": 0.35,
        "whiff_punish": 0.08,
        "cross_up_chance": 0.0,
        "ledge_guard_chance": 0.0,
        "fast_fall_ground_return": 0.85,
        "whiff_commit": 0.3,
    },
    "hard": {
        "reaction_delay": 9,
        "approach_chance": 0.50,
        "attack_chance": 0.40,
        "shield_chance": 0.18,
        "jump_chance": 0.18,
        "aerial_chance": 0.15,
        "combo_max_version": 2,
        "heavy_chance": 0.12,
        "special_chance": 0.06,
        "chase_accuracy": 0.50,
        "retreat_threshold": 60,
        "di_strength": 0.35,
        "platform_usage": 0.20,
        "edge_guard": True,
        "dash_dance_chance": 0.08,
        "fast_fall_chance": 0.15,
        "l_cancel_chance": 0.25,
        "offense_bias": 0.55,
        "whiff_punish": 0.18,
        "cross_up_chance": 0.10,
        "ledge_guard_chance": 0.15,
        "fast_fall_ground_return": 0.70,
        "whiff_commit": 0.45,
    },
    "pro": {
        "reaction_delay": 5,
        "approach_chance": 0.65,
        "attack_chance": 0.55,
        "shield_chance": 0.30,
        "jump_chance": 0.25,
        "aerial_chance": 0.30,
        "combo_max_version": 3,
        "heavy_chance": 0.20,
        "special_chance": 0.10,
        "chase_accuracy": 0.65,
        "retreat_threshold": 40,
        "di_strength": 0.6,
        "platform_usage": 0.40,
        "edge_guard": True,
        "dash_dance_chance": 0.18,
        "fast_fall_chance": 0.30,
        "l_cancel_chance": 0.50,
        "offense_bias": 0.70,
        "whiff_punish": 0.35,
        "cross_up_chance": 0.20,
        "ledge_guard_chance": 0.30,
        "fast_fall_ground_return": 0.55,
        "whiff_commit": 0.55,
    },
    "insane": {
        "reaction_delay": 2,
        "approach_chance": 0.80,
        "attack_chance": 0.70,
        "shield_chance": 0.45,
        "jump_chance": 0.35,
        "aerial_chance": 0.50,
        "combo_max_version": 3,
        "heavy_chance": 0.30,
        "special_chance": 0.15,
        "chase_accuracy": 0.85,
        "retreat_threshold": 25,
        "di_strength": 1.0,
        "platform_usage": 0.65,
        "edge_guard": True,
        "dash_dance_chance": 0.35,
        "fast_fall_chance": 0.50,
        "l_cancel_chance": 0.85,
        "offense_bias": 0.85,
        "whiff_punish": 0.55,
        "cross_up_chance": 0.30,
        "ledge_guard_chance": 0.45,
        "fast_fall_ground_return": 0.40,
        "whiff_commit": 0.70,
    },
}


class AIController:
    def __init__(self, player, opponent, difficulty="normal", controls=None):
        self.player = player
        self.opponent = opponent
        self.controls = controls
        self.difficulty = difficulty
        self.cfg = DIFFICULTY_CONFIGS.get(difficulty, DIFFICULTY_CONFIGS["normal"])

        self.decision_timer = 0
        self.current_intent = "idle"
        self.intent_timer = 0
        self._rng = random.Random()

        self._prev_opp_x = 0
        self._prev_opp_vy = 0
        self._prev_opp_on_ground = True
        self.held = {}

        self.airborne_frames = 0
        self.opp_airborne_frames = 0
        self._recent_aerial_attack = 0
        self._recovery_dir = 1
        self._edge_guard_toward = True

        self.level_w = None
        self.blast_margin = 350
        self.solid = []
        self._obstacle_jump_timer = 0

    def set_stage(self, level_w, blast_margin=350, solid=None):
        self.level_w = level_w
        self.blast_margin = blast_margin
        self.solid = solid or []

    def _obstacle_ahead(self, look_ahead=80):
        """Check if there's a solid tile (pipe/wall) blocking the AI's path ahead."""
        p = self.player
        if not self.solid or not p.on_ground:
            return False
        check_x = p.rect.centerx + (1 if p.facing == 1 else -1) * look_ahead
        check_rect = pygame.Rect(check_x - 8, p.rect.bottom - 40, 16, 40)
        for r in self.solid:
            if check_rect.colliderect(r):
                return True
        return False

    def update(self, real_keys, frame, stage_bounds=None):
        self.decision_timer -= 1
        self.intent_timer -= 1
        if self._recent_aerial_attack > 0:
            self._recent_aerial_attack -= 1

        if stage_bounds is not None:
            self.level_w, self.blast_margin = stage_bounds

        p = self.player
        o = self.opponent

        # AI ledge actions: randomly choose after a brief delay
        if p.ledge_grabbing and p.ledge_action is None:
            if self.intent_timer <= 0:
                actions = ["jump", "getup", "drop", "attack"]
                choice = self._rng.choice(actions)
                self.current_intent = f"ledge_{choice}"
                self.intent_timer = self._rng.randint(10, 30)
            self._apply_ledge_intent()
            return

        if p.on_ground:
            self.airborne_frames = 0
        else:
            self.airborne_frames += 1

        if o.on_ground:
            self.opp_airborne_frames = 0
        else:
            self.opp_airborne_frames += 1

        dx = o.rect.centerx - p.rect.centerx
        dy = o.rect.centery - p.rect.centery
        dist = abs(dx)
        facing_opp = (dx > 0 and p.facing == 1) or (dx < 0 and p.facing == -1)

        opp_was_on_ground = self._prev_opp_on_ground
        opp_just_left_ground = opp_was_on_ground and not o.on_ground
        opp_just_landed = not opp_was_on_ground and o.on_ground

        if self._needs_recovery():
            self._decide_recover(dx)
        elif self.intent_timer <= 0 or self.decision_timer <= 0:
            self._decide(dx, dy, dist, facing_opp, frame, opp_just_left_ground, opp_just_landed)
            jitter = self._rng.randint(0, max(1, self.cfg["reaction_delay"] // 3))
            self.decision_timer = self.cfg["reaction_delay"] + jitter

        self._apply_intent(dx, dy, dist, facing_opp)

        self._prev_opp_x = o.rect.centerx
        self._prev_opp_vy = o.vy_int + o.vy_ext
        self._prev_opp_on_ground = o.on_ground

    def _needs_recovery(self):
        p = self.player
        if p.on_ground or p.is_dead or p.hitstun > 0 or p.hitlag > 0:
            return False
        if p.ledge_grabbing:
            return False
        falling = (p.vy_int + p.vy_ext) > 1.0
        out_of_jumps = p.jumps_left <= 0
        stranded = self.airborne_frames > 70
        off_stage = False
        if self.level_w is not None:
            off_stage = (p.rect.centerx < -self.blast_margin * 0.3
                         or p.rect.centerx > self.level_w + self.blast_margin * 0.3)
        return falling and (out_of_jumps or stranded or off_stage)

    def _apply_ledge_intent(self):
        """Set held keys for ledge actions."""
        self.held = {
            "left": False, "right": False, "jump": False,
            "attack": False, "attack_alt": False, "special": False,
            "shield": False, "crouch": False,
        }
        intent = self.current_intent
        if intent == "ledge_jump":
            self.held["special"] = True
        elif intent == "ledge_getup":
            self.held["jump"] = True
        elif intent == "ledge_drop":
            self.held["crouch"] = True
        elif intent == "ledge_attack":
            self.held["attack"] = True

    def _decide_recover(self, dx):
        p = self.player
        if self.level_w is not None:
            target_x = self.level_w / 2
            toward_target = target_x - p.rect.centerx
        else:
            toward_target = dx
        self._recovery_dir = 1 if toward_target >= 0 else -1
        self.current_intent = "recover"
        self.intent_timer = 6

    def _opponent_recovering(self):
        o = self.opponent
        if o.on_ground:
            return False
        falling = (o.vy_int + o.vy_ext) > 0.5
        stranded = o.jumps_left <= 0 or self.opp_airborne_frames > 40
        return falling and stranded

    def _decide_edge_guard(self, dx):
        cfg = self.cfg
        self._edge_guard_toward = dx > 0
        if self._rng.random() < cfg["ledge_guard_chance"]:
            self.current_intent = "edge_guard_dive"
        else:
            self.current_intent = "edge_guard_hold"
        self.intent_timer = 8

    def _decide(self, dx, dy, dist, facing_opp, frame, opp_just_left_ground, opp_just_landed):
        p = self.player
        o = self.opponent
        cfg = self.cfg

        if p.is_dead or p.hitstun > 0 or p.hitlag > 0:
            self.current_intent = "idle"
            self.intent_timer = 5
            return

        if p.attacking > 0:
            self.current_intent = "idle"
            self.intent_timer = 2
            return

        if p.landing_lag > 0:
            self.current_intent = "idle"
            self.intent_timer = p.landing_lag
            return

        if p.combo_version > 0 and p.combo_hitstun > 0:
            if dist < 70 and self._rng.random() < cfg["attack_chance"] * 1.5:
                self.current_intent = "attack"
                self.intent_timer = 4
                return

        if p.on_ground and self._obstacle_ahead(80):
            self.current_intent = "jump_toward"
            self.intent_timer = 8
            return

        if not p.on_ground:
            above_opponent = p.rect.centery < o.rect.centery - 30
            close_enough = dist < 100
            if above_opponent and self._rng.random() < cfg["fast_fall_ground_return"]:
                self.current_intent = "fast_fall"
                self.intent_timer = 4
                return
            if close_enough and self._rng.random() < cfg["aerial_chance"]:
                self._decide_airborne_attack(dx, dy, dist, facing_opp)
                return
            if close_enough and self._rng.random() < cfg["fast_fall_chance"]:
                self.current_intent = "fast_fall"
                self.intent_timer = 3
                return
            # Drift toward opponent while airborne (uses the "aerial_approach" intent)
            if self._rng.random() < cfg["approach_chance"] * 0.6:
                self.current_intent = "aerial_approach"
                self.intent_timer = 6
                return
            self.current_intent = "fast_fall"
            self.intent_timer = 4
            return

        if cfg["edge_guard"] and self._opponent_recovering() and dist < 260:
            self._decide_edge_guard(dx)
            return

        if opp_just_landed and dist < 90 and self._rng.random() < cfg["whiff_punish"]:
            self.current_intent = "attack"
            self.intent_timer = 3
            return

        if o.attacking > 0 and dist < 100:
            if self._rng.random() < cfg["shield_chance"]:
                self.current_intent = "shield"
                self.intent_timer = 12
                return
            if self._rng.random() < cfg["di_strength"]:
                self.current_intent = "di_brace"
                self.intent_timer = 3
                return

        if dist < 55:
            self._decide_close_combat(dx, dy, dist, facing_opp)
        elif dist < 150:
            self._decide_mid_range(dx, dy, dist, facing_opp)
        else:
            self._decide_approach(dx, dy, dist, facing_opp)

    def _decide_airborne_attack(self, dx, dy, dist, facing_opp):
        if not facing_opp:
            self.current_intent = "turn_and_aerial"
        else:
            self.current_intent = "aerial_attack"
        self.intent_timer = 4
        self._recent_aerial_attack = 8

    def _decide_close_combat(self, dx, dy, dist, facing_opp):
        cfg = self.cfg
        p = self.player
        o = self.opponent
        r = self._rng.random()

        if not facing_opp:
            if r < cfg["chase_accuracy"]:
                self.current_intent = "turn_and_attack"
            else:
                self.current_intent = "attack"
            self.intent_timer = 4
            return

        opp_vx = getattr(o, "vx_int", 0.0) + getattr(o, "vx_ext", 0.0)
        opp_retreating = (dx > 0 and opp_vx > 0.5) or (dx < 0 and opp_vx < -0.5)

        attack_roll = cfg["attack_chance"]
        if opp_retreating and self._rng.random() > cfg["whiff_commit"]:
            attack_roll *= 0.3

        cross_up_roll = cfg["cross_up_chance"]
        jump_roll = cfg["jump_chance"] * cfg["offense_bias"]

        if r < attack_roll:
            if cfg["combo_max_version"] > 0 and p.combo_version > 0:
                self.current_intent = "attack"
            elif self._rng.random() < cfg["heavy_chance"] and p.heavy_cooldown <= 0:
                self.current_intent = "heavy"
            else:
                self.current_intent = "attack"
            self.intent_timer = 3
        elif r < attack_roll + cross_up_roll:
            self.current_intent = "cross_up"
            self.intent_timer = 6
        elif r < attack_roll + cross_up_roll + jump_roll:
            self.current_intent = "jump_toward"
            self.intent_timer = 5
        else:
            if self._rng.random() < cfg["dash_dance_chance"]:
                self.current_intent = "dash_dance"
            else:
                self.current_intent = "idle"
            self.intent_timer = 6

    def _decide_mid_range(self, dx, dy, dist, facing_opp):
        cfg = self.cfg
        r = self._rng.random()
        p = self.player

        if r < cfg["approach_chance"]:
            if self._rng.random() < cfg["jump_chance"] and p.on_ground:
                self.current_intent = "jump_toward"
            else:
                self.current_intent = "approach"
            self.intent_timer = 8
        elif r < cfg["approach_chance"] + cfg["shield_chance"] * 0.5:
            self.current_intent = "shield"
            self.intent_timer = 10
        elif p.on_ground and self._rng.random() < cfg["platform_usage"]:
            self.current_intent = "platform_hop"
            self.intent_timer = 10
        elif self._rng.random() < cfg["special_chance"]:
            self.current_intent = "special"
            self.intent_timer = 5
        else:
            self.current_intent = "approach"
            self.intent_timer = 6

    def _decide_approach(self, dx, dy, dist, facing_opp):
        cfg = self.cfg
        r = self._rng.random()

        if self.player.percentage > cfg["retreat_threshold"] and self._rng.random() < 0.3:
            self.current_intent = "retreat"
            self.intent_timer = 10
        elif self.player.on_ground and self._rng.random() < cfg["platform_usage"] * 0.5:
            self.current_intent = "platform_hop"
            self.intent_timer = 10
        elif r < cfg["approach_chance"]:
            if self._rng.random() < cfg["jump_chance"] and self.player.on_ground:
                self.current_intent = "jump_toward"
                self.intent_timer = 6
            else:
                self.current_intent = "approach"
                self.intent_timer = 10
        else:
            self.current_intent = "approach"
            self.intent_timer = 8

    def _apply_intent(self, dx, dy, dist, facing_opp):
        intent = self.current_intent

        self.held = {
            "left": False, "right": False, "jump": False,
            "attack": False, "attack_alt": False, "special": False,
            "shield": False, "crouch": False,
        }

        move_toward = dx > 0
        move_away = dx < 0

        if intent == "approach":
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "retreat":
            if move_away:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "attack":
            self.held["attack"] = True
            if not facing_opp:
                if move_toward:
                    self.held["right"] = True
                else:
                    self.held["left"] = True

        elif intent == "heavy":
            self.held["attack_alt"] = True
            if not facing_opp:
                if move_toward:
                    self.held["right"] = True
                else:
                    self.held["left"] = True

        elif intent == "turn_and_attack":
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True
            self.held["attack"] = True

        elif intent == "cross_up":
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True
            self.held["jump"] = True

        elif intent == "jump_toward":
            self.held["jump"] = True
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "aerial":
            self.held["jump"] = True
            if self._rng.random() < self.cfg["fast_fall_chance"]:
                self.held["crouch"] = True
            if self._rng.random() < self.cfg["aerial_chance"]:
                self.held["attack"] = True

        elif intent == "aerial_approach":
            self.held["jump"] = True
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True
            if self._rng.random() < self.cfg["fast_fall_chance"]:
                self.held["crouch"] = True
            if self._rng.random() < self.cfg["aerial_chance"]:
                self.held["attack"] = True

        elif intent == "aerial_attack":
            self.held["attack"] = True
            if self._rng.random() < 0.5:
                self.held["crouch"] = True

        elif intent == "turn_and_aerial":
            if move_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True
            self.held["attack"] = True

        elif intent == "fast_fall":
            self.held["crouch"] = True

        elif intent == "shield":
            self.held["shield"] = True

        elif intent == "di_brace":
            if move_away:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "platform_hop":
            self.held["jump"] = True

        elif intent == "recover":
            if self.player.jumps_left > 0:
                self.held["jump"] = True
            if self._recovery_dir > 0:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "edge_guard_dive":
            self.held["jump"] = True
            if self._edge_guard_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "edge_guard_hold":
            if self._edge_guard_toward:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "special":
            self.held["special"] = True

        elif intent == "dash_dance":
            if self.intent_timer % 4 < 2:
                self.held["right"] = True
            else:
                self.held["left"] = True

        elif intent == "idle":
            pass
