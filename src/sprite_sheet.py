import pygame
import json

class SpriteSheet:
    def __init__(self, image_path: str, json_path: str, scale: int = 3):
        self.scale  = scale
        self.sheet  = pygame.image.load(image_path).convert()
        self.sheet.set_colorkey((0, 0, 0))

        with open(json_path) as f:
            data = json.load(f)

        self._cache: dict[str, pygame.Surface] = {}
        for entry in data:
            surf = self._crop(entry)
            self._cache[entry["label"]] = surf

    def _crop(self, entry: dict) -> pygame.Surface:
        rect = pygame.Rect(entry["x"], entry["y"], entry["w"], entry["h"])
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        surf.blit(self.sheet, (0, 0), rect)
        surf.set_colorkey((0, 0, 0))

        if self.scale != 1:
            w = rect.w * self.scale
            h = rect.h * self.scale
            surf = pygame.transform.scale(surf, (w, h))

        return surf

    def get(self, label: str) -> pygame.Surface:
        return self._cache.get(label)

    def get_flipped(self, label: str) -> pygame.Surface:
        surf = self.get(label)
        return pygame.transform.flip(surf, True, False) if surf else None
