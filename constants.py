import pygame

# --- Display Settings ---
SCREEN_W = 800
SCREEN_H = 600
FPS = 60

# --- Tile and Asset Scaling ---
TILE_SIZE = 32
SCALE = 1
MAP_SCALE = 1

# --- Movement Physics (these are now DEFAULTS, overridden by CHARACTER_STATS) ---
RUN_SPEED = 4.0
FRICTION = 0.85
GRAVITY = 0.65
MAX_FALL = 14
JUMP_FORCE = -10
DOUBLE_JUMP_FORCE = -9.0

# --- Aerial Physics (Smash Bros exact model) ---
AIR_FRICTION_LINEAR = 0.015  # Tiny drag per frame — lets momentum coast naturally
AIR_DRIFT_DEADZONE = 0.1     # Stick threshold to register air drift input
JUMP_MOMENTUM_MULT = 0.8     # Ground speed retained when jumping from dash
L_CANCEL_LAG_MULT = 0.5      # L-cancel halves landing lag
SHORT_HOP_FRAMES = 2         # Release jump within this many frames = short hop
SHORT_HOP_FORCE_MULT = 0.5   # Short hop is 50% of full hop height
JUMP_SQUAT_FRAMES = 3        # Pre-jump animation frames (Smash: 3-8, most chars 3-5)
AERIAL_DRIFT_MULT = 0.75     # Air speed multiplier during aerial attacks
FAST_FALL_MULT = 1.75        # Gravity multiplier when fast-falling (Smash: 1.5x-1.9x)
AUTO_CANCEL_LAG = 4          # Landing lag when landing in auto-cancel window

# --- Air Dodge ---
AIR_DODGE_SPEED = 10.0       # Initial burst speed of directional air dodge
AIR_DODGE_DURATION = 20      # Total frames of air dodge
AIR_DODGE_INVULN_START = 1   # First frame of invincibility
AIR_DODGE_INVULN_END = 15    # Last frame of invincibility

# --- Slide Combat ---
SLIDE_DAMAGE_IDLE = 3           # Minor damage when hitting grounded idle opponent
SLIDE_BASE_KB_IDLE = 6          # Small upward knockback
SLIDE_KB_GROWTH_IDLE = 0.5
SLIDE_COUNTER_DAMAGE = 8        # Damage to stomper when they stomp a sliding player
SLIDE_COUNTER_KB = 22           # Significant upward knockback (launches stomper)
SLIDE_COUNTER_KB_GROWTH = 1.6   # Scales with stomper's percent
SLIDE_COUNTER_BOUNCE = -14      # Stomper gets launched upward

# --- Knockback Conversion ---
# Smash Bros standard is 0.03 on a ~6000px stage.
# Our stage is 1824px with blast zones ~350px outside edges.
# Scale = 0.2 keeps jabs survival at low %, lethal at high %.
LAUNCH_SPEED_SCALE = 0.2
DI_MAX_ANGLE = 18.0         # Max DI shift in degrees (Smash Bros: 18°)
RAGE_MAX_MULT = 1.3         # Max rage multiplier at 100%+ attacker percent
RAGE_SCALE = 0.3            # Rage bonus = 0.3 per 100% attacker damage

# --- Blast Zones (Smash Bros style — generous recovery room) ---
BLAST_ZONE_MARGIN_SIDE = 350 * MAP_SCALE   # Pixels outside stage edges (sides)
BLAST_ZONE_MARGIN_BOTTOM = 400 * MAP_SCALE # Pixels below stage bottom (recovery room)
BLAST_ZONE_MARGIN_TOP = 300 * MAP_SCALE    # Pixels above stage top (upward KOs)

# --- Stale Queue (9-slot system, exact Smash Bros multipliers) ---
# Each slot reduces damage of a repeated move. Sum all slots for total reduction.
STALE_SLOT_MULTIPLIERS = [0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
STALE_FRESH_BONUS = 1.05    # 5% bonus if queue is empty
STALE_MIN_MULT = 0.55       # Max 45% reduction cap

# --- Combo Mechanics ---
KB_LAUNCH_THRESHOLD = 50.0  # Minimum knockback to launch victim off ground
HIT_PAUSE_FRAMES = 6  # Frames victim freezes in place before launch

# --- Ledge Grab System ---
LEDGE_GRAB_RANGE_X = 18     # Horizontal range to detect ledge
LEDGE_GRAB_RANGE_Y = 24     # Vertical range to detect ledge
LEDGE_GRAB_INVULN = 12      # Invincibility frames on ledge grab
LEDGE_HANG_MAX = 300        # Max frames before forced getup
LEDGE_GETUP_LAG = 18        # Frames of lag after normal getup
LEDGE_JUMP_VX = 4.0         # Horizontal speed on ledge jump
LEDGE_JUMP_VY = -10.0       # Vertical speed on ledge jump
LEDGE_DROP_VY = 2.0         # Downward speed on ledge drop
LEDGE_ATTACK_DAMAGE = 8     # Ledge attack damage
LEDGE_ATTACK_KB = 12        # Ledge attack base knockback
LEDGE_ATTACK_FRAMES = 20    # Ledge attack duration
LEDGE_ATTACK_HIT_START = 6  # Ledge attack hitbox active start
LEDGE_ATTACK_HIT_END = 12   # Ledge attack hitbox active end

# --- Counter-Hit System ---
# If you hit someone during their attack startup (before impact frame),
# your hit gets bonus KB multiplier and hitstun bonus.
COUNTER_HIT_KB_MULT = 1.4      # 40% more knockback on counter-hit
COUNTER_HIT_HITSTUN_BONUS = 8  # Extra hitstun frames on counter-hit
COUNTER_HIT_VISUAL_DURATION = 12  # Flash frames for counter-hit feedback

# --- Shield Mechanics ---
MAX_SHIELD_HEALTH = 50.0    # Maximum shield health
SHIELD_DECAY_RATE = 0.08    # Shield health lost per frame when held
SHIELD_REGEN_RATE = 0.12    # Shield health gained per frame when released
SHIELD_MIN_HEALTH = 0.0     # Minimum shield health (shield breaks at 0)
SHIELD_BREAK_STUN = 60      # Frames of stun when shield breaks
SHIELD_PUSHBACK_ATTACKER = 0.4  # Attacker pushback multiplier on shield hit
SHIELD_PUSHBACK_DEFENDER = 0.6  # Defender pushback multiplier on shield hit
SHIELD_VISUAL_RADIUS = 30   # Radius of shield bubble in pixels
SHIELD_VISUAL_ALPHA = 128   # Transparency of shield bubble (0-255)
SHIELD_STUN_GROUND_MULT = 0.8   # Ground attack shield stun multiplier
SHIELD_STUN_AERIAL_MULT = 0.33  # Aerial attack shield stun multiplier
SHIELD_STUN_BASE = 2           # Base shield stun frames
SHIELD_STUN_MIN = 4            # Minimum shield stun frames
SHIELD_VISUAL_COLOR = (100, 150, 255, 128)  # Blue shield bubble with alpha

# --- Aerial Attack Landing Lag ---
# In Smash Bros, aerials have base landing lag + reduced by L-cancel
# These are the BASE landing lag values (before L-cancel reduction)
AERIAL_LAG_NEUTRAL = 10
AERIAL_LAG_FORWARD = 14
AERIAL_LAG_BACK = 12
AERIAL_LAG_UP = 11
AERIAL_LAG_DOWN = 16  # Dair often has the most lag (spike risk/reward)

# --- Normal Attack Stats (DEFAULTS, overridden by CHARACTER_STATS) ---
ATTACK_STATS = {
    "mario": {"damage": 5,  "base_knockback": 10,  "knockback_growth": 1.2},
    "luigi": {"damage": 12, "base_knockback": 14,  "knockback_growth": 1.4},
}

STOMP_DAMAGE = 5
STOMP_BASE_KNOCKBACK = 12
STOMP_KNOCKBACK_GROWTH = 1.0
STOMP_KNOCKBACK = 10
STOMP_COOLDOWN = 20  # Frames before same player can be stomped again

ENEMY_CONTACT_DAMAGE = 3
ENEMY_CONTACT_KNOCKBACK = 4
ENEMY_CONTACT_COOLDOWN = 30

# --- Grrrol Enemy ---
GRRROL_SPEED = 2.5
GRRROL_CONTACT_DAMAGE = 5
GRRROL_CONTACT_KNOCKBACK = 8
GRRROL_CONTACT_COOLDOWN = 40
GRRROL_SIZE = 30
GRRROL_ANIM_SPEED = 0.08
GRRROL_KILL_PERCENT = 60

# --- Bob-omb Enemy ---
BOBOMB_SIZE = 28
BOBOMB_FALL_SPEED = 2.0
BOBOMB_TARGET_SPEED = 1.5
BOBOMB_EXPLOSION_RADIUS = 100
BOBOMB_EXPLOSION_DAMAGE = 12
BOBOMB_EXPLOSION_KB = 12
BOBOMB_EXPLOSION_LAG = 20
BOBOMB_TARGET_HEIGHT = 42

KAMEK_SIZE = 30
KAMEK_SCALE = 3
KAMEK_FLY_SPEED = 1.8
KAMEK_DRIFT_AMP = 40
KAMEK_DRIFT_FREQ = 0.8
KAMEK_HEALTH = 45
KAMEK_MAGIC_DAMAGE = 6
KAMEK_MAGIC_KB = 10
KAMEK_MAGIC_SPEED = 5.0
KAMEK_MAGIC_SIZE = 16
KAMEK_MAGIC_COOLDOWN = 40
KAMEK_SPAWN_INTERVAL_MIN = 120
KAMEK_SPAWN_INTERVAL_MAX = 240
KAMEK_TELEPORT_RANGE = 200
KAMEK_TELEPORT_COOLDOWN = 240
KAMEK_FLY_MIN_Y = 650
KAMEK_FLY_MAX_Y = 1200

# --- Controls ---
CTRL_P1 = {
    'left': pygame.K_a,
    'right': pygame.K_d,
    'jump': pygame.K_w,
    'crouch': pygame.K_s,
    'attack': pygame.K_f,
    'attack_alt': pygame.K_g,
    'special': pygame.K_e,
    'shield': pygame.K_q
}

CTRL_P2 = {
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'jump': pygame.K_UP,
    'crouch': pygame.K_DOWN,
    'attack': pygame.K_j,
    'attack_alt': pygame.K_k,
    'special': pygame.K_o,
    'shield': pygame.K_p
}

# --- Mario Hammer Smash ---
HAMMER_SMASH_COOLDOWN = 600
HAMMER_SMASH_ACTIVE_FRAMES = 30
HAMMER_SMASH_HIT_START = 8
HAMMER_SMASH_HIT_END = 20
HAMMER_SMASH_DAMAGE = 15
HAMMER_SMASH_BASE_KNOCKBACK = 25
HAMMER_SMASH_KNOCKBACK_GROWTH = 1.5
HAMMER_SMASH_KB_BONUS = 1.20

# --- Mario Fire Punch ---
FIRE_PUNCH_COOLDOWN = 45
FIRE_PUNCH_ACTIVE_FRAMES = 18
FIRE_PUNCH_HIT_START = 4
FIRE_PUNCH_HIT_END = 12
FIRE_PUNCH_DAMAGE = 10
FIRE_PUNCH_BASE_KNOCKBACK = 14
FIRE_PUNCH_KNOCKBACK_GROWTH = 1.3
FIRE_PUNCH_KB_BONUS = 1.0

# --- Luigi Shell Throw ---
SHELL_THROW_COOLDOWN = 900
SHELL_THROW_ACTIVE_FRAMES = 30

HEAD_DRILL_COOLDOWN = 750
HEAD_DRILL_ACTIVE_FRAMES = 36
HEAD_DRILL_DAMAGE = 18
HEAD_DRILL_KNOCKBACK_GROWTH = 1.8
HEAD_DRILL_BASE_KNOCKBACK = 26
HEAD_DRILL_KB_BONUS = 1.2
HEAD_DRILL_HIT_START = 4
HEAD_DRILL_HIT_END = 20
SHELL_THROW_SPAWN_FRAME = 15
SHELL_SPEED = 8
SHELL_DAMAGE = 12
SHELL_BASE_KNOCKBACK = 18
SHELL_KNOCKBACK_GROWTH = 1.2
SHELL_THROW_KB_BONUS = 1.35
SHELL_GRACE_FRAMES = 3

# --- Heavy Attack (attack_alt) ---
# Slower startup, more damage/knockback, cooldown between uses
HEAVY_ATTACK_COOLDOWN = 30      # 0.5 seconds at 60fps (combo-friendly)
HEAVY_ATTACK_DAMAGE_MULT = 2.0  # Double damage
HEAVY_ATTACK_KB_MULT = 1.4      # 40% more knockback (reduced for combo potential)
HEAVY_ATTACK_FRAMES = 28        # Slower than normal (16-22)
HEAVY_ATTACK_HIT_START = 10     # Late active frames (committal)
HEAVY_ATTACK_HIT_END = 20
HEAVY_ATTACK_RANGE_MULT = 1.3   # Slightly more reach

# --- Yoshi Egg Throw (Q special) ---
EGG_THROW_COOLDOWN = 60         # 1 second cooldown
EGG_THROW_ACTIVE_FRAMES = 25    # Total animation duration
EGG_THROW_SPAWN_FRAME = 12      # Frame when egg spawns
EGG_SPEED = 9                   # Projectile speed
EGG_DAMAGE = 8
EGG_BASE_KNOCKBACK = 12
EGG_KNOCKBACK_GROWTH = 1.0
EGG_KB_BONUS = 1.0
EGG_SIZE = 20                   # Projectile hitbox size
EGG_BOUNCE = True               # Egg bounces off walls
EGG_GRAVITY = 0.3               # Slight arc on egg trajectory

# --- Yoshi Egg Roll (E special) ---
EGG_ROLL_COOLDOWN = 120         # 2 seconds cooldown
EGG_ROLL_ACTIVE_FRAMES = 48     # Long roll duration
EGG_ROLL_SPEED = 10             # Roll speed
EGG_ROLL_DAMAGE = 6             # Damage per hit during roll
EGG_ROLL_BASE_KNOCKBACK = 8
EGG_ROLL_KNOCKBACK_GROWTH = 0.6
EGG_ROLL_KB_BONUS = 1.0
EGG_ROLL_KB_TYPE = "downward"   # Ground bounce setup
EGG_ROLL_HIT_INTERVAL = 8       # Damage every N frames during roll

# --- Yoshi Player Throw (grab + hurl behind) ---
PLAYER_THROW_RANGE = 35         # Grab range in front of Yoshi
PLAYER_THROW_COOLDOWN = 90      # 1.5 seconds cooldown
PLAYER_THROW_FRAMES = 18        # Total animation
PLAYER_THROW_RELEASE_FRAME = 8  # Frame when opponent is thrown
PLAYER_THROW_SPEED = 14         # Launch speed of thrown player
PLAYER_THROW_DAMAGE = 3         # Minor damage
PLAYER_THROW_GRAB_DURATION = 12 # How long opponent is held

# --- DK Barrel Throw (Q special) ---
BARREL_THROW_COOLDOWN = 90       # 1.5 seconds cooldown
BARREL_THROW_ACTIVE_FRAMES = 30  # Total animation
BARREL_THROW_SPAWN_FRAME = 15    # Frame when barrel spawns
BARREL_SPEED = 6                 # Barrel roll speed
BARREL_GRAVITY = 0.4             # Heavy — stays on ground
BARREL_DAMAGE = 10
BARREL_BASE_KNOCKBACK = 14
BARREL_KNOCKBACK_GROWTH = 1.2
BARREL_KB_BONUS = 1.0
BARREL_SIZE = 20                 # Barrel hitbox size
BARREL_BOUNCE = True             # Bounces off walls
BARREL_LIFETIME = 300            # 5 seconds

# --- DK Barrel Smash (E special) ---
BARREL_SMASH_COOLDOWN = 600      # 10 seconds cooldown
BARREL_SMASH_ACTIVE_FRAMES = 30
BARREL_SMASH_HIT_START = 8
BARREL_SMASH_HIT_END = 20
BARREL_SMASH_DAMAGE = 18
BARREL_SMASH_BASE_KNOCKBACK = 28
BARREL_SMASH_KNOCKBACK_GROWTH = 1.6
BARREL_SMASH_KB_BONUS = 1.25

# --- Yoshi Combo System ---
LIVES = 3
MATCH_TIME = 180  # seconds (3 minutes)

# Per-version combo stats: {version: (damage, base_kb, kb_growth, frames, hit_start, hit_end, kb_type)}
# Each version scales up knockback, so V3 finisher launches much harder than V1
YOSHI_LIGHT_COMBO = {
    1: (3,  8,  0.9, 12, 3, 7,  "normal"),   # Jab — low KB, combos into V2
    2: (4,  10, 1.0, 14, 3, 9,  "straight"),  # Mid — horizontal, combos into V3
    3: (6,  16, 1.5, 14, 4, 8,  "straight"),  # Finisher — horizontal launch, high KB growth
}
YOSHI_HEAVY_COMBO = {
    1: (12, 14, 1.3, 28, 10, 20, "normal"),   # Opener — moderate KB
    2: (16, 18, 1.5, 28, 10, 20, "straight"), # Mid — horizontal launch
    3: (24, 28, 1.8, 28, 10, 20, "straight"), # Finisher — devastating horizontal kill
}

MARIO_LIGHT_COMBO = {
    1: (4,  8,  1.0, 12, 3, 6,  "normal"),    # Jab — balanced starter
    2: (5,  12, 1.2, 14, 3, 8,  "straight"),  # Mid — horizontal push
    3: (8,  18, 1.6, 16, 4, 10, "upward"),    # Finisher — upward launch
}
MARIO_HEAVY_COMBO = {
    1: (10, 12, 1.2, 28, 10, 20, "normal"),   # Opener — strong starter
    2: (14, 16, 1.4, 28, 10, 20, "straight"), # Mid — horizontal
    3: (20, 24, 1.8, 28, 10, 20, "straight"), # Finisher — kill move
}
LUIGI_LIGHT_COMBO = {
    1: (3,  8,  1.0, 12, 3, 6,  "normal"),    # Jab — fast starter
    2: (5,  12, 1.2, 14, 3, 8,  "upward"),    # Mid — upward juggle
    3: (7,  18, 1.5, 16, 4, 10, "upward"),    # Finisher — upward launch
}
LUIGI_HEAVY_COMBO = {
    1: (9,  12, 1.2, 28, 10, 20, "normal"),   # Opener — strong starter
    2: (13, 16, 1.4, 28, 10, 20, "straight"), # Mid — horizontal
    3: (18, 24, 1.8, 28, 10, 20, "straight"), # Finisher — kill move
}
DK_LIGHT_COMBO = {
    1: (5,  10, 1.1, 14, 3, 9,  "normal"),    # Arm swing double hit
    2: (6,  12, 1.2, 16, 3, 10, "straight"),   # Punch
    3: (8,  18, 1.6, 16, 4, 10, "straight"),   # Punch finisher
}
DK_HEAVY_COMBO = {
    1: (12, 14, 1.3, 28, 10, 20, "normal"),    # Opener
    2: (16, 18, 1.5, 28, 10, 20, "straight"),  # Mid
    3: (22, 26, 1.8, 28, 10, 20, "straight"),  # Finisher — devastating
}

# ============================================================
# FINISHER COMBOS — Heavy+Light, Light+Special, Heavy+Special
# ============================================================
FINISHER_EFFECTS = {
    "mario": {
        ("heavy", "light"): {
            "type": "stun",
            "duration": 20,
        },
        ("light", "fire_punch"): {
            "type": "fire_dot",
            "damage_per_tick": 1,
            "tick_interval": 15,
            "total_ticks": 6,
            "kb_mult": 2.0,
        },
        ("heavy", "hammer_smash"): {
            "type": "slow",
            "speed_mult": 0.65,
            "damage_mult": 0.65,
            "duration": 480,
        },
    },
    "luigi": {
        ("heavy", "light"): {
            "type": "stun",
            "duration": 20,
        },
        ("light", "blastshot"): {
            "type": "kb_amp",
            "kb_taken_mult": 1.10,
            "duration": 300,
        },
        ("heavy", "head_drill"): {
            "type": "stun",
            "duration": 30,
            "extra_hitstun": 180,
        },
    },
    "yoshi": {
        ("heavy", "light"): {
            "type": "stun",
            "duration": 20,
        },
        ("heavy", "light_extra"): {
            "type": "damage_amp",
            "damage_taken_mult": 1.01,
            "duration": 180,
        },
        ("light", "egg_roll"): {
            "type": "hitstun_amp",
            "extra_hitstun": 120,
            "damage_dealt_mult": 1.10,
            "duration": 120,
        },
    },
    "donkey_kong": {
        ("heavy", "light"): {
            "type": "stun",
            "duration": 24,
        },
        ("light", "barrel_throw"): {
            "type": "fire_dot",
            "damage_per_tick": 1,
            "tick_interval": 15,
            "total_ticks": 5,
            "kb_mult": 1.8,
        },
        ("heavy", "barrel_smash"): {
            "type": "kb_amp",
            "kb_taken_mult": 1.15,
            "duration": 300,
        },
    },
}

# Per-character special names used for finisher lookups
CHAR_SPECIAL_NAMES = {
    "mario": "hammer_smash",
    "luigi": "head_drill",
    "yoshi": "egg_roll",
    "donkey_kong": "barrel_smash",
}

# ============================================================
# CHARACTER STATS — The core of character differentiation
# ============================================================
# Archetype guide:
#   Rushdown  = fast combos, low knockback, close range
#   Balanced  = average everything, good for learning
#   Light     = fast, floaty, launched easily, good recovery
#   Heavy     = slow, hard to launch, devastating hits
#   Sword     = long reach, average speed, linear attacks
#   Projectile= controls space, weak up close

CHARACTER_STATS = {
    "mario": {
        # --- Archetype: Balanced / Rushdown ---
        # All-rounder with slight rushdown lean.
        # Fast attacks, low damage per hit, combos well.
        # Hammer Smash gives him kill power at close range.

        "display_name": "Mario",

        # Weight (affects knockback distance)
        # 100 = standard. Heavy = 120+, Light = 80-
        "weight": 100,

        # Ground movement
        "run_speed":       5.0,    # Base horizontal speed

        "friction":        0.85,   # Ground deceleration (lower = slide more)

        # Air movement (base values, scaled by weight in Player.__init__)
        # weight_factor = 100 / weight → lighter chars get faster air speed
        "air_speed":       6.0,    # Max horizontal air control (before weight scaling)
        "air_friction":    0.015,  # Tiny drag per frame — momentum coasts naturally
        "air_accel":       0.8,    # How fast you change direction in air (before weight scaling)

        # Jump
        "jump_force":          -11.5,
        "double_jump_force":   -10.0,
        "max_jumps":           2,

        # Gravity
        "gravity":         0.65,   # Smash Bros: snappy falling, not floaty
        "max_fall":        14,     # Terminal velocity (higher = fall faster)
        "fast_fall_speed": 22.0,   # gravity × FAST_FALL_MULT (Smash: 1.5-1.9x)

        # Normal attack (ground)
        "attack_damage":         5,
        "attack_base_knockback": 10,
        "attack_knockback_growth": 1.2,
        "attack_range":          22,     # Reach in pixels
        "attack_frames":         16,     # Duration of attack animation
        "attack_hit_start":      5,      # First frame hitbox is active
        "attack_hit_end":        10,     # Last frame hitbox is active

        # Aerial attacks: (damage, base_knockback, knockback_growth, range, duration, hit_start, hit_end, kb_type, ac_start, ac_end)
        # kb_type: "normal" = diagonal, "straight" = horizontal, "upward" = vertical, "spike" = downward
        # ac_start/ac_end: auto-cancel windows — landing in these frames = AUTO_CANCEL_LAG instead of full lag
        "aerial_neutral":   (5, 8, 1.0, 20, 18, 4, 12, "normal", 0, 2),
        "aerial_forward":   (7, 12, 1.3, 26, 20, 6, 14, "normal", 0, 3),
        "aerial_back":      (9, 14, 1.4, 22, 18, 5, 12, "straight", 0, 2),
        "aerial_up":        (6, 10, 1.2, 20, 16, 4, 10, "upward", 0, 2),
        "aerial_down":      (10, 8, 1.0, 18, 24, 8, 18, "spike", 0, 4),

        # Special
        "special_name":         "hammer_smash",
    },

    "luigi": {
        # --- Archetype: Light / Projectile ---
        # Floaty and light — launched further by hits.
        # Better air control and recovery (higher double jump).
        # Weaker up close but Shell Throw controls space from distance.

        "display_name": "Luigi",

        "weight": 85,              # LIGHT — launched further

        "run_speed":       4.5,    # Slightly slower on ground
        "friction":        0.85,

        "air_speed":       5.5,    # Reduced from 6.5 — less extreme aerial drift
        "air_friction":    0.018,  # More drag than before (was 0.012) — slows down sooner
        "air_accel":       0.65,   # Reduced from 0.85 — slower direction changes in air

        "jump_force":          -12.0,  # Slightly higher ground jump
        "double_jump_force":   -11.0,  # MUCH better recovery
        "max_jumps":           2,

        "gravity":         0.55,   # FLOATY but not too slow — still responsive
        "max_fall":        12,
        "fast_fall_speed": 19.0,   # gravity × FAST_FALL_MULT (floaty = lower FF)

        "attack_damage":         8,     # Stronger per hit
        "attack_base_knockback": 14,
        "attack_knockback_growth": 1.4,
        "attack_range":          16,    # SHORT range
        "attack_frames":         22,    # More lag after attacking
        "attack_hit_start":      5,
        "attack_hit_end":        10,

        # Aerial attacks: (damage, base_knockback, knockback_growth, range, duration, hit_start, hit_end, kb_type, ac_start, ac_end)
        "aerial_neutral":   (6, 10, 1.1, 22, 20, 4, 14, "normal", 0, 3),
        "aerial_forward":   (8, 14, 1.5, 20, 22, 7, 16, "normal", 0, 3),
        "aerial_back":      (11, 16, 1.6, 18, 20, 6, 14, "straight", 0, 2),
        "aerial_up":        (7, 12, 1.3, 18, 18, 4, 12, "upward", 0, 2),
        "aerial_down":      (12, 6, 0.9, 16, 26, 8, 20, "spike", 0, 4),

        "special_name":         "head_drill",
    },

    "yoshi": {
        # --- Archetype: Rushdown ---
        # Extremely fast ground speed, light weight.
        # Low knockback per hit but very fast attacks — overwhelm with volume.
        # Roll has downward knockback (ground bounce setup).
        # Heavy after roll = big bonus knockback.

        "display_name": "Yoshi",

        "weight": 75,               # VERY LIGHT — launched far

        "run_speed":       6.0,     # Fastest runner
        "friction":        0.88,    # Snappy stops

        "air_speed":       5.8,     # Normal air control
        "air_friction":    0.016,   # Normal drag
        "air_accel":       0.75,    # Normal direction changes

        "jump_force":          -11.0,
        "double_jump_force":   -9.5,
        "max_jumps":           2,

        "gravity":         0.70,    # Slightly floaty
        "max_fall":        13,
        "fast_fall_speed": 20.0,

        # Fast attacks, low knockback — rushdown style
        "attack_damage":         4,     # Weak per hit
        "attack_base_knockback": 6,     # Low KB
        "attack_knockback_growth": 0.8,
        "attack_range":          20,    # Moderate reach
        "attack_frames":         12,    # FAST
        "attack_hit_start":      3,     # Very quick active
        "attack_hit_end":        7,

        # Aerial attacks: fast, low knockback, combo-oriented
        "aerial_neutral":   (4, 6, 0.8, 18, 14, 3, 9, "normal", 0, 2),
        "aerial_forward":   (5, 8, 1.0, 22, 16, 4, 11, "normal", 0, 2),
        "aerial_back":      (6, 10, 1.1, 18, 14, 3, 10, "straight", 0, 2),
        "aerial_up":        (5, 7, 0.9, 16, 14, 3, 9, "upward", 0, 2),
        "aerial_down":      (7, 5, 0.7, 14, 20, 5, 14, "spike", 0, 3),

        "special_name":         "egg_throw",

        # Yoshi-specific: roll KB type is downward
        "roll_kb_type":         "downward",
        # Heavy after roll bonus
        "roll_heavy_bonus":     2.0,
    },

    "donkey_kong": {
        # --- Archetype: Rushdown ---
        # Medium weight, fast ground speed, long reach.
        # Barrel throw controls space; ground pound for kill power.
        # Strong combos, high knockback per hit.

        "display_name": "DONKEY KONG",

        "weight": 95,               # Medium-heavy

        "run_speed":       5.2,     # Fast rushdown
        "friction":        0.86,    # Snappy stops

        "air_speed":       5.5,     # Good air control
        "air_friction":    0.014,   # Light drag
        "air_accel":       0.75,    # Normal direction changes

        "jump_force":          -11.0,
        "double_jump_force":   -9.5,
        "max_jumps":           2,

        "gravity":         0.65,
        "max_fall":        14,
        "fast_fall_speed": 22.0,

        # Strong attacks, long reach
        "attack_damage":         6,
        "attack_base_knockback": 12,
        "attack_knockback_growth": 1.3,
        "attack_range":          26,     # Long arms
        "attack_frames":         16,
        "attack_hit_start":      5,
        "attack_hit_end":        11,

        # Aerial attacks: strong, long reach
        "aerial_neutral":   (6, 10, 1.1, 24, 18, 4, 12, "normal", 0, 2),
        "aerial_forward":   (8, 14, 1.3, 30, 20, 6, 14, "normal", 0, 3),
        "aerial_back":      (10, 16, 1.4, 26, 18, 5, 12, "straight", 0, 2),
        "aerial_up":        (7, 12, 1.2, 22, 16, 4, 10, "upward", 0, 2),
        "aerial_down":      (12, 8, 1.0, 20, 24, 8, 18, "spike", 0, 4),

        "special_name":         "barrel_smash",
    },
}
