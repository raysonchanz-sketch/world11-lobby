import pygame
import os
import math
import random
from constants import TILE_SIZE, SCALE, MAP_SCALE


def load_goomba_sprites():
    base = os.path.join("Npc's", "world 1-1 enemies")
    frames = {}
    for name in ("walk1", "walk2", "stomped"):
        key = name
        if name == "walk1":
            fname = "goomba_walk(1).png"
        elif name == "walk2":
            fname = "goomba_walk(2).png"
        else:
            fname = "goomba_stomped.png"
        img = pygame.image.load(os.path.join(base, fname)).convert_alpha()
        frames[key] = img
    return frames


def load_koopa_sprites():
    base = os.path.join("Npc's", "world 1-1 enemies")
    frames = {}
    for name, fname in [
        ("walk1", "koopa_walk_left(1).png"),
        ("walk2", "koopa_walk_left(2).png"),
        ("hit", "koopa_hit.png"),
        ("shell", "koopa_shell.png"),
    ]:
        img = pygame.image.load(os.path.join(base, fname)).convert_alpha()
        frames[name] = img
    return frames


GOOMBA_SPEED = 0.5
GOOMBA_STOMP_DURATION = 30
GOOMBA_SCALE = 1.5

KOOPA_WALK_SPEED = 0.5
KOOPA_SHELL_SPEED = 3.0
KOOPA_WAKEUP_TIME = 300
KOOPA_SCALE = 1.5


class Goomba:
    def __init__(self, x, y, sprites, facing=-1):
        self.sprites = sprites
        self.facing = facing
        self.walk_timer = 0
        self.stomp_timer = 0
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.pos_x = float(x)

        walk1 = sprites["walk1"]
        w = max(1, int(walk1.get_width() * GOOMBA_SCALE))
        h = max(1, int(walk1.get_height() * GOOMBA_SCALE))
        self.image = pygame.transform.smoothscale(walk1, (w, h))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos_x = float(self.rect.x)

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return

        if self.stomp_timer > 0:
            self.stomp_timer -= 1
            if self.stomp_timer <= 0:
                self.alive = False
            return

        self.walk_timer += 1
        frame_key = "walk1" if (self.walk_timer // 8) % 2 == 0 else "walk2"
        img = self.sprites[frame_key]
        w = max(1, int(img.get_width() * GOOMBA_SCALE))
        h = max(1, int(img.get_height() * GOOMBA_SCALE))
        center = self.rect.center
        self.image = pygame.transform.smoothscale(img, (w, h))
        self.rect = self.image.get_rect(center=center)

        self.vy += 0.5
        if self.vy > 10:
            self.vy = 10
        self.pos_x += self.facing * GOOMBA_SPEED
        self.rect.x = round(self.pos_x)

        self.on_ground = False
        self.rect.y += round(self.vy)
        for r in solid:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.rect.bottom = r.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = r.bottom
                    self.vy = 0

        if self.rect.left <= 0 or self.rect.right >= 1824:
            self.facing *= -1

    def stomp(self):
        self.stomp_timer = GOOMBA_STOMP_DURATION
        img = self.sprites["stomped"]
        w = max(1, int(img.get_width() * GOOMBA_SCALE))
        h = max(1, int(img.get_height() * GOOMBA_SCALE))
        center = self.rect.center
        self.image = pygame.transform.smoothscale(img, (w, h))
        self.rect = self.image.get_rect(midbottom=center)

    def draw(self, surface, offset):
        if not self.alive:
            return
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


class Koopa:
    def __init__(self, x, y, sprites, facing=-1):
        self.sprites = sprites
        self.facing = facing
        self.state = "walk"
        self.walk_timer = 0
        self.shell_timer = 0
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.vx = 0.0
        self.pos_x = float(x)

        self._update_image()

        walk1 = sprites["walk1"]
        w = max(1, int(walk1.get_width() * KOOPA_SCALE))
        h = max(1, int(walk1.get_height() * KOOPA_SCALE))
        self.image = pygame.transform.smoothscale(walk1, (w, h))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos_x = float(self.rect.x)

    def _update_image(self):
        if self.state == "walk":
            frame_key = "walk1" if (self.walk_timer // 8) % 2 == 0 else "walk2"
            img = self.sprites[frame_key]
        elif self.state == "shell":
            img = self.sprites["hit"]
        else:
            img = self.sprites["shell"]

        w = max(1, int(img.get_width() * KOOPA_SCALE))
        h = max(1, int(img.get_height() * KOOPA_SCALE))
        return pygame.transform.smoothscale(img, (w, h))

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return

        if self.state == "walk":
            self.walk_timer += 1
            self.vx = self.facing * KOOPA_WALK_SPEED
        elif self.state == "shell":
            self.vx = 0
            self.shell_timer += 1
            if self.shell_timer >= KOOPA_WAKEUP_TIME:
                self.state = "walk"
                self.shell_timer = 0
                self.walk_timer = 0
                self.facing = -1
        elif self.state == "kicked":
            pass

        new_image = self._update_image()
        center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect(center=center)

        self.vy += 0.5
        if self.vy > 10:
            self.vy = 10

        self.pos_x += self.vx
        self.rect.x = round(self.pos_x)

        if level_w and (self.rect.left <= 0 or self.rect.right >= level_w):
            if self.state == "kicked":
                self.alive = False
                return
            else:
                self.facing *= -1
                self.rect.x = max(0, min(level_w - self.rect.w, self.rect.x))

        self.on_ground = False
        self.rect.y += round(self.vy)
        for r in solid:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.rect.bottom = r.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = r.bottom
                    self.vy = 0

        for r in solid:
            if self.rect.colliderect(r):
                if self.vx > 0:
                    self.rect.right = r.left
                elif self.vx < 0:
                    self.rect.left = r.right
                if self.state == "kicked":
                    self.alive = False
                    return

        self.pos_x = float(self.rect.x)

    def stomp(self, from_left=True):
        if self.state == "walk":
            self.state = "kicked"
            self.shell_timer = 0
            self.vx = KOOPA_SHELL_SPEED if from_left else -KOOPA_SHELL_SPEED
            self.facing = 1 if self.vx > 0 else -1
            old_bottom = self.rect.bottom
            new_image = self._update_image()
            self.image = new_image
            self.rect = self.image.get_rect(midbottom=(self.rect.centerx, old_bottom))
            self.pos_x = float(self.rect.x)

    def kick(self, from_left):
        self.state = "kicked"
        self.vx = KOOPA_SHELL_SPEED if from_left else -KOOPA_SHELL_SPEED
        self.facing = 1 if self.vx > 0 else -1

    def check_kill_enemy(self, other):
        if self.state == "kicked" and self.alive and other.alive:
            if self.rect.colliderect(other.rect):
                other.alive = False
                return True
        return False

    def draw(self, surface, offset):
        if not self.alive:
            return
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


SHYGUY_SCALE = 1.8
SHYGUY_SPEED = 0.7
SHYGUY_STOMP_DURATION = 30


def load_shyguy_sprites():
    shy_dir = os.path.join("Npc's", "shy_guy")
    frames = {}
    if os.path.exists(shy_dir):
        mapping = {"walk1": "shy_guy_walk(1).png", "walk2": "shy_guy_walk(2).png", "stomped": "shy_guy_stomped.png"}
        for key, fname in mapping.items():
            path = os.path.join(shy_dir, fname)
            if os.path.exists(path):
                frames[key] = pygame.image.load(path).convert_alpha()
    if not frames:
        for key in ("walk1", "walk2", "stomped"):
            surf = pygame.Surface((12, 16), pygame.SRCALPHA)
            if key == "stomped":
                pygame.draw.ellipse(surf, (220, 40, 40), (0, 6, 12, 10))
                pygame.draw.rect(surf, (240, 240, 240), (3, 4, 6, 5))
            else:
                pygame.draw.rect(surf, (220, 40, 40), (1, 0, 10, 14))
                pygame.draw.rect(surf, (200, 30, 30), (1, 12, 10, 4))
                pygame.draw.rect(surf, (240, 240, 240), (2, 2, 8, 6))
                pygame.draw.rect(surf, (40, 40, 40), (3, 3, 2, 3))
                pygame.draw.rect(surf, (40, 40, 40), (7, 3, 2, 3))
                if key == "walk2":
                    pygame.draw.rect(surf, (200, 30, 30), (0, 13, 5, 3))
                    pygame.draw.rect(surf, (200, 30, 30), (7, 13, 5, 3))
            frames[key] = surf
    return frames


class ShyGuy:
    def __init__(self, x, y, sprites, facing=-1):
        self.sprites = sprites
        self.facing = facing
        self.walk_timer = 0
        self.stomp_timer = 0
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.pos_x = float(x)

        img = sprites["walk1"]
        w = max(1, int(img.get_width() * SHYGUY_SCALE))
        h = max(1, int(img.get_height() * SHYGUY_SCALE))
        self.image = pygame.transform.smoothscale(img, (w, h))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos_x = float(self.rect.x)

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return
        if self.stomp_timer > 0:
            self.stomp_timer -= 1
            if self.stomp_timer <= 0:
                self.alive = False
            return

        self.walk_timer += 1
        frame_key = "walk1" if (self.walk_timer // 8) % 2 == 0 else "walk2"
        img = self.sprites[frame_key]
        w = max(1, int(img.get_width() * SHYGUY_SCALE))
        h = max(1, int(img.get_height() * SHYGUY_SCALE))
        center = self.rect.center
        self.image = pygame.transform.smoothscale(img, (w, h))
        self.rect = self.image.get_rect(center=center)

        self.vy += 0.5
        if self.vy > 10:
            self.vy = 10
        self.pos_x += self.facing * SHYGUY_SPEED
        self.rect.x = round(self.pos_x)

        self.on_ground = False
        self.rect.y += round(self.vy)
        for r in solid:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.rect.bottom = r.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = r.bottom
                    self.vy = 0

        if level_w and (self.rect.left <= 0 or self.rect.right >= level_w):
            self.facing *= -1
            self.pos_x = float(self.rect.x)

    def stomp(self):
        self.stomp_timer = SHYGUY_STOMP_DURATION
        img = self.sprites["stomped"]
        w = max(1, int(img.get_width() * SHYGUY_SCALE))
        h = max(1, int(img.get_height() * SHYGUY_SCALE))
        center = self.rect.center
        self.image = pygame.transform.smoothscale(img, (w, h))
        self.rect = self.image.get_rect(midbottom=center)

    def draw(self, surface, offset):
        if not self.alive:
            return
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


BUZZY_SCALE = 1.5
BUZZY_WALK_SPEED = 0.5
BUZZY_SHELL_SPEED = 3.0
BUZZY_STOMP_DURATION = 30


def load_buzzy_beetle_sprites():
    base = os.path.join("Npc's", "Factory enemies", "buzzy_beetle")
    frames = {}
    mapping = {
        "walk1": "buzzy_bettle_walk_right(1).PNG",
        "walk2": "buzzy_bettle_walk_right(2).PNG",
        "shell": "buzzy_beetle_shell.png",
    }
    for key, fname in mapping.items():
        path = os.path.join(base, fname)
        if os.path.exists(path):
            frames[key] = pygame.image.load(path).convert_alpha()
    for i in range(1, 9):
        path = os.path.join(base, f"buzzy_beetle_shell_spin({i}).png")
        if os.path.exists(path):
            frames[f"spin{i}"] = pygame.image.load(path).convert_alpha()
    return frames


class BuzzyBeetle:
    def __init__(self, x, y, sprites, facing=-1):
        self.sprites = sprites
        self.facing = facing
        self.state = "walk"
        self.walk_timer = 0
        self.spin_timer = 0
        self.stomp_timer = 0
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.vx = 0.0
        self.pos_x = float(x)
        self.wall_bounces = 0

        walk1 = sprites["walk1"]
        w = max(1, int(walk1.get_width() * BUZZY_SCALE))
        h = max(1, int(walk1.get_height() * BUZZY_SCALE))
        self.image = pygame.transform.smoothscale(walk1, (w, h))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos_x = float(self.rect.x)

    def _update_image(self):
        if self.state == "walk":
            frame_key = "walk1" if (self.walk_timer // 8) % 2 == 0 else "walk2"
            img = self.sprites[frame_key]
        elif self.state == "shell":
            img = self.sprites["shell"]
        else:
            idx = (self.spin_timer // 4) % 8 + 1
            img = self.sprites.get(f"spin{idx}", self.sprites["shell"])
        w = max(1, int(img.get_width() * BUZZY_SCALE))
        h = max(1, int(img.get_height() * BUZZY_SCALE))
        return pygame.transform.smoothscale(img, (w, h))

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return
        if self.stomp_timer > 0:
            self.stomp_timer -= 1
            if self.stomp_timer <= 0:
                self.alive = False
            return

        if self.state == "walk":
            self.walk_timer += 1
            self.vx = self.facing * BUZZY_WALK_SPEED
        elif self.state == "spin":
            self.spin_timer += 1
            self.vx = self.facing * BUZZY_SHELL_SPEED

        new_image = self._update_image()
        center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect(center=center)

        self.vy += 0.5
        if self.vy > 10:
            self.vy = 10
        self.pos_x += self.vx
        self.rect.x = round(self.pos_x)

        if level_w and (self.rect.left <= 0 or self.rect.right >= level_w):
            self.facing *= -1
            self.pos_x = float(self.rect.x)

        self.on_ground = False
        self.rect.y += round(self.vy)
        for r in solid:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.rect.bottom = r.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = r.bottom
                    self.vy = 0

        if self.state == "spin":
            for r in solid:
                if self.rect.colliderect(r):
                    if self.vx > 0:
                        self.rect.right = r.left
                    elif self.vx < 0:
                        self.rect.left = r.right
                    self.facing *= -1
                    self.pos_x = float(self.rect.x)
        elif self.state == "walk":
            for r in solid:
                if self.rect.colliderect(r):
                    if self.vx > 0:
                        self.rect.right = r.left
                    elif self.vx < 0:
                        self.rect.left = r.right
                    self.facing *= -1
                    self.pos_x = float(self.rect.x)

    def stomp(self, from_left=True):
        if self.state == "walk":
            self.state = "spin"
            self.spin_timer = 0
            self.facing = 1 if from_left else -1
            old_bottom = self.rect.bottom
            new_image = self._update_image()
            self.image = new_image
            self.rect = self.image.get_rect(midbottom=(self.rect.centerx, old_bottom))
            self.pos_x = float(self.rect.x)
        elif self.state == "spin":
            self.stomp_timer = BUZZY_STOMP_DURATION

    def kick(self, from_left):
        if self.state == "walk":
            self.state = "spin"
            self.spin_timer = 0
            self.facing = 1 if from_left else -1

    def check_kill_enemy(self, other):
        if self.state == "spin" and self.alive and other.alive:
            if self.rect.colliderect(other.rect):
                other.alive = False
                return True
        return False

    def draw(self, surface, offset):
        if not self.alive:
            return
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == -1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


BULLET_SPEED = 2.0
BULLET_LIFETIME = 300


def load_bullet_bill_sprites():
    base = os.path.join("Npc's", "Factory enemies", "bullet_bill")
    frames = {}
    if os.path.exists(os.path.join(base, "bullet_bill.png")):
        frames["bullet"] = pygame.image.load(os.path.join(base, "bullet_bill.png")).convert_alpha()
    if os.path.exists(os.path.join(base, "bill_blaster.png")):
        frames["blaster"] = pygame.image.load(os.path.join(base, "bill_blaster.png")).convert_alpha()
    return frames


class BillBlaster:
    def __init__(self, x, y, sprites, facing=-1):
        self.facing = facing
        self.sprites = sprites
        self.alive = True
        self.fire_timer = 0
        self.fire_interval = random.randint(240, 600)
        img = sprites.get("blaster")
        if img:
            w = max(1, int(img.get_width() * 1.5))
            h = max(1, int(img.get_height() * 1.5))
            self.image = pygame.transform.smoothscale(img, (w, h))
        else:
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (60, 60, 60), (4, 0, 40, 48))
            pygame.draw.rect(self.image, (80, 80, 80), (8, 4, 32, 40))
            pygame.draw.rect(self.image, (40, 40, 40), (12, 10, 24, 8))
        self.rect = self.image.get_rect(midbottom=(x, y))

    def try_fire(self):
        self.fire_timer += 1
        if self.fire_timer >= self.fire_interval:
            self.fire_timer = 0
            self.fire_interval = random.randint(240, 600)
            spawn_x = self.rect.centerx + self.facing * 40
            spawn_y = self.rect.centery
            return BulletBill(spawn_x, spawn_y, self.sprites, facing=self.facing)
        return None

    def draw(self, surface, offset):
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


class BulletBill:
    def __init__(self, x, y, sprites=None, facing=-1):
        self.facing = facing
        self.sprites = sprites or {}
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.vx = facing * BULLET_SPEED
        self.pos_x = float(x)
        self.lifetime = BULLET_LIFETIME

        img = self.sprites.get("bullet") if self.sprites else None
        if img:
            w = max(1, int(img.get_width() * 1.5))
            h = max(1, int(img.get_height() * 1.5))
            self.image = pygame.transform.smoothscale(img, (w, h))
        else:
            self.image = pygame.Surface((36, 24), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (40, 40, 40), (0, 2, 30, 20))
            pygame.draw.rect(self.image, (60, 60, 60), (28, 6, 8, 12))
            pygame.draw.circle(self.image, (255, 200, 0), (9, 12), 4)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos_x = float(self.rect.x)

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return

        self.pos_x += self.vx
        self.rect.x = round(self.pos_x)

    def draw(self, surface, offset):
        if not self.alive:
            return
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))


CHAIN_CHOMP_SCALE = 1.0
CHAIN_CHOMP_LUNGE_SPEED = 4.0
CHAIN_CHOMP_COOLDOWN = 180
CHAIN_CHOMP_LUNGE_DURATION = 20
CHAIN_CHOMP_PULLBACK_SPEED = 2.0


def load_chain_chomp_sprites():
    base = os.path.join("Npc's", "Factory enemies", "chain_chomp")
    frames = {}
    idle_path = os.path.join(base, "chain_chomp_idle.png")
    if os.path.exists(idle_path):
        frames["idle"] = pygame.image.load(idle_path).convert_alpha()
    for i in range(1, 7):
        path = os.path.join(base, f"chain_chomp_lunge_left({i}).png")
        if os.path.exists(path):
            frames[f"lunge{i}"] = pygame.image.load(path).convert_alpha()
    pullback_path = os.path.join(base, "attack_and_pullback.png")
    if os.path.exists(pullback_path):
        full_pb = pygame.image.load(pullback_path).convert_alpha()
        fw = full_pb.get_width()
        fh = full_pb.get_height()
        n_frames = 6
        frame_w = fw // n_frames
        for i in range(n_frames):
            frame = full_pb.subsurface((i * frame_w, 0, frame_w, fh))
            frames[f"pullback{i+1}"] = frame.copy()
    return frames


def generate_chain_chomp_post():
    surf = pygame.Surface((14, 24), pygame.SRCALPHA)
    pygame.draw.rect(surf, (90, 70, 40), (3, 4, 8, 20))
    pygame.draw.rect(surf, (120, 100, 60), (4, 4, 6, 20))
    pygame.draw.ellipse(surf, (150, 130, 80), (2, 0, 10, 6))
    pygame.draw.rect(surf, (70, 50, 25), (1, 20, 12, 4))
    return surf


class ChainChomp:
    def __init__(self, post_x, post_y, sprites):
        self.sprites = sprites
        self.post_x = float(post_x)
        self.post_y = float(post_y)
        self.state = "idle"
        self.facing = -1
        self.alive = True
        self.on_ground = False
        self.vy = 0.0
        self.vx = 0.0
        self.cooldown = CHAIN_CHOMP_COOLDOWN
        self.lunge_timer = 0
        self.pullback_timer = 0
        self.walk_timer = 0

        idle_img = sprites.get("idle")
        if idle_img:
            w = max(1, int(idle_img.get_width() * CHAIN_CHOMP_SCALE))
            h = max(1, int(idle_img.get_height() * CHAIN_CHOMP_SCALE))
            self.image = pygame.transform.smoothscale(idle_img, (w, h))
        else:
            self.image = generate_chain_chomp_post()
        self.rect = self.image.get_rect(midbottom=(int(self.post_x), int(self.post_y)))
        self.pos_x = float(self.rect.x)
        self.home_x = float(self.rect.x)

    def update(self, solid, dt, level_w=None):
        if not self.alive:
            return

        if self.state == "idle":
            self.walk_timer += 1
            self.vx = 0
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.state = "lunging"
                self.lunge_timer = CHAIN_CHOMP_LUNGE_DURATION
                self.vx = self.facing * CHAIN_CHOMP_LUNGE_SPEED

        elif self.state == "lunging":
            self.lunge_timer -= 1
            if self.lunge_timer <= 0:
                self.state = "pullback"
                self.pullback_timer = 12

        elif self.state == "pullback":
            self.pullback_timer -= 1
            self.vx = -self.facing * CHAIN_CHOMP_PULLBACK_SPEED
            dx = self.home_x - self.pos_x
            if abs(dx) < 3 or self.pullback_timer <= 0:
                self.state = "idle"
                self.pos_x = self.home_x
                self.cooldown = CHAIN_CHOMP_COOLDOWN
                self.vx = 0

        self.pos_x += self.vx
        self.rect.x = round(self.pos_x)

        self.vy += 0.5
        if self.vy > 10:
            self.vy = 10
        self.on_ground = False
        self.rect.y += round(self.vy)
        for r in solid:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.rect.bottom = r.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = r.bottom
                    self.vy = 0

        if self.state == "idle":
            frame_key = "idle"
        elif self.state == "lunging":
            idx = max(1, min(6, (CHAIN_CHOMP_LUNGE_DURATION - self.lunge_timer) + 1))
            frame_key = f"lunge{idx}"
        else:
            idx = max(1, min(6, 6 - self.pullback_timer))
            frame_key = f"pullback{idx}"
        img = self.sprites.get(frame_key, self.sprites.get("idle"))
        if img:
            w = max(1, int(img.get_width() * CHAIN_CHOMP_SCALE))
            h = max(1, int(img.get_height() * CHAIN_CHOMP_SCALE))
            center = self.rect.center
            self.image = pygame.transform.smoothscale(img, (w, h))
            self.rect = self.image.get_rect(center=center)

    def draw(self, surface, offset):
        if not self.alive:
            return
        post_img = generate_chain_chomp_post()
        post_sx = int(self.post_x) - offset[0] - post_img.get_width() // 2
        post_sy = int(self.post_y) - offset[1] - post_img.get_height()
        surface.blit(post_img, (post_sx, post_sy))
        sx = self.rect.x - offset[0]
        sy = self.rect.y - offset[1]
        flip = self.facing == 1
        img = pygame.transform.flip(self.image, flip, False)
        surface.blit(img, (sx, sy))
