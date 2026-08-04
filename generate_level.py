"""Generate World 1-1 level with classic Mario Bros layout.

Tile IDs:
  1 = ground_block (solid floor)
  2 = platform_brick (floating bricks, walkable platform)
  3 = steel_block (strong block)
  4 = pipe

Layout:
  - Continuous ground at y=33 (rows 33-35)
  - Floating brick platforms at y=27 and y=22
  - Steel blocks at key positions
  - Pipes at classic positions
"""
import json

LEVEL_W = 57   # x: 0-56
LEVEL_H = 36   # y: 0-35
GROUND_Y = 33

tiles = {}

# ===== GROUND (3 rows) =====
for x in range(LEVEL_W):
    tiles[f"{x}-{GROUND_Y}"] = {"x": x, "y": GROUND_Y, "crop": 1}
    tiles[f"{x}-{GROUND_Y+1}"] = {"x": x, "y": GROUND_Y+1, "crop": 1}
    tiles[f"{x}-{GROUND_Y+2}"] = {"x": x, "y": GROUND_Y+2, "crop": 1}

# ===== FLOATING BRICK PLATFORMS (2 rows tall) =====
platforms_y29 = [
    (8, 11),
    (20, 23),
    (32, 35),
    (45, 48),
]

platforms_y25 = [
    (14, 17),
    (37, 40),
]

for x_start, x_end in platforms_y29:
    for x in range(x_start, x_end + 1):
        tiles[f"{x}-29"] = {"x": x, "y": 29, "crop": 2}

for x_start, x_end in platforms_y25:
    for x in range(x_start, x_end + 1):
        tiles[f"{x}-25"] = {"x": x, "y": 25, "crop": 2}

# ===== STEEL BLOCKS =====
steel_positions = [(9, 29), (21, 29), (33, 29), (46, 29),
                   (15, 25), (38, 25)]
for sx, sy in steel_positions:
    tiles[f"{sx}-{sy}"] = {"x": sx, "y": sy, "crop": 3}

# ===== PIPES (1-tile wide, classic positions) =====
pipe_configs = [
    (15, 1),    # 1 tile tall
    (30, 1),    # 1 tile tall
    (42, 1),    # 1 tile tall
]
for pipe_x, pipe_h in pipe_configs:
    for dy in range(pipe_h):
        py = GROUND_Y - 1 - dy
        tiles[f"{pipe_x}-{py}"] = {"x": pipe_x, "y": py, "crop": 4}

# ===== UPDATE JSON =====
with open('assets/levels/world1-1.json', 'r') as f:
    data = json.load(f)

if "tilesetEditing" in data:
    for item in data["tilesetEditing"]:
        if "layers" in item:
            for layer in item["layers"]:
                if layer.get("layerId") == 5 or layer.get("name") == "Layer 5":
                    layer["tiles"] = tiles
                    break

with open('assets/levels/world1-1.json', 'w') as f:
    json.dump(data, f, separators=(',', ':'))

print(f"Level generated: {len(tiles)} tiles")
print(f"Ground: y={GROUND_Y}-{GROUND_Y+2} ({LEVEL_W} tiles wide)")
print(f"Platforms at y=29: {len(platforms_y29)} segments")
print(f"Platforms at y=25: {len(platforms_y25)} segments")
print(f"Pipes: {len(pipe_configs)}")
