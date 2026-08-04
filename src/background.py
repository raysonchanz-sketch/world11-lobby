import pygame
import os
import random


class Background:
    def __init__(self, tile_dir="tileset/world 1-1", scale=2):
        self.elements = []
        self._load(tile_dir, scale)

    def _load(self, tile_dir, scale):
        bg_files = {
            "hill": ("hill(bg).png", scale * 3),
            "bush": ("bush(bg).png", scale * 2),
            "cloud": ("cloud(bg).png", scale * 2),
        }
        for kind, (fname, s) in bg_files.items():
            path = os.path.join(tile_dir, fname)
            if not os.path.exists(path):
                continue
            img = pygame.image.load(path).convert_alpha()
            w = max(1, int(img.get_width() * s))
            h = max(1, int(img.get_height() * s))
            self.elements.append((kind, pygame.transform.smoothscale(img, (w, h))))

    def generate_positions(self, level_w, ground_top_y, tile_px):
        positions = []
        for kind, img in self.elements:
            w, h = img.get_size()
            if kind == "hill":
                positions.append((img, 60, ground_top_y - h))
                positions.append((img, level_w - 60 - w, ground_top_y - h))
            elif kind == "bush":
                positions.append((img, 200, ground_top_y - h // 2))
                positions.append((img, level_w - 200 - w, ground_top_y - h // 2))
            elif kind == "cloud":
                positions.append((img, 150, ground_top_y - h - tile_px * 14))
                positions.append((img, level_w - 200 - w, ground_top_y - h - tile_px * 16))
                positions.append((img, level_w // 2 - w // 2, ground_top_y - h - tile_px * 12))
        return positions

    def draw(self, surface, camera_offset, level_w, ground_top_y, tile_px):
        for img, wx, wy in self.generate_positions(level_w, ground_top_y, tile_px):
            sx = int(wx - camera_offset[0])
            sy = int(wy - camera_offset[1])
            surface.blit(img, (sx, sy))


class FactoryBackground:
    def __init__(self, level_w, ground_top_y, tile_px):
        self.elements = []
        self._generate(level_w, ground_top_y, tile_px)

    def _generate(self, level_w, ground_top_y, tile_px):
        rng = random.Random(42)

        for i in range(8):
            x = rng.randint(0, level_w)
            y = rng.randint(ground_top_y - tile_px * 20, ground_top_y - tile_px * 5)
            w = rng.randint(30, 80)
            h = rng.randint(100, 250)
            self.elements.append(("pipe", x, y, w, h))

        for i in range(12):
            x = rng.randint(0, level_w)
            y = rng.randint(ground_top_y - tile_px * 22, ground_top_y - tile_px * 8)
            w = rng.randint(40, 100)
            h = rng.randint(20, 50)
            self.elements.append(("vent", x, y, w, h))

        for i in range(6):
            x = rng.randint(0, level_w)
            y = rng.randint(ground_top_y - tile_px * 18, ground_top_y - tile_px * 6)
            r = rng.randint(20, 50)
            self.elements.append(("gear", x, y, r))

        for i in range(5):
            x = rng.randint(0, level_w)
            y = ground_top_y - tile_px * rng.randint(2, 6)
            w = rng.randint(60, 150)
            h = rng.randint(30, 60)
            self.elements.append(("panel", x, y, w, h))

        for i in range(4):
            x = rng.randint(0, level_w)
            y = rng.randint(ground_top_y - tile_px * 20, ground_top_y - tile_px * 10)
            self.elements.append(("light", x, y))

    def draw(self, surface, camera_offset):
        for elem in self.elements:
            kind = elem[0]
            sx = int(elem[1] - camera_offset[0])
            sy = int(elem[2] - camera_offset[1])

            if kind == "pipe":
                w, h = elem[3], elem[4]
                pygame.draw.rect(surface, (50, 55, 65), (sx, sy, w, h))
                pygame.draw.rect(surface, (65, 70, 80), (sx + 2, sy, w - 4, h))
                pygame.draw.rect(surface, (40, 45, 55), (sx + w // 2 - 3, sy - 8, 6, 12))

            elif kind == "vent":
                w, h = elem[3], elem[4]
                pygame.draw.rect(surface, (55, 60, 70), (sx, sy, w, h))
                for j in range(3):
                    vy = sy + 5 + j * (h - 10) // 3
                    pygame.draw.line(surface, (35, 40, 50), (sx + 4, vy), (sx + w - 4, vy), 2)

            elif kind == "gear":
                r = elem[3]
                pygame.draw.circle(surface, (60, 65, 75), (sx, sy), r)
                pygame.draw.circle(surface, (75, 80, 90), (sx, sy), r - 4)
                pygame.draw.circle(surface, (45, 50, 60), (sx, sy), r // 3)
                for a in range(0, 360, 45):
                    import math
                    gx = sx + int(r * 0.7 * math.cos(math.radians(a)))
                    gy = sy + int(r * 0.7 * math.sin(math.radians(a)))
                    pygame.draw.circle(surface, (55, 60, 70), (gx, gy), 4)

            elif kind == "panel":
                w, h = elem[3], elem[4]
                pygame.draw.rect(surface, (45, 50, 60), (sx, sy, w, h))
                pygame.draw.rect(surface, (55, 60, 70), (sx + 2, sy + 2, w - 4, h - 4), 1)
                for px in range(sx + 10, sx + w - 5, 20):
                    pygame.draw.circle(surface, (70, 75, 85), (px, sy + h // 2), 3)

            elif kind == "light":
                pygame.draw.circle(surface, (200, 180, 60), (sx, sy), 6)
                glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (200, 180, 60, 30), (15, 15), 15)
                surface.blit(glow_surf, (sx - 15, sy - 15))
