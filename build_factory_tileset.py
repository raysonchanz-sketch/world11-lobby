"""Build factory tileset.png from individual tile sprites.

Tile layout (32x32 grid, 1-based IDs):
  0: empty
  Ground tiles (16x16 -> 32x32):
    1: ground_edge(top left)
    2: ground_edge(top right)
    3: ground_normal(face up)
    4: ground_edge(bottom left)
    5: ground_edge(bottom right)
    6: ground_normal(face down)
    7: ground_middle(far left)
    8: ground_middle(far right)
    9: ground_middle(normal)
  Platform tiles (16x16 -> 32x32):
    10: platform_edge(top left)
    11: platform_edge(top right)
    12: normal_platform(face_up)
    13: platform_edge(bottom left)
    14: platform_edge(bottom right)
    15: normal_platform(face_down)
  Full-size tiles (32x32):
    16: conveyor
    17: factory_pipe
    18: metal_block
  Pipe tiles (32x32):
    19: pipe_vertical_top
    20: pipe_vertical_middle
    21: pipe_vertical_bottom
    22: pipe_horizontal_left
    23: pipe_horizontal_middle
    24: pipe_horizontal_right
"""
import pygame
import os

TILE_PX = 32
TILES_PER_ROW = 25
OUT = "assets/tiles/factory_tileset.png"
SRC_DIR = os.path.join("tileset", "factory")

TILE_MAP = [
    # Ground (16x16)
    ("factory_tile_ground_edge(top left).png", True),
    ("factory_tile_ground_edge(top right).png", True),
    ("factory_tile_ground_normal(face up).png", True),
    ("factory_tile_ground_edge(bottom left).png", True),
    ("factory_tile_ground_edge(bottom right).png", True),
    ("factory_tile_ground_normal(face down).png", True),
    ("factory_tile_ground_middle(far left).png", True),
    ("factory_tile_ground_middle(far right).png", True),
    ("factory_tile_ground_middle(normal).png", True),
    # Platform (16x16)
    ("factory_tile_platform_edge(top left).png", True),
    ("factory_tile_platform_edge(top right).png", True),
    ("factory_tile_normal_platform(face_up.png", True),
    ("factory_tile_platform_edge(bottom left).png", True),
    ("factory_tile_platform_edge(bottom right).png", True),
    ("factory_tile_normal_platform(face_down).png", True),
    # Full-size (32x32)
    ("conveyor.png", True),
    ("factory_pipe.png", True),
    ("metal_block.png", True),
    # Pipes (32x32)
    ("pipe_vertical_top.png", True),
    ("pipe_vertical_middle.png", True),
    ("pipe_vertical_bottom.png", True),
    ("pipe_horizontal_left.png", True),
    ("pipe_horizontal_middle.png", True),
    ("pipe_horizontal_right.png", True),
]


def build():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    screen = pygame.display.set_mode((1, 1))
    surf = pygame.Surface((TILES_PER_ROW * TILE_PX, TILE_PX), pygame.SRCALPHA)

    for i, (fname, solid) in enumerate(TILE_MAP):
        path = os.path.join(SRC_DIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname}")
            continue
        img = pygame.image.load(path).convert_alpha()
        orig_w, orig_h = img.get_size()
        if orig_w != TILE_PX or orig_h != TILE_PX:
            scaled = pygame.transform.smoothscale(img, (TILE_PX, TILE_PX))
        else:
            scaled = img
        col = i + 1
        surf.blit(scaled, (col * TILE_PX, 0))
        print(f"  Tile {i+1}: {fname} ({orig_w}x{orig_h}) -> col {col}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(surf, OUT)
    print(f"\nSaved {OUT} ({surf.get_width()}x{surf.get_height()})")

    print("\nTile ID mapping:")
    for i, (fname, solid) in enumerate(TILE_MAP):
        tag = "SOLID" if solid else ""
        print(f"  ID {i+1}: {fname} [{tag}]")


if __name__ == "__main__":
    build()
