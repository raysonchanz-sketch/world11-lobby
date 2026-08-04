import pygame

class SceneManager:
    def __init__(self):
        self.scenes  = {}
        self.current = None

    def add(self, name: str, scene):
        self.scenes[name] = scene

    def switch(self, name: str):
        self.current = self.scenes[name]
        self.current.on_enter()

    def update(self, dt):
        if self.current:
            next_scene = self.current.update(dt)
            if next_scene:
                self.switch(next_scene)

    def draw(self, surface):
        if self.current:
            self.current.draw(surface)

class Scene:
    def on_enter(self):
        pass

    def update(self, dt):
        return None

    def draw(self, surface):
        pass
