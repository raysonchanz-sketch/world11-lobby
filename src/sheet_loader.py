import pygame
import numpy as np

def threshold_colorkey(surface: pygame.Surface, threshold: int = 30) -> pygame.Surface:
    arr = pygame.surfarray.pixels3d(surface)
    max_ch = arr.max(axis=2)
    rgba = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    rgba_arr = pygame.surfarray.pixels3d(rgba)
    alpha_arr = pygame.surfarray.pixels_alpha(rgba)
    rgba_arr[:] = arr
    alpha_arr[:] = np.where(max_ch < threshold, 0, 255)
    del arr, rgba_arr, alpha_arr
    return rgba

class SheetAnimLoader:
    def __init__(self, image_path, frame_defs, scale=3):
        self.scale = scale
        sheet = pygame.image.load(image_path).convert_alpha()
        sheet = threshold_colorkey(sheet)
        self._cache = {}

        for label, (x, y, w, h) in frame_defs.items():
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), (x, y, w, h))
            surf = pygame.transform.flip(surf, True, False)
            if scale != 1:
                surf = pygame.transform.scale(surf, (w * scale, h * scale))
            self._cache[label] = surf

    def get(self, label):
        return self._cache.get(label)

    def get_flipped(self, label):
        surf = self.get(label)
        return pygame.transform.flip(surf, True, False) if surf else None

SHEET_PATHS = {
    "waluigi": "Custom _ Edited - Mario Customs - Waluigi - Waluigi (Super Mario World-Style).png",
    "shyguy":  "Game Boy Advance - Super Mario Advance 3_ Yoshi's Island - Enemies - Shy Guy.png",
    "kamek":   "Custom _ Edited - Mario Customs - Kamek & Magikoopa - Kamek (Yoshi's Island DS-Style, Expanded)-Photoroom.png",
    "larry":   "Custom _ Edited - Mario Customs - The Koopalings - Larry Koopa (Mario & Luigi_ Bowser's Inside Story-Style).png",
}

LEFT = 0  # SMW palette in left half of Waluigi sheet

WALUIGI_FRAMES = {
    "Waluigi - Idle":   (LEFT+1,   1,  36, 50),
    "Waluigi - Walk 1": (LEFT+1,   53, 28, 80),
    "Waluigi - Walk 2": (LEFT+29,  53, 28, 80),
    "Waluigi - Walk 3": (LEFT+57,  53, 28, 80),
    "Waluigi - Run 1":  (LEFT+1,   135, 27, 38),
    "Waluigi - Run 2":  (LEFT+29,  135, 27, 38),
    "Waluigi - Run 3":  (LEFT+57,  135, 27, 38),
    "Waluigi - Run 4":  (LEFT+85,  135, 27, 38),
    "Waluigi - Skid":   (LEFT+2,   382, 16, 30),
    "Waluigi - Jump":   (LEFT+1,   175, 37, 122),
    "Waluigi - Fall":   (LEFT+39,  175, 37, 122),
    "Waluigi - Crouch": (LEFT+1,   298, 34, 82),
    "Waluigi - Spin 1": (LEFT+2,   382, 16, 30),
    "Waluigi - Spin 2": (LEFT+19,  382, 16, 30),
    "Waluigi - Spin 3": (LEFT+36,  382, 16, 30),
    "Waluigi - Spin 4": (LEFT+53,  382, 16, 30),
    "Waluigi - Death 1":(LEFT+1,   298, 34, 82),
    "Waluigi - Death 2":(LEFT+35,  298, 34, 82),
    "Waluigi - Death 3":(LEFT+69,  298, 34, 82),
}

SHYGUY_FRAMES = {
    "ShyGuy - Idle":   (1,   0,  16, 16),
    "ShyGuy - Walk 1": (17,  0,  16, 16),
    "ShyGuy - Walk 2": (33,  0,  16, 16),
    "ShyGuy - Walk 3": (49,  0,  16, 16),
    "ShyGuy - Walk 4": (65,  0,  16, 16),
    "ShyGuy - Run 1":  (81,  0,  16, 16),
    "ShyGuy - Run 2":  (97,  0,  16, 16),
    "ShyGuy - Run 3":  (113, 0,  16, 16),
    "ShyGuy - Run 4":  (129, 0,  16, 16),
    "ShyGuy - Jump":   (145, 0,  16, 16),
    "ShyGuy - Spin 1": (161, 0,  16, 16),
    "ShyGuy - Spin 2": (177, 0,  16, 16),
    "ShyGuy - Death 1":(193, 0,  16, 16),
    "ShyGuy - Death 2":(209, 0,  16, 16),
}

KAMEK_FRAMES = {
    "Kamek - Idle":    (8,   0,  31, 38),
    "Kamek - Walk 1":  (8,   43, 31, 35),
    "Kamek - Walk 2":  (40,  43, 31, 35),
    "Kamek - Walk 3":  (72,  43, 31, 35),
    "Kamek - Cast 1":  (0,   83, 41, 38),
    "Kamek - Cast 2":  (42,  83, 41, 38),
    "Kamek - Cast 3":  (84,  83, 41, 38),
    "Kamek - Cast 4":  (0,   83, 41, 38),
    "Kamek - Jump":    (173, 0,  47, 38),
    "Kamek - Hurt":    (8,   129, 29, 36),
    "Kamek - Death 1": (8,   170, 32, 45),
    "Kamek - Death 2": (8,   275, 32, 39),
}

LARRY_FRAMES = {
    "Larry - Idle":     (0,   27,  64, 81),
    "Larry - Walk 1":   (64,  111, 64, 81),
    "Larry - Walk 2":   (128, 111, 64, 81),
    "Larry - Walk 3":   (192, 111, 64, 81),
    "Larry - Hard":     (0,   195, 64, 173),
    "Larry - Shell":    (64,  195, 64, 173),
    "Larry - Spin 1":   (128, 195, 64, 173),
    "Larry - Spin 2":   (192, 195, 64, 173),
    "Larry - Spin 3":   (256, 195, 64, 173),
    "Larry - Fall":     (0,   369, 64, 173),
    "Larry - Fireball 1":(0,   720, 64, 173),
    "Larry - Fireball 2":(64,  720, 64, 173),
    "Larry - Death 1":  (320, 195, 64, 173),
    "Larry - Death 2":  (384, 195, 64, 173),
}

SHEET_FRAMES = {
    "waluigi": WALUIGI_FRAMES,
    "shyguy":  SHYGUY_FRAMES,
    "kamek":   KAMEK_FRAMES,
    "larry":   LARRY_FRAMES,
}
