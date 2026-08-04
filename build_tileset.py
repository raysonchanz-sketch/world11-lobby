"""Build a new tileset.png from the individual World 1-1 tiles.

Layout (32x32 grid):
  Tile 0: empty (transparent)
  Tile 1: ground_block
  Tile 2: platform_brick
  Tile 3: steel_block
  Tile 4: pipe
"""
import pygame
import os

TILE_PX = 32
TILES_PER_ROW = 5
ROWS = 1
OUT = "assets/tiles/tileset.png"
SRC_DIR = "tileset/world 1-1"

TILE_MAP = [
    "ground_block.png",
    "platform_brick.png",
    "steel_block(use once in every platform).png",
    "pipe.png",
]

def build():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    screen = pygame.display.set_mode((1, 1))
    surf = pygame.Surface((TILES_PER_ROW * TILE_PX, ROWS * TILE_PX), pygame.SRCALPHA)

    for i, fname in enumerate(TILE_MAP):
        path = os.path.join(SRC_DIR, fname)
        img = pygame.image.load(path).convert_alpha()
        scaled = pygame.transform.smoothscale(img, (TILE_PX, TILE_PX))
        col = i + 1
        row = 0
        surf.blit(scaled, (col * TILE_PX, row * TILE_PX))
        print(f"  Tile {i+1}: {fname} -> col {col}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(surf, OUT)
    print(f"\nSaved {OUT} ({surf.get_width()}x{surf.get_height()})")

    # Quick summary
    print("\nTile ID mapping:")
    for i, fname in enumerate(TILE_MAP):
        solid = "SOLID" if i + 1 in (1, 2, 3, 4) else ""
        print(f"  ID {i+1}: {fname} [{solid}]")

if __name__ == "__main__":
    build()
