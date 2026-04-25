import random
import math
import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class Star:
    """Parallax background stars with multiple layers"""
    def __init__(self, layer=0):
        self.layer = layer
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = (layer + 1) * 0.5 + random.random() * 2
        self.size = layer + 1
        self.brightness = random.randint(150, 255)
        self.twinkle_speed = random.uniform(0.02, 0.05)
        self.twinkle_offset = random.random() * math.pi * 2

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface, time_offset=0):
        twinkle = math.sin(time_offset * self.twinkle_speed + self.twinkle_offset) * 30
        brightness = max(100, min(255, self.brightness + twinkle))
        color = (int(brightness), int(brightness), int(brightness))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


class Nebula:
    """Background nebula clouds"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.width = random.randint(100, 300)
        self.height = random.randint(50, 150)
        self.speed = random.uniform(0.1, 0.3)
        self.color = random.choice([
            (50, 0, 100),    # Purple
            (0, 50, 100),    # Dark blue
            (100, 0, 50),    # Dark red
            (0, 100, 50),    # Dark green
        ])
        self.alpha = random.randint(30, 60)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT + 100:
            self.y = -100
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        nebula_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(5):
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            radius = min(self.width, self.height) // 2 + random.randint(-10, 10)
            color = (*self.color, self.alpha // 5)
            pygame.draw.circle(nebula_surface, color,
                             (self.width // 2 + offset_x, self.height // 2 + offset_y), radius)
        nebula_surface.set_alpha(self.alpha)
        surface.blit(nebula_surface, (self.x, self.y))