"""Generate Factory level layout using proper tile IDs.

Tile IDs:
  1 = ground_edge(top left)
  2 = ground_edge(top right)
  3 = ground_normal(face up)
  4 = ground_edge(bottom left)
  5 = ground_edge(bottom right)
  6 = ground_normal(face down)
  7 = ground_middle(far left)
  8 = ground_middle(far right)
  9 = ground_middle(normal)
  10 = platform_edge(top left)
  11 = platform_edge(top right)
  12 = normal_platform(face_up)
  13 = platform_edge(bottom left)
  14 = platform_edge(bottom right)
  15 = normal_platform(face_down)
  16 = conveyor
  17 = factory_pipe
  18 = metal_block
  19 = pipe_vertical_top
  20 = pipe_vertical_middle
  21 = pipe_vertical_bottom
  22 = pipe_horizontal_left
  23 = pipe_horizontal_middle
  24 = pipe_horizontal_right
"""
import json
import os

LEVEL_W = 57
LEVEL_H = 36
GROUND_Y = 33

tiles = {}


def place_ground(x_start, x_end, top_y, depth=3):
    width = x_end - x_start + 1
    if width < 1:
        return

    # Top row: edge_top_left ... face_up ... edge_top_right
    if depth >= 1:
        if width == 1:
            tiles[f"{x_start}-{top_y}"] = {"x": x_start, "y": top_y, "crop": 3}
        else:
            tiles[f"{x_start}-{top_y}"] = {"x": x_start, "y": top_y, "crop": 1}
            for x in range(x_start + 1, x_end):
                tiles[f"{x}-{top_y}"] = {"x": x, "y": top_y, "crop": 3}
            tiles[f"{x_end}-{top_y}"] = {"x": x_end, "y": top_y, "crop": 2}

    # Middle rows: far_left ... middle_normal ... far_right
    for dy in range(1, depth - 1):
        row_y = top_y + dy
        if width == 1:
            tiles[f"{x_start}-{row_y}"] = {"x": x_start, "y": row_y, "crop": 9}
        else:
            tiles[f"{x_start}-{row_y}"] = {"x": x_start, "y": row_y, "crop": 7}
            for x in range(x_start + 1, x_end):
                tiles[f"{x}-{row_y}"] = {"x": x, "y": row_y, "crop": 9}
            tiles[f"{x_end}-{row_y}"] = {"x": x_end, "y": row_y, "crop": 8}

    # Bottom row: edge_bot_left ... face_down ... edge_bot_right
    if depth >= 2:
        bot_y = top_y + depth - 1
        if width == 1:
            tiles[f"{x_start}-{bot_y}"] = {"x": x_start, "y": bot_y, "crop": 6}
        else:
            tiles[f"{x_start}-{bot_y}"] = {"x": x_start, "y": bot_y, "crop": 4}
            for x in range(x_start + 1, x_end):
                tiles[f"{x}-{bot_y}"] = {"x": x, "y": bot_y, "crop": 6}
            tiles[f"{x_end}-{bot_y}"] = {"x": x_end, "y": bot_y, "crop": 5}


def place_platform(x_start, x_end, top_y):
    width = x_end - x_start + 1
    if width < 1:
        return

    # Top row: platform edge_top_left ... face_up ... edge_top_right
    if width == 1:
        tiles[f"{x_start}-{top_y}"] = {"x": x_start, "y": top_y, "crop": 12}
    else:
        tiles[f"{x_start}-{top_y}"] = {"x": x_start, "y": top_y, "crop": 10}
        for x in range(x_start + 1, x_end):
            tiles[f"{x}-{top_y}"] = {"x": x, "y": top_y, "crop": 12}
        tiles[f"{x_end}-{top_y}"] = {"x": x_end, "y": top_y, "crop": 11}

    # Bottom row: platform edge_bot_left ... face_down ... edge_bot_right
    bot_y = top_y + 1
    if width == 1:
        tiles[f"{x_start}-{bot_y}"] = {"x": x_start, "y": bot_y, "crop": 15}
    else:
        tiles[f"{x_start}-{bot_y}"] = {"x": x_start, "y": bot_y, "crop": 13}
        for x in range(x_start + 1, x_end):
            tiles[f"{x}-{bot_y}"] = {"x": x, "y": bot_y, "crop": 15}
        tiles[f"{x_end}-{bot_y}"] = {"x": x_end, "y": bot_y, "crop": 14}


# GROUND (3 rows: top edge, middle, bottom edge)
place_ground(0, LEVEL_W - 1, GROUND_Y, depth=3)

# FLOATING PLATFORMS (4 tiles wide, matching World 1-1 size)
# First row platforms at y=29
platforms_y29 = [
    (8, 11),
    (20, 23),
    (32, 35),
    (45, 48),
]
for x_start, x_end in platforms_y29:
    place_platform(x_start, x_end, 29)

# Second row platforms at y=25
platforms_y25 = [
    (14, 17),
    (37, 40),
]
for x_start, x_end in platforms_y25:
    place_platform(x_start, x_end, 25)

# BULLET BILL CANNONS (far edges, visible but separate from main fight)
bullet_bill_platforms = [
    (1, 2),     # far left
    (54, 55),   # far right
]
for x_start, x_end in bullet_bill_platforms:
    place_platform(x_start, x_end, 26)

# FACTORY PIPES (single tile, on ground)
pipe_positions = [15, 30, 42]
for pipe_x in pipe_positions:
    py_top = GROUND_Y - 2
    py_mid = GROUND_Y - 1
    tiles[f"{pipe_x}-{py_top}"] = {"x": pipe_x, "y": py_top, "crop": 19}
    tiles[f"{pipe_x}-{py_mid}"] = {"x": pipe_x, "y": py_mid, "crop": 20}

# SAVE
os.makedirs("assets/levels", exist_ok=True)

data = {
    "projectId": "factory",
    "projectName": "Mario_Multiplayer",
    "tilesetEditing": [{
        "layers": [{
            "layerId": 5,
            "name": "Layer 5",
            "tiles": tiles
        }]
    }]
}

with open("assets/levels/factory.json", "w") as f:
    json.dump(data, f, separators=(",", ":"))

print(f"Factory level: {len(tiles)} tiles")
print(f"Pipe spawner positions: {pipe_positions}")
