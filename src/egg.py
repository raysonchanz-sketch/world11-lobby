import pygame
import math

class EggProjectile:
    """Yoshi's egg throw projectile. Bounces off walls, deals damage on contact."""

    def __init__(self, x, y, facing, owner, sprites, scale=1):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.owner = owner
        self.vx = 9.0 * facing  # EGG_SPEED
        self.vy = -4.0          # Slight upward arc
        self.gravity = 0.3      # EGG_GRAVITY
        self.damage = 8
        self.base_kb = 12
        self.kb_growth = 1.0
        self.kb_bonus = 1.0
        self.active = True
        self.timer = 300        # 5 second lifetime
        self.bounce_count = 0
        self.max_bounces = 3

        # Sprite for animation
        self.sprites = sprites
        self.anim_frame = 0
        self.anim_timer = 0
        self.image = None
        self._update_image()

        # Hitbox
        size = 20 * scale
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        self.scale = scale

    def _update_image(self):
        if self.sprites:
            labels = ["Yoshi - Egg Spin 1", "Yoshi - Egg Spin 2",
                      "Yoshi - Egg Spin 3", "Yoshi - Egg Spin 4"]
            idx = self.anim_frame % len(labels)
            self.image = self.sprites.get(labels[idx])

    def update(self, tiles):
        if not self.active:
            return

        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        # Animate
        self.anim_timer += 1
        if self.anim_timer >= 6:
            self.anim_timer = 0
            self.anim_frame += 1
            self._update_image()

        # Apply gravity
        self.vy += self.gravity
        self.vy = min(self.vy, 10)

        # Move
        self.pos.x += self.vx
        self.pos.y += self.vy

        # Update rect
        size = 20 * self.scale
        self.rect.x = int(self.pos.x) - size // 2
        self.rect.y = int(self.pos.y) - size // 2
        self.rect.width = size
        self.rect.height = size

        # Tile collisions
        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                # Determine collision side
                overlap_left = self.rect.right - rect.left
                overlap_right = rect.right - self.rect.left
                overlap_top = self.rect.bottom - rect.top
                overlap_bottom = rect.bottom - self.rect.top

                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                if min_overlap == overlap_top or min_overlap == overlap_bottom:
                    # Vertical bounce
                    self.vy = -abs(self.vy) * 0.6
                    if abs(self.vy) < 1:
                        self.vy = 0
                    self.bounce_count += 1
                else:
                    # Horizontal bounce or break
                    self.vx = -self.vx * 0.8
                    self.bounce_count += 1

                if self.bounce_count >= self.max_bounces:
                    self.active = False
                    return

        # Off-screen check
        if (self.rect.right < -100 or self.rect.left > 2000 or
            self.rect.top > 1500 or self.rect.bottom < -500):
            self.active = False

    def draw(self, surface, camera_offset):
        if not self.active or not self.image:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        surface.blit(self.image, (draw_x, draw_y))
