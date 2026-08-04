import random

class ScreenShake:
    def __init__(self):
        self.duration  = 0
        self.intensity = 0

    def trigger(self, duration=10, intensity=4):
        self.duration  = duration
        self.intensity = intensity

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            return (random.randint(-self.intensity, self.intensity),
                    random.randint(-self.intensity, self.intensity))
        return (0, 0)
