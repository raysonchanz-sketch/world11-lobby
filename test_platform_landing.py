import sys; sys.path.insert(0, '.')
import os; os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame; pygame.init(); pygame.display.set_mode((800, 600), pygame.NOFRAME)

from src.player import Player, CTRL_P1
from src.tilemap import Tilemap
from src.sprite_loader import SpriteLoader, MARIO_FILE_MAP
from constants import *

# Setup
mario_sprites = SpriteLoader('mario_assets', MARIO_FILE_MAP, scale=SCALE)
tileset_surf = pygame.image.load('assets/tiles/tileset.png').convert()
tilemap = Tilemap('assets/levels/world1-1.json', pygame.image.load('assets/tiles/tileset.png').convert())
solid = tilemap.solid_rects()
platforms = tilemap.platform_rects()

ground_y = 33 * 32
player1 = Player(200, ground_y - 44, SpriteLoader('mario_assets', MARIO_FILE_MAP, scale=SCALE), character='mario', controls=CTRL_P1)
player2 = Player(300, ground_y - 44, SpriteLoader('luigi_assets', MARIO_FILE_MAP, scale=SCALE), character='luigi', controls=CTRL_P2)

# Auto-select characters (simulate F/G and J/K presses)
keys1 = {k: False for k in list(CTRL_P1.values())}
keys2 = {k: False for k in list(CTRL_P2.values())}

# Character select: P1=Mario (F), P2=Luigi (J)
keys1[pygame.K_f] = True
keys2[pygame.K_j] = True

dt = 1.0 / FPS

# Character select
for _ in range(10):
    player1.update(keys1, solid, 1.0/FPS, platforms)
    player2.update(keys2, solid, 1.0/FPS, platforms)

# Now test jump to platform
keys1[pygame.K_f] = False
keys1[pygame.K_w] = True  # P1 jump

player1.on_ground = False
player1.coyote_time = 0
player1.jump_buffer = 0

print('Testing jump to platform...')
platform_landed = False
for i in range(80):
    # P1 jumps for first 20 frames
    if 0 <= i < 20:
        keys1[pygame.K_w] = True
    else:
        keys1[pygame.K_w] = False
    
    player1.update(keys1, solid, 1.0/FPS, platforms)
    player2.update(keys2, solid, 1.0/FPS, platforms)
    
    if i % 5 == 0:
        on_platform = player1.rect.bottom <= 992 and player1.rect.bottom >= 960
        print(f'Frame {i}: y={player1.rect.y:.1f} vel_y={player1.vel.y:.1f} on_g={player1.on_ground} on_platform={on_platform}')
        if on_platform:
            platform_landed = True

    if i == 20:
        keys1[pygame.K_w] = False

print(f'Platform landed: {platform_landed}')
print(f'Final: pos={player1.rect.topleft} vel={player1.vel} on_g={player1.on_ground}')

pygame.quit()