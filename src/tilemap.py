import pygame
import json
from constants import TILE_SIZE, SCALE, MAP_SCALE

SOLID_WALLS   = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}
PLATFORM_TIDS = set()
SKIP_TIDS     = set()
PLATFORM_HEIGHT = 8

class Tilemap:
    def __init__(self, json_path: str, tileset: pygame.Surface):
        self.tileset  = tileset
        self.tile_px  = TILE_SIZE * SCALE * MAP_SCALE
        self.tiles    = []
        self.level_w  = 0
        self.level_h  = 0
        self._load(json_path)

    def _load(self, path):
        with open(path) as f:
            data = json.load(f)

        if isinstance(data, list):
            for row_idx, row in enumerate(data):
                for col_idx, val in enumerate(row):
                    tid = int(val)
                    if tid <= 0 or tid in SKIP_TIDS:
                        continue
                    rect = pygame.Rect(
                        col_idx * self.tile_px,
                        row_idx * self.tile_px,
                        self.tile_px,
                        self.tile_px,
                    )
                    self.tiles.append((rect, tid))
                    self.level_w = max(self.level_w, (col_idx + 1) * self.tile_px)
                    self.level_h = max(self.level_h, (row_idx + 1) * self.tile_px)

        elif isinstance(data, dict):
            if "tilesetEditing" in data:
                te = data["tilesetEditing"][0]["layers"]
                layer5 = None
                for layer in te:
                    if layer.get("layerId") == 5 or layer.get("name") == "Layer 5":
                        layer5 = layer
                        break
                if layer5 and "tiles" in layer5:
                    tiles = layer5["tiles"]
                    for key, val in tiles.items():
                        x = val["x"]
                        y = val["y"]
                        tid = val.get("crop", 0)
                        if tid <= 0 or tid in SKIP_TIDS:
                            continue
                        rect = pygame.Rect(
                            x * self.tile_px,
                            y * self.tile_px,
                            self.tile_px,
                            self.tile_px,
                        )
                        self.tiles.append((rect, tid))
                        self.level_w = max(self.level_w, (x + 1) * self.tile_px)
                        self.level_h = max(self.level_h, (y + 1) * self.tile_px)
            else:
                tilemap_data = data.get("tiles") or data.get("data") or data.get("layers")
                if tilemap_data:
                    for row_idx, row in enumerate(tilemap_data):
                        for col_idx, val in enumerate(row):
                            tid = int(val)
                            if tid <= 0 or tid in SKIP_TIDS:
                                continue
                            rect = pygame.Rect(
                                col_idx * self.tile_px,
                                row_idx * self.tile_px,
                                self.tile_px,
                                self.tile_px,
                            )
                            self.tiles.append((rect, tid))
                            self.level_w = max(self.level_w, (col_idx + 1) * self.tile_px)
                            self.level_h = max(self.level_h, (row_idx + 1) * self.tile_px)

    def solid_rects(self) -> list[pygame.Rect]:
        return [r for r, tid in self.tiles if tid in SOLID_WALLS]

    def platform_rects(self) -> list[pygame.Rect]:
        return [pygame.Rect(r.x, r.y, r.w, PLATFORM_HEIGHT) for r, tid in self.tiles if tid in PLATFORM_TIDS]

    def draw(self, surface, camera_offset, tileset_surface):
        screen_rect = pygame.Rect(camera_offset, surface.get_size())
        tp = self.tile_px
        cols_per_row = tileset_surface.get_width() // TILE_SIZE

        for rect, tid in self.tiles:
            if not screen_rect.colliderect(rect):
                continue
            src_col = tid % cols_per_row
            src_row = tid // cols_per_row
            src = pygame.Rect(src_col * TILE_SIZE, src_row * TILE_SIZE,
                              TILE_SIZE, TILE_SIZE)
            tile_surf = pygame.transform.scale(
                tileset_surface.subsurface(src), (tp, tp))
            
            # FIX: For platform tiles, only draw the top portion
            # This removes the visual "bottom line" of the platform
            if tid in PLATFORM_TIDS:
                draw_h = PLATFORM_HEIGHT
                tile_surf = tile_surf.subsurface(pygame.Rect(0, 0, tp, draw_h))
                surface.blit(tile_surf,
                             (rect.x - camera_offset[0], rect.y - camera_offset[1]))
            else:
                surface.blit(tile_surf,
                             (rect.x - camera_offset[0], rect.y - camera_offset[1]))
