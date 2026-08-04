import pygame
import math
import random
from constants import (
    SCALE, GRAVITY, MAX_FALL, ATTACK_STATS,
    STOMP_DAMAGE, STOMP_KNOCKBACK,
    ENEMY_CONTACT_DAMAGE, ENEMY_CONTACT_KNOCKBACK, ENEMY_CONTACT_COOLDOWN,
    LAUNCH_SPEED_SCALE, GRRROL_SPEED, GRRROL_CONTACT_DAMAGE,
    GRRROL_CONTACT_KNOCKBACK, GRRROL_CONTACT_COOLDOWN,
    GRRROL_SIZE, GRRROL_ANIM_SPEED, GRRROL_KILL_PERCENT,
    BOBOMB_SIZE, BOBOMB_FALL_SPEED, BOBOMB_TARGET_SPEED, BOBOMB_EXPLOSION_RADIUS,
    BOBOMB_EXPLOSION_DAMAGE, BOBOMB_EXPLOSION_KB, BOBOMB_EXPLOSION_LAG,
    KAMEK_SIZE, KAMEK_FLY_SPEED, KAMEK_DRIFT_AMP, KAMEK_DRIFT_FREQ,
    KAMEK_HEALTH, KAMEK_MAGIC_DAMAGE, KAMEK_MAGIC_KB, KAMEK_MAGIC_SPEED,
    KAMEK_MAGIC_SIZE, KAMEK_MAGIC_COOLDOWN, KAMEK_TELEPORT_RANGE,
    KAMEK_TELEPORT_COOLDOWN, KAMEK_FLY_MIN_Y, KAMEK_FLY_MAX_Y,
    KAMEK_SPAWN_INTERVAL_MIN, KAMEK_SPAWN_INTERVAL_MAX,
)


def is_facing(attacker, victim):
    if attacker.facing == 1:
        return victim.rect.centerx >= attacker.rect.centerx
    else:
        return victim.rect.centerx <= attacker.rect.centerx

class Enemy(pygame.sprite.Sprite):
    """NPC enemy that participates in the Smash-Bros-style knockback system.

    Like players, enemies accumulate 'percentage' and take scaling knockback.
    They are eliminated when launched into a blast zone (off-screen margins).
    """

    def __init__(self, x, y, sheet=None, anim_labels=None, speed=1.0,
                 contact_damage=ENEMY_CONTACT_DAMAGE,
                 contact_knockback=ENEMY_CONTACT_KNOCKBACK):
        super().__init__()
        self.pos        = pygame.math.Vector2(x, y)
        self.base_speed = speed
        self.vel        = pygame.math.Vector2(-speed, 0)
        self.rect       = pygame.Rect(x, y, 28 * SCALE, 28 * SCALE)
        self.alive      = True
        self.on_ground  = False

        self.sheet  = sheet
        self.labels = anim_labels
        self._frame = 0
        self._timer = 0
        self.image  = None

        # --- Smash-Bros-style combat state ---
        self.percentage        = 0
        self.hitstun           = 0       # frames locked in knockback
        self.contact_cooldown  = 0       # frames before enemy can hit player again
        self.contact_damage    = contact_damage
        self.contact_knockback = contact_knockback

    # ================================================================ #
    #  Combat                                                           #
    # ================================================================ #
    def take_damage(self, damage_amount, knockback, attacker_facing):
        """Smash-Bros-style damage with percentage-scaled knockback.

        Mirrors Player.take_damage exactly so PvP and PvE feel consistent.
        """
        if not self.alive:
            return
        self.percentage += damage_amount

        P = self.percentage
        D = damage_amount
        W = 100.0
        S = 1.0
        B = knockback

        KB = (((2 * P + D) / 20.0) * (200.0 / (W + 100.0)) * 1.4 + 18) * S + B
        launch_speed = KB * LAUNCH_SPEED_SCALE * 0.6

        self.vel.x = launch_speed * attacker_facing
        self.vel.y = -(launch_speed * 0.7)
        self.hitstun = max(self.hitstun, int(KB * 0.015 + 8))

    @property
    def facing(self):
        return 1 if self.vel.x > 0 else -1

    def check_player_attack(self, player):
        """Apply melee damage if the player's swing overlaps this enemy.
        One hit per swing (attacking resets to 0 on contact)."""
        if not self.alive or player.is_dead:
            return False
        if player.attacking <= 5:               # wind-up frames 5→0 are active
            return False
        if not self.rect.colliderect(player.rect):
            return False

        stats = ATTACK_STATS.get(player.char, {"damage": 8, "base_knockback": 12})
        self.take_damage(
            damage_amount=stats["damage"],
            knockback=stats["base_knockback"],
            attacker_facing=player.facing,
        )
        player.attacking = 0                     # swing ends on hit
        if player.on_ground:
            player.vel.y = -4                    # small hop (Smash-style)
        return True

    def check_player_hit(self, player):
        """Body-contact between enemy and player.

        * Player falling on top  → stomp (damage + bounce).
        * Otherwise              → contact damage to the player (with cooldown).
        """
        if not self.alive or player.is_dead:
            return
        if not self.rect.colliderect(player.rect):
            return

        # --- Stomp: player landing on the enemy from above ---
        if player.vel.y > 0 and player.rect.bottom < self.rect.centery + 6:
            self.take_damage(
                damage_amount=STOMP_DAMAGE,
                knockback=STOMP_KNOCKBACK,
                attacker_facing=player.facing,
            )
            player.vel.y = -8                    # bounce the attacker
            return

        # --- Body contact: enemy damages player (cooldown-gated) ---
        if self.contact_cooldown <= 0:
            player.take_damage(
                base_damage=self.contact_damage,
                knockback_growth=1.0,
                base_knockback=self.contact_knockback,
                attacker_facing=self.facing,
            )
            self.contact_cooldown = ENEMY_CONTACT_COOLDOWN

    def check_blast_zone(self, level_w, level_h, margin=350):
        """KO the enemy when launched beyond the level boundaries."""
        if not self.alive:
            return
        if (self.rect.right < -margin
                or self.rect.left  >  level_w + margin
                or self.rect.top   >  level_h + margin
                or self.rect.bottom < -margin * 2):
            self.stomp()

    def stomp(self):
        self.alive = False
        self.kill()

    # ================================================================ #
    #  Physics & animation                                              #
    # ================================================================ #
    def update(self, tiles, dt):
        if not self.alive:
            return

        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1
        if self.hitstun > 0:
            self.hitstun -= 1

        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL)

        # Horizontal behaviour: hitstun decay vs. patrol resume
        if self.hitstun > 0:
            self.vel.x *= 0.92                   # decay knockback velocity
        elif self.on_ground:
            direction = -1 if self.vel.x < 0 else 1
            self.vel.x = direction * self.base_speed

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        self._collide_x(tiles)

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        self._collide_y(tiles)

        # Two-frame walk animation
        self._timer += dt
        if self._timer > 0.12:
            self._timer = 0
            self._frame = 1 - self._frame
        if self.sheet and self.labels:
            self.image = self.sheet.get(self.labels[self._frame])

    def _collide_x(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.x > 0:
                    self.rect.right = tile.left
                elif self.vel.x < 0:
                    self.rect.left = tile.right
                if self.hitstun > 0:
                    self.vel.x *= -0.4            # weak wall-bounce during knockback
                else:
                    self.vel.x *= -1              # reverse patrol direction
                self.pos.x = self.rect.x

    def _collide_y(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.y > 0:
                    self.rect.bottom = tile.top
                    self.vel.y = 0
                    self.pos.y = self.rect.y
                    self.on_ground = True
                    # Edge detection — turn at ledges (patrol only)
                    if self.hitstun <= 0:
                        probe = self.rect.move(self.vel.x * 2, 2)
                        if not any(probe.colliderect(t) for t in tiles):
                            self.vel.x *= -1
                elif self.vel.y < 0:
                    self.rect.top = tile.bottom
                    self.vel.y = 0
                    self.pos.y = self.rect.y

    # ================================================================ #
    #  Rendering                                                         #
    # ================================================================ #
    def draw(self, surface, camera_offset):
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        if self.image:
            surface.blit(self.image, (draw_x, draw_y))
        else:
            # Fallback: coloured rect (tinted bright during hitstun)
            colour = (255, 80, 80) if self.hitstun > 0 else (200, 60, 60)
            pygame.draw.rect(surface, colour,
                             (draw_x, draw_y, self.rect.w, self.rect.h))


class Grrrol(Enemy):
    """Rolling spiked-stone enemy from New Super Mario Bros. U.
    
    Patrols back and forth, bounces off walls, deals contact damage.
    Cannot be killed by normal attacks — only stomps or high-percent launch.
    """

    def __init__(self, x, y, roll_frames=None):
        super().__init__(
            x, y,
            speed=GRRROL_SPEED,
            contact_damage=GRRROL_CONTACT_DAMAGE,
            contact_knockback=GRRROL_CONTACT_KNOCKBACK,
        )
        self.roll_frames = roll_frames or []
        self.rect = pygame.Rect(x, y, GRRROL_SIZE, GRRROL_SIZE)
        self.base_speed = GRRROL_SPEED
        self.vel = pygame.math.Vector2(-GRRROL_SPEED, 0)
        self.contact_cooldown = 0

        self._frame = 0
        self._anim_timer = 0.0
        self.image = self.roll_frames[0] if self.roll_frames else None

    def update(self, tiles, dt):
        if not self.alive:
            return

        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1
        if self.hitstun > 0:
            self.hitstun -= 1

        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL)

        if self.hitstun > 0:
            self.vel.x *= 0.92
        elif self.on_ground:
            direction = -1 if self.vel.x < 0 else 1
            self.vel.x = direction * self.base_speed

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        self._collide_x(tiles)

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        self._collide_y(tiles)

        if self.roll_frames:
            self._anim_timer += dt
            if self._anim_timer >= GRRROL_ANIM_SPEED:
                self._anim_timer = 0.0
                self._frame = (self._frame + 1) % len(self.roll_frames)
            self.image = self.roll_frames[self._frame % len(self.roll_frames)]

    def check_player_attack(self, player):
        if not self.alive or player.is_dead:
            return False
        if player.attacking <= 5:
            return False
        if not self.rect.colliderect(player.rect):
            return False
        if not is_facing(player, self):
            return False

        stats = ATTACK_STATS.get(player.char, {"damage": 8, "base_knockback": 12})
        self.take_damage(
            damage_amount=stats["damage"],
            knockback=stats["base_knockback"],
            attacker_facing=player.facing,
        )
        player.attacking = 0
        if player.on_ground:
            player.vy_int = -4
        return True

    def take_damage(self, damage_amount, knockback, attacker_facing):
        if not self.alive:
            return
        self.percentage += damage_amount

        P = self.percentage
        D = damage_amount
        W = 100.0
        S = 1.0
        B = knockback

        KB = (((2 * P + D) / 20.0) * (200.0 / (W + 100.0)) * 1.4 + 18) * S + B
        launch_speed = KB * LAUNCH_SPEED_SCALE * 0.6

        self.vel.x = launch_speed * attacker_facing
        self.vel.y = -(launch_speed * 0.7)
        self.hitstun = max(self.hitstun, int(KB * 0.015 + 8))

        if self.percentage >= GRRROL_KILL_PERCENT:
            self.stomp()

    def check_player_hit(self, player):
        if not self.alive or player.is_dead:
            return
        if not self.rect.colliderect(player.rect):
            return

        player_vy = player.vy_int + player.vy_ext
        if player_vy > 0 and player.rect.bottom < self.rect.centery + 6:
            self.take_damage(
                damage_amount=STOMP_DAMAGE,
                knockback=STOMP_KNOCKBACK,
                attacker_facing=player.facing,
            )
            if self.contact_cooldown <= 0:
                player.take_damage(
                    base_damage=self.contact_damage,
                    knockback_growth=1.0,
                    base_knockback=self.contact_knockback,
                    attacker_facing=self.facing,
                )
                self.contact_cooldown = GRRROL_CONTACT_COOLDOWN
            player.vy_int = -8
            player.vy_ext = 0
            return

        if self.contact_cooldown <= 0:
            player.take_damage(
                base_damage=self.contact_damage,
                knockback_growth=1.0,
                base_knockback=self.contact_knockback,
                attacker_facing=self.facing,
            )
            self.contact_cooldown = GRRROL_CONTACT_COOLDOWN

    def _collide_y(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.y > 0:
                    self.rect.bottom = tile.top
                    self.vel.y = 0
                    self.pos.y = self.rect.y
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = tile.bottom
                    self.vel.y = 0
                    self.pos.y = self.rect.y

    def draw(self, surface, camera_offset):
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        if self.image:
            img = self.image
            if self.facing == -1:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (draw_x, draw_y))
        else:
            colour = (255, 80, 80) if self.hitstun > 0 else (120, 120, 120)
            pygame.draw.rect(surface, colour,
                             (draw_x, draw_y, self.rect.w, self.rect.h))


class BobOmb(pygame.sprite.Sprite):
    """Para-bomb: falls with parachute, drifts toward players, explodes on ground contact."""

    def __init__(self, x, y, sprites=None, targets=None):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, BOBOMB_FALL_SPEED)
        self.sprites = sprites or {}
        self.targets = targets or []
        self.image = self.sprites.get("fall")
        if self.image:
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, BOBOMB_SIZE, BOBOMB_SIZE)
        self.alive = True
        self.on_ground = False
        self.exploding = False
        self.start_explode_timer = 0
        self.explosion_frames = self.sprites.get("explosion", [])
        self.start_explode_frames = self.sprites.get("start_explode", [])
        self.explosion_frame_idx = 0
        self.explosion_timer = 0
        self.hit_players = set()

    def update(self, tiles):
        if not self.alive:
            return

        if self.exploding:
            self.explosion_timer -= 1
            if self.start_explode_timer > 0:
                self.start_explode_timer -= 1
                if self.start_explode_frames:
                    elapsed = 10 - self.start_explode_timer
                    fi = min(elapsed, len(self.start_explode_frames) - 1)
                    self.image = self.start_explode_frames[fi]
            elif self.explosion_timer > 0:
                self.explosion_frame_idx += 1
                if self.explosion_frames:
                    fi = min(self.explosion_frame_idx // 6, len(self.explosion_frames) - 1)
                    self.image = self.explosion_frames[fi]
            else:
                self.alive = False
                self.kill()
            return

        self.vel.y = min(self.vel.y + GRAVITY * 0.4, BOBOMB_FALL_SPEED)

        if self.targets:
            closest = None
            closest_dist = float('inf')
            for t in self.targets:
                if hasattr(t, 'rect') and not getattr(t, 'is_dead', False):
                    dx = t.rect.centerx - self.rect.centerx
                    dy = t.rect.centery - self.rect.centery
                    dist = dx * dx + dy * dy
                    if dist < closest_dist:
                        closest_dist = dist
                        closest = t
            if closest:
                dx = closest.rect.centerx - self.rect.centerx
                if abs(dx) > 4:
                    self.vel.x = BOBOMB_TARGET_SPEED * (1 if dx > 0 else -1)
                else:
                    self.vel.x *= 0.9

        ground_dist = 0
        for tile in tiles:
            if tile.top >= self.rect.bottom and abs(tile.centerx - self.rect.centerx) < 64:
                if ground_dist == 0 or tile.top < ground_dist:
                    ground_dist = tile.top
        near_ground = ground_dist > 0 and (ground_dist - self.rect.bottom) < 60

        if self.vel.x > 0.3:
            side = "right"
        elif self.vel.x < -0.3:
            side = "left"
        else:
            side = "right"

        if near_ground:
            key = f"abouttoland_{side}"
            if key in self.sprites:
                self.image = self.sprites[key]
            elif "fall" in self.sprites:
                self.image = self.sprites["fall"]
        elif abs(self.vel.x) > 0.3:
            key = f"glide_{side}"
            if key in self.sprites:
                self.image = self.sprites[key]
        else:
            if "fall" in self.sprites:
                self.image = self.sprites["fall"]

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False

        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.y > 0:
                    self.rect.bottom = tile.top
                    self.vel.y = 0
                    self.pos.y = self.rect.y
                    self.on_ground = True

        if self.on_ground:
            self._explode()

    def _explode(self):
        self.exploding = True
        self.start_explode_timer = 10
        self.explosion_timer = 10 + len(self.explosion_frames) * 6
        if self.start_explode_frames:
            self.image = self.start_explode_frames[0]
            old_cx, old_cy = self.rect.centerx, self.rect.centery
            self.rect = self.image.get_rect(center=(old_cx, old_cy))

    def check_hit(self, player):
        if not self.alive or not self.exploding:
            return
        if self.start_explode_timer > 0:
            return
        if not self.explosion_frames:
            return
        pid = id(player)
        if pid in self.hit_players:
            return
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < BOBOMB_EXPLOSION_RADIUS and not player.is_dead:
            facing = 1 if dx <= 0 else -1
            player.take_damage(
                base_damage=BOBOMB_EXPLOSION_DAMAGE,
                knockback_growth=1.0,
                base_knockback=BOBOMB_EXPLOSION_KB,
                attacker_facing=facing,
                kb_bonus=1.0,
                knockback_type="normal",
            )
            self.hit_players.add(pid)

    def draw(self, surface, camera_offset):
        if not self.alive:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        if self.image:
            surface.blit(self.image, (draw_x, draw_y))
        else:
            if self.exploding:
                colour = (255, 160, 40)
            else:
                colour = (40, 40, 40)
            pygame.draw.rect(surface, colour, self.rect)


class MagicProjectile:
    """Magic bolt fired by Kamek. Travels in a direction, damages players on hit."""

    def __init__(self, x, y, dx, dy, sprites=None, owner=None):
        self.rect = pygame.Rect(x, y, KAMEK_MAGIC_SIZE, KAMEK_MAGIC_SIZE)
        self.dx = dx
        self.dy = dy
        self.alive = True
        self.damage = KAMEK_MAGIC_DAMAGE
        self.knockback = KAMEK_MAGIC_KB
        self.owner = owner
        self.sprites = sprites or []
        self._frame = 0
        self._anim_timer = 0.0
        self._lifetime = 180
        self.hit_players = set()

    def update(self):
        if not self.alive:
            return
        self.rect.x += self.dx
        self.rect.y += self.dy
        self._lifetime -= 1
        if self._lifetime <= 0:
            self.alive = False
        if self.sprites:
            self._anim_timer += 1
            if self._anim_timer >= 4:
                self._anim_timer = 0
                self._frame += 1

    def check_player_hit(self, player):
        if not self.alive or player.is_dead:
            return
        pid = id(player)
        if pid in self.hit_players:
            return
        if not self.rect.colliderect(player.rect):
            return
        if player == self.owner:
            return
        player.take_damage(
            base_damage=self.damage,
            knockback_growth=1.0,
            base_knockback=self.knockback,
            attacker_facing=1 if self.dx > 0 else -1,
        )
        self.hit_players.add(pid)
        self.alive = False

    def draw(self, surface, camera_offset):
        if not self.alive:
            return
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        if self.sprites:
            idx = self._frame % len(self.sprites)
            img = self.sprites[idx]
            surface.blit(img, (draw_x, draw_y))
        else:
            pygame.draw.circle(surface, (100, 180, 255), self.rect.center, KAMEK_MAGIC_SIZE // 2)


class Kamek:
    """Flying wizard enemy that shoots magic and spawns minions.

    Flies in dynamic circular/figure-8 patterns, faces the player,
    tilts before attacking, and teleports when approached.
    """

    def __init__(self, x, y, sprites=None):
        self.rect = pygame.Rect(x, y, KAMEK_SIZE, KAMEK_SIZE)
        self.pos = pygame.math.Vector2(x, y)
        self.alive = True
        self.health = KAMEK_HEALTH
        self.facing = 1
        self.sprites = sprites or {}
        self.image = None
        self._raw_image = None

        self._fly_phase = 0.0
        self._orbit_angle = 0.0
        self._anim_frame = 0
        self._anim_timer = 0.0

        self.magic_cooldown = 0
        self.teleport_cooldown = KAMEK_TELEPORT_COOLDOWN
        self.spawn_timer = 0
        self.spawn_interval = 300

        self.state = "fly"
        self.attack_timer = 0
        self.attack_duration = 40
        self.tilt_angle = 0
        self.target_tilt = 0

        self._hover_offset_x = 0.0
        self._hover_offset_y = 0.0
        self._hover_angle = random.uniform(0, math.tau)
        self._hover_speed = random.uniform(1.0, 1.8)
        self._hover_rx = random.randint(8, 20)
        self._hover_ry = random.randint(5, 15)

        self._sine_dir = random.choice([-1, 1])
        self._sine_base_y = y

    def update(self, players, level_w, level_h):
        if not self.alive:
            return

        self._fly_phase += 0.016
        self._orbit_angle += self._hover_speed * 0.016

        if self.magic_cooldown > 0:
            self.magic_cooldown -= 1
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
        self.spawn_timer += 1

        closest = self._closest_player(players)

        if self.state == "fly":
            if closest:
                self._fly_chase(closest, level_w, level_h)

                dx = closest.rect.centerx - self.rect.centerx
                dy = closest.rect.centery - self.rect.centery
                self.facing = 1 if dx >= 0 else -1

                dist_to_player = math.hypot(dx, dy)
                if dist_to_player > 0:
                    self.target_tilt = max(-40, min(40, math.degrees(math.atan2(dy, abs(dx) + 1)) * 0.6))
                else:
                    self.target_tilt = 0
            else:
                self._fly_idle(level_w, level_h)
                self.target_tilt = 0

            self.tilt_angle += (self.target_tilt - self.tilt_angle) * 0.1

            self._animate_fly()

            if self.spawn_timer >= self.spawn_interval and closest:
                self.state = "windup"
                self.attack_timer = 15
                self.spawn_timer = 0
                self.spawn_interval = random.randint(KAMEK_SPAWN_INTERVAL_MIN, KAMEK_SPAWN_INTERVAL_MAX)

        elif self.state == "windup":
            self.attack_timer -= 1
            self._animate_attack()
            self.tilt_angle += (-35 - self.tilt_angle) * 0.15
            self._fly_chase(closest, level_w, level_h)
            if self.attack_timer <= 0:
                self.state = "attack"
                self.attack_timer = 20

        elif self.state == "attack":
            self.attack_timer -= 1
            self._animate_attack()
            self.tilt_angle += (10 - self.tilt_angle) * 0.1
            if closest:
                dx = closest.rect.centerx - self.rect.centerx
                self.facing = 1 if dx >= 0 else -1
            if self.attack_timer <= 0:
                self.state = "fly"
                self.magic_cooldown = KAMEK_MAGIC_COOLDOWN
                self.tilt_angle = 0
                self.target_tilt = 0
                self._hover_rx = random.randint(8, 20)
                self._hover_ry = random.randint(5, 15)

        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def _fly_chase(self, closest, level_w, level_h):
        self.pos.x += self._sine_dir * 1.8
        if self.pos.x > level_w - 80:
            self._sine_dir = -1
        elif self.pos.x < 80:
            self._sine_dir = 1

        self.pos.y = self._sine_base_y + math.sin(self._fly_phase * 2.0) * 60

        self.pos.x = max(30, min(level_w - 30, self.pos.x))
        self.pos.y = max(KAMEK_FLY_MIN_Y, min(KAMEK_FLY_MAX_Y, self.pos.y))

    def _fly_idle(self, level_w, level_h):
        self.pos.x += math.sin(self._fly_phase * 0.8) * 1.0
        self.pos.y += math.sin(self._fly_phase * 1.2) * 0.8

        self.pos.x = max(30, min(level_w - 30, self.pos.x))
        self.pos.y = max(KAMEK_FLY_MIN_Y, min(KAMEK_FLY_MAX_Y, self.pos.y))

    def _animate_fly(self):
        self._anim_timer += 0.016
        if self._anim_timer >= 0.18:
            self._anim_timer = 0
            self._anim_frame += 1
        frames = self.sprites.get("fly_right", [])
        if frames:
            self._raw_image = frames[self._anim_frame % len(frames)]

    def _animate_attack(self):
        frames = self.sprites.get("attack_right", [])
        if frames:
            self._raw_image = frames[self._anim_frame % len(frames)]

    def _closest_player(self, players):
        closest = None
        min_dist = float("inf")
        for p in players:
            if p.is_dead:
                continue
            d = math.hypot(p.rect.centerx - self.rect.centerx,
                           p.rect.centery - self.rect.centery)
            if d < min_dist:
                min_dist = d
                closest = p
        return closest

    def _teleport(self, closest, level_w, level_h):
        side = random.choice([-1, 1])
        self.pos.x = closest.rect.centerx + side * random.randint(100, 180)
        self.pos.y = closest.rect.centery - random.randint(30, 100)
        self.pos.x = max(30, min(level_w - 30, self.pos.x))
        self.pos.y = max(KAMEK_FLY_MIN_Y, min(KAMEK_FLY_MAX_Y, self.pos.y))
        self.teleport_cooldown = KAMEK_TELEPORT_COOLDOWN
        self._hover_angle = random.uniform(0, math.tau)
        self._hover_rx = random.randint(8, 20)
        self._hover_ry = random.randint(5, 15)

    def fire_magic(self, players):
        if not self.alive or self.magic_cooldown > 0:
            return None
        closest = self._closest_player(players)
        if not closest:
            return None
        dx = closest.rect.centerx - self.rect.centerx
        dy = closest.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 1:
            return None
        nx = (dx / dist) * KAMEK_MAGIC_SPEED
        ny = (dy / dist) * KAMEK_MAGIC_SPEED
        self.magic_cooldown = KAMEK_MAGIC_COOLDOWN
        return MagicProjectile(
            self.rect.centerx - KAMEK_MAGIC_SIZE // 2,
            self.rect.centery - KAMEK_MAGIC_SIZE // 2,
            nx, ny,
            sprites=self.sprites.get("magic", []),
            owner=None,
        )

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def check_player_attack(self, player):
        if not self.alive or player.is_dead:
            return False
        if player.attacking <= 5:
            return False
        if not self.rect.colliderect(player.rect):
            return False
        if not is_facing(player, self):
            return False
        stats = ATTACK_STATS.get(player.char, {"damage": 8, "base_knockback": 12})
        self.take_damage(stats["damage"])
        player.attacking = 0
        if player.on_ground:
            player.vy_int = -4
        return True

    def draw(self, surface, camera_offset):
        if not self.alive:
            return
        draw_x = self.rect.centerx - camera_offset[0]
        draw_y = self.rect.centery - camera_offset[1]
        if self._raw_image:
            img = self._raw_image
            if self.facing == -1:
                img = pygame.transform.flip(img, True, False)
            if abs(self.tilt_angle) > 1:
                img = pygame.transform.rotate(img, self.tilt_angle * self.facing)
            w, h = img.get_size()
            surface.blit(img, (draw_x - w // 2, draw_y - h // 2))
        else:
            colour = (180, 100, 255) if self.state == "fly" else (255, 100, 180)
            pygame.draw.ellipse(surface, colour, self.rect)
