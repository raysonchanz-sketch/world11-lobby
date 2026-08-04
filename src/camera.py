import pygame
from constants import SCREEN_W, SCREEN_H

class Camera:
    def __init__(self, level_width, level_height):
        self._offset  = pygame.math.Vector2(0, 0)
        self.offset   = pygame.math.Vector2(0, 0)
        self.level_w  = level_width
        self.level_h  = level_height
        self._target  = pygame.math.Vector2(0, 0)
        self.zoom     = 1.0
        self._target_zoom = 1.0
        self._shake   = (0, 0)

    def follow(self, midpoint_x, midpoint_y, dt: float):
        render_w = int(SCREEN_W / self.zoom)
        render_h = int(SCREEN_H / self.zoom)

        target_x = midpoint_x - render_w * 0.5
        target_y = midpoint_y - render_h * 0.5

        # No level clamping — camera follows players even off-screen
        # (Smash Bros camera follows the action, not the stage)

        self._target.x += (target_x - self._target.x) * 0.15
        self._target.y += (target_y - self._target.y) * 0.12

        self.offset.x = self._target.x + self._shake[0]
        self.offset.y = self._target.y + self._shake[1]

    def set_zoom(self, zoom_target: float):
        self._target_zoom = max(0.3, min(2.0, zoom_target))
        self.zoom += (self._target_zoom - self.zoom) * 0.04

    def get_render_size(self) -> tuple:
        return (int(SCREEN_W / self.zoom), int(SCREEN_H / self.zoom))

    def set_shake(self, shake_offset):
        self._shake = shake_offset
