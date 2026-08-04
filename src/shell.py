import pygame
from constants import *

# Fixed display size for the shell regardless of source image dimensions
SHELL_DISPLAY_W = 32 * SCALE
SHELL_DISPLAY_H = 28 * SCALE


def _make_fallback_shell() -> pygame.Surface:
    """Create a clearly visible green shell when the sprite file is missing/broken."""
    surf = pygame.Surface((SHELL_DISPLAY_W, SHELL_DISPLAY_H), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (34, 177, 76),
                        (1, SHELL_DISPLAY_H // 5, SHELL_DISPLAY_W - 2, SHELL_DISPLAY_H * 3 // 5))
    pygame.draw.ellipse(surf, (0, 100, 0),
                        (1, SHELL_DISPLAY_H // 5, SHELL_DISPLAY_W - 2, SHELL_DISPLAY_H * 3 // 5), 2)
    pygame.draw.line(surf, (0, 120, 0),
                     (SHELL_DISPLAY_W // 2, SHELL_DISPLAY_H // 5 + 2),
                     (SHELL_DISPLAY_W // 2, SHELL_DISPLAY_H * 4 // 5 - 2), 2)
    pygame.draw.line(surf, (0, 120, 0),
                     (4, SHELL_DISPLAY_H // 2),
                     (SHELL_DISPLAY_W - 4, SHELL_DISPLAY_H // 2), 2)
    pygame.draw.ellipse(surf, (130, 255, 130),
                        (SHELL_DISPLAY_W // 3, SHELL_DISPLAY_H // 3,
                         SHELL_DISPLAY_W // 4, SHELL_DISPLAY_H // 5))
    return surf


class KoopaShell:
    def __init__(self, x, y, facing, owner, image, scale=SCALE):
        if image is not None:
            # FIX: Use smoothscale instead of scale for dramatic downscaling.
            # smoothscale uses bilinear filtering which properly blends pixels
            # with their alpha values, producing clean edges and preserving colors.
            # Regular scale uses nearest-neighbor which creates jagged edges
            # and loses small details when downscaling a lot.
            self.image = pygame.transform.smoothscale(image, (SHELL_DISPLAY_W, SHELL_DISPLAY_H))
        else:
            print("[DEBUG] Shell sprite missing — using programmatic fallback")
            self.image = _make_fallback_shell()

        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(float(self.rect.x), float(self.rect.y))
        self.vel = pygame.math.Vector2(facing * SHELL_SPEED, 0)
        self.facing = facing
        self.owner = owner
        self.active = True
        self.on_ground = False
        self.lifetime = 300
        self.grace_frames = SHELL_GRACE_FRAMES

    def update(self, tiles):
        if not self.active:
            return

        if self.grace_frames > 0:
            self.grace_frames -= 1

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False
            return

        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL)

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        self._collide_x(tiles)

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self._collide_y(tiles)

    def _collide_x(self, tiles):
        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                if self.vel.x > 0:
                    self.rect.right = rect.left
                elif self.vel.x < 0:
                    self.rect.left = rect.right
                self.vel.x *= -1
                self.facing *= -1
                self.pos.x = float(self.rect.x)
                break

    def _collide_y(self, tiles):
        self.on_ground = False
        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                if self.vel.y > 0:
                    self.rect.bottom = rect.top
                    self.on_ground = True
                    self.vel.y = 0
                elif self.vel.y < 0:
                    self.rect.top = rect.bottom
                    self.vel.y = 0
                self.pos.y = float(self.rect.y)
                break

    def draw(self, surface, camera_offset, debug=False):
        if not self.active:
            return

        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]

        if self.facing == -1:
            flipped = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped, (draw_x, draw_y))
        else:
            surface.blit(self.image, (draw_x, draw_y))

        if debug:
            pygame.draw.rect(surface, (255, 255, 0),
                             (draw_x, draw_y, self.rect.width, self.rect.height), 2)
