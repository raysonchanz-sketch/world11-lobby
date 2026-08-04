import pygame


class Fireball:
    """Mario's fireball projectile. Travels straight, bounces off walls."""
    SPEED = 8.0
    GRAVITY = 0.25
    DAMAGE = 5
    BASE_KB = 8
    KB_GROWTH = 0.8
    LIFETIME = 180

    def __init__(self, x, y, facing, owner):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.owner = owner
        self.vx = self.SPEED * facing
        self.vy = -2.0
        self.active = True
        self.timer = self.LIFETIME
        self.bounce_count = 0
        self.max_bounces = 3
        self.damage = self.DAMAGE
        self.base_kb = self.BASE_KB
        self.kb_growth = self.KB_GROWTH

        size = 14
        self.rect = pygame.Rect(int(x) - size // 2, int(y) - size // 2, size, size)
        self.anim_timer = 0
        self.image = None

    def update(self, tiles):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        self.anim_timer += 1
        self.vy += self.GRAVITY
        self.vy = min(self.vy, 8)

        self.pos.x += self.vx
        self.pos.y += self.vy

        size = 14
        self.rect.x = int(self.pos.x) - size // 2
        self.rect.y = int(self.pos.y) - size // 2
        self.rect.width = size
        self.rect.height = size

        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                overlap_left = self.rect.right - rect.left
                overlap_right = rect.right - self.rect.left
                overlap_top = self.rect.bottom - rect.top
                overlap_bottom = rect.bottom - self.rect.top
                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                if min_overlap in (overlap_top, overlap_bottom):
                    self.vy = -abs(self.vy) * 0.7
                    if abs(self.vy) < 1:
                        self.vy = 0
                    self.bounce_count += 1
                else:
                    self.vx = -self.vx * 0.8
                    self.bounce_count += 1
                if self.bounce_count >= self.max_bounces:
                    self.active = False
                    return

        if (self.rect.right < -100 or self.rect.left > 3000 or
            self.rect.top > 1500 or self.rect.bottom < -500):
            self.active = False

    def draw(self, surface, camera_offset):
        if not self.active:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        color = (255, 120, 20)
        glow = (255, 80, 0)
        s = self.rect.width
        phase = (self.anim_timer // 3) % 3
        sz = s + phase
        pygame.draw.circle(surface, glow, (int(draw_x + s // 2), int(draw_y + s // 2)), sz // 2 + 3)
        pygame.draw.circle(surface, color, (int(draw_x + s // 2), int(draw_y + s // 2)), sz // 2)


class Blastshot:
    """Luigi's blastshot projectile. Travels fast, disappears on hit."""
    SPEED = 10.0
    DAMAGE = 6
    BASE_KB = 10
    KB_GROWTH = 0.9
    LIFETIME = 120

    def __init__(self, x, y, facing, owner):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.owner = owner
        self.vx = self.SPEED * facing
        self.vy = 0
        self.active = True
        self.timer = self.LIFETIME
        self.damage = self.DAMAGE
        self.base_kb = self.BASE_KB
        self.kb_growth = self.KB_GROWTH

        size = 12
        self.rect = pygame.Rect(int(x) - size // 2, int(y) - size // 2, size, size)
        self.anim_timer = 0

    def update(self, tiles):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        self.anim_timer += 1
        self.pos.x += self.vx
        self.pos.y += self.vy

        size = 12
        self.rect.x = int(self.pos.x) - size // 2
        self.rect.y = int(self.pos.y) - size // 2
        self.rect.width = size
        self.rect.height = size

        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                self.active = False
                return

        if (self.rect.right < -100 or self.rect.left > 3000 or
            self.rect.top > 1500 or self.rect.bottom < -500):
            self.active = False

    def draw(self, surface, camera_offset):
        if not self.active:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        color = (100, 180, 255)
        glow = (60, 120, 255)
        s = self.rect.width
        phase = (self.anim_timer // 2) % 3
        sz = s + phase
        pygame.draw.circle(surface, glow, (int(draw_x + s // 2), int(draw_y + s // 2)), sz // 2 + 3)
        pygame.draw.circle(surface, color, (int(draw_x + s // 2), int(draw_y + s // 2)), sz // 2)


class Barrel:
    """DK's barrel throw projectile. Rolls along the ground, bounces off walls."""
    SPEED = 6.0
    GRAVITY = 0.4
    DAMAGE = 10
    BASE_KB = 14
    KB_GROWTH = 1.2
    LIFETIME = 300

    def __init__(self, x, y, facing, owner):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.owner = owner
        self.vx = self.SPEED * facing
        self.vy = -3.0
        self.active = True
        self.timer = self.LIFETIME
        self.damage = self.DAMAGE
        self.base_kb = self.BASE_KB
        self.kb_growth = self.KB_GROWTH
        self.grounded = False

        size = 20
        self.rect = pygame.Rect(int(x) - size // 2, int(y) - size // 2, size, size)
        self.anim_timer = 0

    def update(self, tiles):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        self.anim_timer += 1
        self.vy += self.GRAVITY
        self.vy = min(self.vy, 8)

        self.pos.x += self.vx
        self.pos.y += self.vy

        size = 20
        self.rect.x = int(self.pos.x) - size // 2
        self.rect.y = int(self.pos.y) - size // 2
        self.rect.width = size
        self.rect.height = size

        for tile in tiles:
            rect = tile[0] if isinstance(tile, (list, tuple)) else tile
            if self.rect.colliderect(rect):
                overlap_left = self.rect.right - rect.left
                overlap_right = rect.right - self.rect.left
                overlap_top = self.rect.bottom - rect.top
                overlap_bottom = rect.bottom - self.rect.top
                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                if min_overlap in (overlap_top, overlap_bottom):
                    self.vy = 0
                    self.pos.y = rect.top - size // 2 if min_overlap == overlap_top else rect.bottom + size // 2
                    self.grounded = True
                else:
                    self.vx = -self.vx * 0.9
                    self.pos.x = self.rect.x

        if (self.rect.right < -100 or self.rect.left > 3000 or
            self.rect.top > 1500 or self.rect.bottom < -500):
            self.active = False

    def draw(self, surface, camera_offset):
        if not self.active:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        s = self.rect.width
        brown = (139, 90, 43)
        dark_brown = (100, 60, 25)
        band = (60, 40, 20)
        cx = int(draw_x + s // 2)
        cy = int(draw_y + s // 2)
        rot = (self.anim_timer * 8 * self.facing) % 360
        pygame.draw.rect(surface, dark_brown, (cx - s // 2, cy - s // 2, s, s), border_radius=3)
        pygame.draw.rect(surface, brown, (cx - s // 2 + 2, cy - s // 2 + 2, s - 4, s - 4), border_radius=2)
        band_y = cy - 2 + int(2 * (rot % 6 - 3) / 3)
        pygame.draw.rect(surface, band, (cx - s // 2, band_y, s, 4))
