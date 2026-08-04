import pygame

MARIO_ANIMATIONS = {
    "idle":     (["Mario - Idle"],                                    6,  False),
    "start_idle": (["Mario - Idle 1", "Mario - Idle 2"],              4,  True),
    "run":      (["Mario - Run 1", "Mario - Run 2", "Mario - Run 3",
                  "Mario - Run 4", "Mario - Run 5", "Mario - Run 6",
                  "Mario - Run 7", "Mario - Run 8"],                 12, True),
    "dash":     (["Mario - Dash 1", "Mario - Dash 2", "Mario - Dash 3",
                  "Mario - Dash 4", "Mario - Dash 5", "Mario - Dash 6",
                  "Mario - Dash 7"],                                  10, False),
    "jump":     (["Mario - Jump 1", "Mario - Jump 2",
                  "Mario - Jump 3", "Mario - Jump 4"],               10,  False),
    "double_jump": (["Mario - Jump 1", "Mario - Jump 2",
                     "Mario - Jump 3", "Mario - Jump 4"],            10,  False),
    "fall":     (["Mario - Fall"],                                    6,  True),
    "land":     (["Mario - Land 1", "Mario - Land 2"],               10, False),
    "hurt":     (["Mario - Hurt"],                                    6,  True),
    "death":    (["Mario - Hurt"],                                    6,  False),

    # === BLOCK ===
    "block":    (["Mario - Block"],                                   6,  False),
    "air_block": (["Mario - Block"],                                  6,  False),
    "taunt":    (["Mario - Idle 1", "Mario - Idle 2",
                  "Mario - Idle 3", "Mario - Idle 4"],               4,  True),

    # === HAMMER SPECIAL ===
    "hammer_smash": (
        ["Mario - Hammer 1", "Mario - Hammer 2",
         "Mario - Hammer 3", "Mario - Hammer 4"],
        8, False
    ),

    # === FIRE PUNCH SPECIAL ===
    "fire_punch": (
        ["Mario - Fire 1", "Mario - Fire 2",
         "Mario - Fire 3", "Mario - Fire 4"],
        8, False
    ),

    # === AIR ATTACKS ===
    "air_light": (
        ["Mario - Air Light 1", "Mario - Air Light 2", "Mario - Air Light 3"],
        10, False
    ),
    "air_heavy": (
        ["Mario - Air Heavy 1", "Mario - Air Heavy 2",
         "Mario - Air Heavy 3", "Mario - Air Heavy 4"],
        8, False
    ),

    # === LIGHT ATTACK COMBO (3 versions) ===
    # fps = num_anim_frames / (attack_frames / 60)
    # v1: 3/(12/60)=15, v2: 3/(14/60)=13, v3: 3/(14/60)=13
    "light_v1": (["Mario - Light V1 1", "Mario - Light V1 2",
                  "Mario - Light V1 3"],                             15,  False),
    "light_v2": (["Mario - Light V2 1", "Mario - Light V2 2",
                  "Mario - Light V2 3"],                             13,  False),
    "light_v3": (["Mario - Light V3 1", "Mario - Light V3 2",
                  "Mario - Light V3 3"],                             13,  False),

    # === HEAVY ATTACK COMBO (3 versions) ===
    # v1: 4/(28/60)=9, v2: 4/(28/60)=9, v3: 4/(28/60)=9
    "heavy_v1": (["Mario - Heavy V1 1", "Mario - Heavy V1 2",
                  "Mario - Heavy V1 3", "Mario - Heavy V1 4"],       9,  False),
    "heavy_v2": (["Mario - Heavy V2 1", "Mario - Heavy V2 2",
                  "Mario - Heavy V2 3", "Mario - Heavy V2 4"],       9,  False),
    "heavy_v3": (["Mario - Heavy V3 1", "Mario - Heavy V3 2",
                  "Mario - Heavy V3 3", "Mario - Heavy V3 4"],       9,  False),
    "ledge_grab": (["Mario - Ledge Grab 1", "Mario - Ledge Grab 2",
                    "Mario - Ledge Grab 3"],                          6,  True),
}

LUIGI_ANIMATIONS = {
    "idle":     (["Luigi - Idle"],                                    6,  False),
    "start_idle": (["Luigi - Idle 1", "Luigi - Idle 2",
                   "Luigi - Idle 3", "Luigi - Idle 4"],              4,  True),
    "run":      (["Luigi - Run 1", "Luigi - Run 2", "Luigi - Run 3",
                  "Luigi - Run 4", "Luigi - Run 5", "Luigi - Run 6",
                  "Luigi - Run 7", "Luigi - Run 8"],                 12, True),
    "dash":     (["Luigi - Dash 1", "Luigi - Dash 2", "Luigi - Dash 3",
                  "Luigi - Dash 4", "Luigi - Dash 5", "Luigi - Dash 6"], 10, False),
    "jump":     (["Luigi - Jump 1", "Luigi - Jump 2",
                  "Luigi - Jump 3", "Luigi - Jump 4"],               10, False),
    "fall":     (["Luigi - Fall"],                                    6,  True),
    "land":     (["Luigi - Land"],                                    10, False),
    "double_jump": (["Luigi - Double Jump 1", "Luigi - Double Jump 2",
                    "Luigi - Double Jump 3", "Luigi - Double Jump 4",
                    "Luigi - Double Jump 5"],                        10, False),

    # === LIGHT ATTACK COMBO (3 versions) ===
    "light_v1": (["Luigi - Light V1 1", "Luigi - Light V1 2",
                  "Luigi - Light V1 3"],                             15,  False),
    "light_v2": (["Luigi - Light V2 1", "Luigi - Light V2 2",
                  "Luigi - Light V2 3"],                             13,  False),
    "light_v3": (["Luigi - Light V3 1", "Luigi - Light V3 2",
                  "Luigi - Light V3 3", "Luigi - Light V3 4"],       13,  False),

    # === HEAVY ATTACK COMBO (3 versions) ===
    "heavy_v1": (["Luigi - Heavy V1 1", "Luigi - Heavy V1 2",
                  "Luigi - Heavy V1 3", "Luigi - Heavy V1 4"],       9,   False),
    "heavy_v2": (["Luigi - Heavy V2 1", "Luigi - Heavy V2 2",
                  "Luigi - Heavy V2 3", "Luigi - Heavy V2 4"],       9,   False),
    "heavy_v3": (["Luigi - Heavy V3 1", "Luigi - Heavy V3 2",
                  "Luigi - Heavy V3 3", "Luigi - Heavy V3 4"],       9,   False),

    # === AIR ATTACKS ===
    "air_light": (["Luigi - Air Light 1", "Luigi - Air Light 2"],    6,  False),
    "air_heavy": (["Luigi - Air Heavy 1", "Luigi - Air Heavy 2",
                   "Luigi - Air Heavy 3", "Luigi - Air Heavy 4"],    6,  False),

    # === BLOCK ===
    "block":    (["Luigi - Block 1", "Luigi - Block 2"],             6,  False),
    "air_block": (["Luigi - Air Block 1", "Luigi - Air Block 2"],    6,  False),

    # === HURT / DEATH ===
    "hurt":     (["Luigi - Hurt"],                                    6,  True),
    "death":    (["Luigi - Hurt"],                                    6,  False),

    # === SPECIALS ===
    "head_drill": (["Luigi - Head Drill 1", "Luigi - Head Drill 2",
                    "Luigi - Head Drill 3", "Luigi - Head Drill 4",
                    "Luigi - Head Drill 5"],                         10,  True, 2),
    "air_shot_air": (["Luigi - Air Shot Air 1", "Luigi - Air Shot Air 2",
                      "Luigi - Air Shot Air 3", "Luigi - Air Shot Air 4",
                      "Luigi - Air Shot Air 5"],                     10,  False),
    "air_shot_land": (["Luigi - Air Shot Land 1", "Luigi - Air Shot Land 2",
                       "Luigi - Air Shot Land 3", "Luigi - Air Shot Land 4",
                       "Luigi - Air Shot Land 5"],                   10,  False),

    # === TAUNT ===
    "taunt":    (["Luigi - Taunt 1", "Luigi - Taunt 2", "Luigi - Taunt 3",
                  "Luigi - Taunt 4", "Luigi - Taunt 5", "Luigi - Taunt 6",
                  "Luigi - Taunt 7"],                                 8,   False),
    "ledge_grab": (["Luigi - Ledge Grab 1", "Luigi - Ledge Grab 2",
                    "Luigi - Ledge Grab 3"],                          6,  True),
}

YOSHI_ANIMATIONS = {
    # === BASE ===
    "idle":     (["Yoshi - Idle 3"],                                   6,  False),
    "block":    (["Yoshi - Air Block 1", "Yoshi - Air Block 2"],      6,  False),
    "taunt":    (["Yoshi - Idle 1", "Yoshi - Idle 2", "Yoshi - Idle 3",
                  "Yoshi - Idle 4", "Yoshi - Idle 5"],               6,  True),
    "start_idle": (["Yoshi - Idle 1", "Yoshi - Idle 2"],               4,  True),
    "run":      (["Yoshi - Run 1", "Yoshi - Run 2", "Yoshi - Run 3", "Yoshi - Run 4",
                  "Yoshi - Run 5", "Yoshi - Run 6", "Yoshi - Run 7", "Yoshi - Run 8"],
                                                                          12, True),
    "dash":     (["Yoshi - Dash 1", "Yoshi - Dash 2"],                   10, False),
    "jump":     (["Yoshi - Jump 1", "Yoshi - Jump 2"],                   8,  False),
    "double_jump": (["Yoshi - Double Jump 1", "Yoshi - Double Jump 2",
                     "Yoshi - Double Jump 3", "Yoshi - Double Jump 4",
                     "Yoshi - Double Jump 5"],                           10, False),
    "fall":     (["Yoshi - Fall 1", "Yoshi - Fall 2"],                   8,  True),
    "land":     (["Yoshi - Land 1", "Yoshi - Land 2"],                   12, False),
    "roll":     (["Yoshi - Roll 1", "Yoshi - Roll 2", "Yoshi - Roll 3",
                  "Yoshi - Roll 4", "Yoshi - Roll 5", "Yoshi - Roll 6",
                  "Yoshi - Roll 7", "Yoshi - Roll 8", "Yoshi - Roll 9"], 12, False),
    "hurt":     (["Yoshi - Hurt 1", "Yoshi - Hurt 2"],                   8,  True),
    "death":    (["Yoshi - Hurt 1", "Yoshi - Hurt 2"],                   6,  False),
    "air_block": (["Yoshi - Air Block 1", "Yoshi - Air Block 2"], 8, False),

    # === LIGHT ATTACK COMBO (3 versions) ===
    # fps = num_anim_frames / (attack_frames / 60)
    # v1: 4/(12/60)=20, v2: 4/(14/60)=17, v3: 4/(14/60)=17
    "light_v1": (["Yoshi - Light V1 1", "Yoshi - Light V1 2",
                  "Yoshi - Light V1 3", "Yoshi - Light V1 4"],           20,  False),
    "light_v2": (["Yoshi - Light V2 1", "Yoshi - Light V2 2",
                  "Yoshi - Light V2 3", "Yoshi - Light V2 4"],           17,  False),
    "light_v3": (["Yoshi - Light V3 1", "Yoshi - Light V3 2",
                  "Yoshi - Light V3 3", "Yoshi - Light V3 4"],           17,  False),
    "combo_reset": (["Yoshi - Combo Reset"],                             6,  False),

    # === HEAVY ATTACK COMBO (3 versions) ===
    # v1: 5/(28/60)=11, v2: 5/(28/60)=11, v3: 6/(28/60)=13
    "heavy_v1": (["Yoshi - Heavy V1 1", "Yoshi - Heavy V1 2",
                  "Yoshi - Heavy V1 3", "Yoshi - Heavy V1 4",
                  "Yoshi - Heavy V1 5"],                                 11,  False),
    "heavy_v2": (["Yoshi - Heavy V2 1", "Yoshi - Heavy V2 2",
                  "Yoshi - Heavy V2 3", "Yoshi - Heavy V2 4",
                  "Yoshi - Heavy V2 5"],                                 11,  False),
    "heavy_v3": (["Yoshi - Heavy V3 1", "Yoshi - Heavy V3 2",
                  "Yoshi - Heavy V3 3", "Yoshi - Heavy V3 4",
                  "Yoshi - Heavy V3 5", "Yoshi - Heavy V3 6"],           13,  False),

    # === AIR ATTACKS ===
    "air_light": (["Yoshi - Air Light 1", "Yoshi - Air Light 2"],        6,  False),
    "air_heavy": (["Yoshi - Air Heavy 1", "Yoshi - Air Heavy 2"],        6,  False),

    # === EGG ROLL (Special E) ===
    "egg_roll": (["Yoshi - Egg Roll 1", "Yoshi - Egg Roll 2",
                  "Yoshi - Egg Roll 3", "Yoshi - Egg Roll 4",
                  "Yoshi - Egg Roll 5", "Yoshi - Egg Roll 6",
                  "Yoshi - Egg Roll 7", "Yoshi - Egg Roll 8"],           12, True),

    # === EGG THROW (Special Q - ground) ===
    "egg_throw_ground": (["Yoshi - Egg Throw G1", "Yoshi - Egg Throw G2",
                          "Yoshi - Egg Throw G3", "Yoshi - Egg Throw G4",
                          "Yoshi - Egg Throw G5", "Yoshi - Egg Throw G6",
                          "Yoshi - Egg Throw G7"],                       14, False),

    # === EGG THROW (Special Q - air) ===
    "egg_throw_air": (["Yoshi - Egg Throw A1", "Yoshi - Egg Throw A2",
                       "Yoshi - Egg Throw A3", "Yoshi - Egg Throw A4",
                       "Yoshi - Egg Throw A5", "Yoshi - Egg Throw A6"],  14, False),

    # === EGG LAY (eat NPC → egg) ===
    "egg_lay":  (["Yoshi - Egg Lay 1", "Yoshi - Egg Lay 2", "Yoshi - Egg Lay 3",
                  "Yoshi - Egg Lay 4", "Yoshi - Egg Lay 5", "Yoshi - Egg Lay 6",
                  "Yoshi - Egg Lay 7", "Yoshi - Egg Lay 8", "Yoshi - Egg Lay 9"],
                                                                          10, False),

    # === PLAYER THROW (grab + hurl behind) ===
    "throw":    (["Yoshi - Throw 1", "Yoshi - Throw 2", "Yoshi - Throw 3"],
                                                                          12, False),
    "throw_air": (["Yoshi - Throw Air 1", "Yoshi - Throw Air 2", "Yoshi - Throw Air 3"],
                                                                           12, False),
    "ledge_grab": (["Yoshi - Ledge Grab 1", "Yoshi - Ledge Grab 2"],
                                                                           6,  True),
}

DONKEY_KONG_ANIMATIONS = {
    "idle":     (["DK - Idle"],                                          6,  False),
    "start_idle": (["DK - Idle"],                                        6,  False),
    "run":      (["DK - Run 1", "DK - Run 2", "DK - Run 3",
                  "DK - Run 4", "DK - Run 5"],                          10, True),
    "roll":     (["DK - Roll 1", "DK - Roll 2", "DK - Roll 3",
                  "DK - Roll 4", "DK - Roll 5", "DK - Roll 6",
                  "DK - Roll 7"],                                        8, False),
    "jump":     (["DK - Jump 1", "DK - Jump 2", "DK - Jump 3"],         10, False),
    "double_jump": (["DK - Jump 1", "DK - Jump 2", "DK - Jump 3"],      10, False),
    "fall":     (["DK - Fall"],                                          6,  False),
    "land":     (["DK - Idle"],                                          6,  False),
    "hurt":     (["DK - Hurt Heavy 1", "DK - Hurt Heavy 2"],            8,  True),
    "death":    (["DK - Hurt Heavy 1", "DK - Hurt Heavy 2"],            6,  False),

    # === BLOCK ===
    "block":    (["DK - Block"],                                         6,  False),
    "air_block": (["DK - Block"],                                        6,  False),
    "taunt":    (["DK - Taunt 1", "DK - Taunt 2", "DK - Taunt 3",
                  "DK - Taunt 4", "DK - Taunt 5", "DK - Taunt 6",
                  "DK - Taunt 7"],                                       6,  True),

    # === BARREL THROW SPECIAL (Q) ===
    "barrel_throw": (
        ["DK - Barrel Throw 1", "DK - Barrel Throw 2", "DK - Barrel Throw 3",
         "DK - Barrel Throw 4", "DK - Barrel Throw 5", "DK - Barrel Throw 6",
         "DK - Barrel Throw 7"],
        8, False
    ),

    # === SPECIAL SMASH (E) ===
    "barrel_smash": (
        ["DK - Special Smash 1", "DK - Special Smash 2", "DK - Special Smash 3",
         "DK - Special Smash 4", "DK - Special Smash 5"],
        8, False
    ),

    # === AIR ATTACKS ===
    "air_light": (
        ["DK - Light V1 1", "DK - Light V1 2", "DK - Light V1 3"],
        18, False
    ),
    "air_heavy": (
        ["DK - Heavy V1 1", "DK - Heavy V1 2"],
        12, False
    ),

    # === LIGHT ATTACK COMBO (v1: arm swings, v2: punch, v3: reuse v2 for finisher) ===
    "light_v1": (["DK - Light V1 1", "DK - Light V1 2", "DK - Light V1 3",
                  "DK - Light V1 4", "DK - Light V1 5"],                20, False),
    "light_v2": (["DK - Light V2 1", "DK - Light V2 2", "DK - Light V2 3",
                  "DK - Light V2 4", "DK - Light V2 5"],                20, False),
    "light_v3": (["DK - Light V2 1", "DK - Light V2 2", "DK - Light V2 3",
                  "DK - Light V2 4", "DK - Light V2 5"],                20, False),

    # === HEAVY ATTACK COMBO (3 versions) ===
    "heavy_v1": (["DK - Heavy V1 1", "DK - Heavy V1 2"],               10, False),
    "heavy_v2": (["DK - Heavy V2 1", "DK - Heavy V2 2", "DK - Heavy V2 3"],
                                                                          10, False),
    "heavy_v3": (["DK - Heavy V3 1", "DK - Heavy V3 2"],               10, False),
    "ledge_grab": (["DK - Ledge Grab 1", "DK - Ledge Grab 2",
                    "DK - Ledge Grab 3"],                               6,  True),
}

class Animator:
    def __init__(self, sheet, definitions: dict):
        self.sheet   = sheet
        self.defs    = definitions
        self.state   = ""
        self._frame  = 0
        self._timer  = 0
        self.done    = False

    def set_state(self, state: str, force: bool = False):
        if state == self.state and not force:
            return
        self.state  = state
        self._frame = 0
        self._timer = 0
        self.done   = False

    def update(self, dt: float):
        if self.state not in self.defs:
            return
        entry = self.defs[self.state]
        labels = entry[0]
        fps    = entry[1]
        loop   = entry[2]
        loop_start = entry[3] if len(entry) > 3 else 0
        self._timer += dt
        frame_time = 1 / fps
        if self._timer >= frame_time:
            self._timer -= frame_time
            if self._frame < len(labels) - 1:
                self._frame += 1
            elif loop:
                self._frame = loop_start
            else:
                self.done = True

    def get_frame(self, facing_right: bool = True) -> pygame.Surface:
        if self.state not in self.defs:
            return None
        labels = self.defs[self.state][0]
        label  = labels[min(self._frame, len(labels) - 1)]
        surf   = self.sheet.get(label)
        if surf is None:
            return None
        if not facing_right:
            surf = pygame.transform.flip(surf, True, False)
        return surf
