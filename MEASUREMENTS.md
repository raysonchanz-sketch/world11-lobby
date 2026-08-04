# Measurements & Specs

## Display
- Screen: 800×600 (SCREEN_W × SCREEN_H)
- Internal render: varies by zoom (800/zoom × 600/zoom)
- Zoom clamp: 0.3–1.0
- FPS: 60

## Tiles
- Raw tile size: 16×16 (TILE_SIZE)
- Scaled tile size: 32×32 (= TILE_SIZE × SCALE)
- Tileset: 392×784 px RGBA, 1px transparent mortar border, 14×14 beveled surface
- Tiles per row: 24 (tileset_width / TILE_SIZE)

### Tile IDs
| tid | Type     | Collision role           |
|-----|----------|--------------------------|
| 0   | empty    | none                     |
| 3   | brick    | SOLID_WALLS              |
| 4   | solid    | SOLID_WALLS              |
| 5   | sand     | SOLID_WALLS              |
| 10  | platform top | PLATFORM_TIDS        |
| 11  | platform bottom | SKIP_TIDS (visual only) |
| 20  | background | visual only              |
| 21  | background | visual only              |

## Level (world1-1)
- Grid: 57 tiles wide × 36 tiles tall (1824×1152 px)
- Tile JSON format: "tilesetEditing" → Layer 5

### Ground
- Rows: y=33, 34, 35 (tile coords)
- Pixel y: 1056, 1088, 1120
- 3 rows solid, 57 tiles wide
- TIDs: 3 (top), 4 (middle), 5 (bottom)

### Platforms
- Rows: y=30 (top, tid=10), y=31 (bottom, tid=11)
- Pixel y: 960 (top surface), 992 (bottom surface)
- Height: 2 tiles (64px raw), visual collision surface: 8px
- Platform top surface: 96px above ground top (1056 − 960)
- 7 segments with irregular gaps:
  | Start x | End x | Width (tiles) |
  |---------|-------|---------------|
  | 3       | 7     | 5             |
  | 12      | 15    | 4             |
  | 19      | 23    | 5             |
  | 27      | 30    | 4             |
  | 33      | 37    | 5             |
  | 41      | 44    | 4             |
  | 48      | 52    | 5             |

### Level edges
- Left: x=0
- Right: x=56 (tile), 1792 (px)
- Top: y=0
- Bottom: y=35 (tile), 1120 (px)
- Blast zone: -100 px left, LEVEL_W+100 right, LEVEL_H+100 bottom

## Characters

### Mario
- Hitbox: 24×44 (12×22 raw × SCALE)
- Weight: 100
- Run speed: 4.0 / Sprint: 6.0
- Air speed: 4.0 / Air friction: 0.95 / Air accel: 0.4
- Jump force: -10.0 / Double jump: -9.0
- Max jumps: 2
- Gravity: 0.50 / Max fall: 10 / Fast fall: 20
- Attack: 5 dmg, 8 base KB, 0.8 KB growth, range 22, 16 frames
- Special: Hammer Smash (30 frames active, 600 cooldown, 15 dmg, 20 base KB)

### Luigi
- Hitbox: 24×32 (12×16 raw × SCALE)
- Weight: 85
- Run speed: 3.6 / Sprint: 5.5
- Air speed: 4.8 / Air friction: 0.96 / Air accel: 0.5
- Jump force: -10.5 / Double jump: -10.0
- Max jumps: 2
- Gravity: 0.42 / Max fall: 9 / Fast fall: 18
- Attack: 8 dmg, 12 base KB, 1.0 KB growth, range 16, 22 frames
- Special: Shell Throw (30 frames active, 900 cooldown, spawn frame 15)

## Physics

### Gravity & Jump
- GRAVITY: 0.5 (pixels/frame²)
- Mario jump (-10): apex at frame 20, height ≈ 105px
- Mario double jump (-9): apex at frame 18, height ≈ 85px
- Luigi jump (-10.5): apex at frame 21, height ≈ 115px
- Luigi double jump (-10.0): apex at frame 20, height ≈ 105px
- Variable jump height: releasing jump when vel.y < -4 adds +0.6/frame

### Horizontal Movement
- Ground acceleration: ±0.4/frame
- Ground friction: *= 0.85 (sliding stop)
- Air friction: *= 0.95
- Air acceleration: 0.4 (Mario) / 0.5 (Luigi)
- Top speed with P-Meter=100: base_speed + 2
- P-Meter: +2/frame when sprinting at ≥ run_speed, -4/frame otherwise, max 100

### Fast Fall
- Trigger: vel.y > 0 + crouch
- Max fall during fast fall: 20 (Mario) / 18 (Luigi)

### Collision
- Ground probe: rect moved 2px down; platform check: abs(bottom − top) ≤ 2
- Coyote time: 6 frames after leaving ground
- Jump buffer: 8 frames
- Drop-through: 15 frame timer, vel.y = 2 nudge
- Slide: crouch + sprint at vel.x > 1.0, 25 frame timer

### Knockback
- KB formula: ((2P + D)/20 × (200/(W+100)) × 1.4 + 18) × KB_growth + base_KB
- Vel scale: x=0.20, y=0.15 (×1.5 for upward type)
- DI strength: 0.25
- Hitstun: int(KB × 0.4) frames
- Stale moves: −8% per reuse, floor 30%

## Hitbox Sizes

### Normal Attack
- Mario: rect extended by attack_range (22) in facing direction
- Luigi: rect extended by attack_range (16) in facing direction

### Special Attack
- Mario (Hammer Smash): rect enlarged: height × 1.4, shifted up 20% of height, +55px reach
- Luigi (Shell Throw): spawns KoopaShell entity

### Stomp
- Trigger: vel.y > 0 AND rect.bottom < target.rect.centery + 6
- Damage: 5, KB: 6 base, 0.4 growth
- Reward: vel.y = −10, restore jumps

## Koopa Shell
- Display size: 32×28 (16×14 raw × SCALE)
- Speed: 8 px/frame
- Lifetime: 300 frames (5 seconds)
- Grace frames: 15 (can't hit owner)
- Bounces off walls

## Camera
- Smash-style midpoint tracking
- Smooth follow: x=0.08 lerp, y=0.06 lerp
- Zoom lerp: 0.04
- Auto-zoom: fits both players within 75% of screen (width & height), min 100px separation
- Level clamping: offset bounded to [0, level_size − render_size]

## Animation Rates
- Idle: 6 fps
- Walk: 8 fps (2 frames)
- Run: 10 fps (3 frames)
- Jump: 6 fps (2 frames Mario / 1 frame Luigi)
- Slide: 6 fps
- Attack (spin/kick): 6 fps
- Hammer Smash: 12 fps (6 frames)
- Shell Throw: 10 fps (3 frames)

## Controls

### P1
| Action | Key    |
|--------|--------|
| Left   | A      |
| Right  | D      |
| Jump   | W      |
| Crouch | S      |
| Attack | F / G  |
| Special| E      |
| Sprint | LShift / Z |

### P2
| Action | Key          |
|--------|--------------|
| Left   | Left Arrow   |
| Right  | Right Arrow  |
| Jump   | Up Arrow     |
| Crouch | Down Arrow   |
| Attack | J / K        |
| Special| O            |
| Sprint | RShift / /   |
