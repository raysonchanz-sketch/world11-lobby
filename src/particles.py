import pygame
import random
import math


class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, gravity=0.0, fade=True, glow=False):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life
        self.gravity = gravity
        self.fade = fade
        self.glow = glow

    def update(self):
        self.vel.y += self.gravity
        self.pos += self.vel
        self.life -= 1
        return self.life > 0

    def draw(self, surface, offset):
        progress = 1.0 - (self.life / self.max_life) if self.max_life > 0 else 1.0
        alpha = int(255 * (1.0 - progress)) if self.fade else 255
        r = max(1, int(self.size * (1.0 - progress * 0.5)))
        sx = int(self.pos.x - offset[0])
        sy = int(self.pos.y - offset[1])
        if self.glow:
            glow_r = r + 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, alpha // 2), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (sx - glow_r, sy - glow_r))
        c = (*self.color, alpha) if self.fade else self.color
        draw_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(draw_surf, c, (r, r), r)
        surface.blit(draw_surf, (sx - r, sy - r))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface, offset):
        for p in self.particles:
            p.draw(surface, offset)

    def emit(self, x, y, color, count=8, speed=3, size=3, life=20, gravity=0.1, fade=True, glow=False):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            sz = random.uniform(size * 0.5, size)
            lt = random.randint(int(life * 0.6), life)
            self.particles.append(Particle(x, y, vx, vy, color, sz, lt, gravity, fade, glow))

    def hit_spark(self, x, y, facing=1, percent=0):
        base = min(12, 6 + int(percent * 0.1))
        colors = [(255, 255, 100), (255, 220, 60), (255, 180, 30), (255, 255, 200)]
        for _ in range(base):
            angle = random.uniform(-0.8, 0.8) + (0 if facing >= 0 else math.pi)
            spd = random.uniform(3, 8)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - random.uniform(0, 2)
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2, 5),
                                           random.randint(8, 18), 0.05, True, True))
        for _ in range(base // 2):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(1, 4)
            self.particles.append(Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd,
                                           (255, 255, 255), random.uniform(1, 3),
                                           random.randint(5, 12), 0.0, True, False))

    def ko_explosion(self, x, y):
        colors = [(255, 100, 30), (255, 180, 50), (255, 255, 100), (255, 60, 20), (255, 220, 80)]
        for _ in range(30):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(2, 10)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(3, 8),
                                           random.randint(20, 45), 0.08, True, True))
        for _ in range(15):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(1, 5)
            self.particles.append(Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd,
                                           (255, 255, 255), random.uniform(2, 5),
                                           random.randint(10, 25), 0.02, True, False))

    def dust(self, x, y, count=5):
        colors = [(180, 170, 150), (200, 190, 170), (160, 150, 130)]
        for _ in range(count):
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(-2, -0.5)
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2, 4),
                                           random.randint(10, 20), -0.02, True, False))

    def magic_impact(self, x, y):
        colors = [(100, 180, 255), (150, 200, 255), (80, 140, 255), (200, 220, 255)]
        for _ in range(12):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(2, 6)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2, 5),
                                           random.randint(12, 25), 0.0, True, True))
        for _ in range(6):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(0.5, 2)
            self.particles.append(Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd,
                                           (200, 230, 255), random.uniform(1, 3),
                                           random.randint(8, 15), 0.0, True, False))

    def shield_hit(self, x, y):
        colors = [(100, 200, 255), (150, 220, 255), (80, 180, 255), (200, 240, 255)]
        for _ in range(10):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(2, 5)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2, 4),
                                           random.randint(10, 20), 0.0, True, True))

    def dash_dust(self, x, y, facing=1):
        colors = [(180, 170, 150), (200, 190, 170)]
        for _ in range(4):
            vx = -facing * random.uniform(0.5, 2)
            vy = random.uniform(-1.5, -0.3)
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2, 4),
                                           random.randint(8, 16), -0.02, True, False))


class BlastZoneExplosion:
    def __init__(self, x, y, frames, duration=18):
        self.x = x
        self.y = y
        self.frames = frames
        self.total_frames = duration
        self.timer = 0
        self.alive = True
        self.scaled_frames = []
        for i, frame in enumerate(frames):
            scale = 0.8 + (i * 0.6)
            w = max(1, int(frame.get_width() * scale))
            h = max(1, int(frame.get_height() * scale))
            scaled = pygame.transform.smoothscale(frame, (w, h))
            self.scaled_frames.append(scaled)

    def update(self):
        self.timer += 1
        if self.timer >= self.total_frames:
            self.alive = False

    def draw(self, surface, offset):
        if not self.alive:
            return
        progress = self.timer / self.total_frames
        frame_idx = min(int(progress * len(self.frames)), len(self.frames) - 1)
        img = self.scaled_frames[frame_idx]
        alpha = max(0, int(255 * (1.0 - progress)))
        faded = img.copy()
        faded.set_alpha(alpha)
        sx = int(self.x - offset[0] - faded.get_width() // 2)
        sy = int(self.y - offset[1] - faded.get_height() // 2)
        surface.blit(faded, (sx, sy))
