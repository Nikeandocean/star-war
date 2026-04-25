import random
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN, YELLOW, ORANGE, CYAN,
    PURPLE, WHITE, PINK, LIGHT_YELLOW, GOLD, SILVER,
)
from effects import Particle


class Bullet(pygame.sprite.Sprite):
    """Player bullet with trail effect"""
    def __init__(self, x, y, angle=0):
        super().__init__()
        self.image = pygame.Surface((20, 25), pygame.SRCALPHA)

        pygame.draw.ellipse(self.image, CYAN, (0, 0, 20, 25))
        pygame.draw.ellipse(self.image, WHITE, (5, 5, 10, 15))
        pygame.draw.ellipse(self.image, LIGHT_YELLOW, (8, 8, 4, 10))

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -12
        self.angle = angle
        self.damage = 15
        self.trail_particles = []

    def update(self):
        self.rect.y += self.speed
        self.rect.x += self.angle

        if random.random() < 0.5:
            self.trail_particles.append(
                Particle(self.rect.centerx, self.rect.bottom, CYAN, 1, 10, 2)
            )

        self.trail_particles = [p for p in self.trail_particles if p.update()]

        if self.rect.bottom < 0:
            self.kill()

    def draw(self, surface):
        for p in self.trail_particles:
            p.draw(surface)
        surface.blit(self.image, self.rect)


class Missile(pygame.sprite.Sprite):
    """Homing missile"""
    def __init__(self, x, y, target=None):
        super().__init__()
        self.image = pygame.Surface((15, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (100, 100, 100), (0, 0, 15, 30))
        pygame.draw.ellipse(self.image, RED, (2, 5, 11, 20))
        pygame.draw.polygon(self.image, RED, [(7, 0), (3, 10), (12, 10)])

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 8
        self.target = target
        self.turn_rate = 0.15
        self.vx = 0
        self.lifetime = 300
        self.damage = 100
        self.trail = []

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        if self.target and self.target.alive():
            dx = self.target.rect.centerx - self.rect.centerx
            self.vx += dx * 0.01
            self.vx = max(-5, min(5, self.vx))

        self.rect.x += self.vx
        self.rect.y -= self.speed

        self.trail.append(Particle(self.rect.centerx, self.rect.bottom + 5,
                                  ORANGE, 2, 15, 4, math.pi/2))
        self.trail = [p for p in self.trail if p.update()]

        if self.rect.bottom < 0:
            self.kill()

    def draw(self, surface):
        for p in self.trail:
            p.draw(surface)
        surface.blit(self.image, self.rect)


class Bomb(pygame.sprite.Sprite):
    """Area damage bomb that detonates above the player"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 25), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (50, 50, 50), (0, 0, 20, 25))
        pygame.draw.circle(self.image, RED, (10, 8), 5)

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.spawn_y = y
        self.speed = -8
        self.damage = 150
        self.blast_radius = 200
        self.exploded = False

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def should_explode(self):
        """Detonate after moving up a short distance."""
        return self.spawn_y - self.rect.top > 50

    def explode(self):
        from effects import Explosion
        return Explosion(self.rect.centerx, self.rect.centery, self.blast_radius,
                        damage=self.damage, is_bomb=True)


class PowerUp(pygame.sprite.Sprite):
    """Power-up items with glow effect"""
    def __init__(self, center):
        super().__init__()
        self.type = random.choices(
            ['health', 'shield', 'power', 'bomb', 'missile', 'energy'],
            weights=[20, 20, 15, 10, 10, 25]
        )[0]
        self.image = pygame.Surface((35, 35), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speed = 2
        self.angle = 0
        self.glow_phase = 0
        self.draw_powerup()

    def draw_powerup(self):
        colors = {
            'health': (RED, WHITE),
            'shield': (CYAN, WHITE),
            'power': (YELLOW, ORANGE),
            'bomb': (ORANGE, RED),
            'missile': (PURPLE, PINK),
            'energy': (GREEN, LIGHT_YELLOW),
        }
        main_color, accent_color = colors.get(self.type, (WHITE, WHITE))

        glow_size = 35 + int(math.sin(self.glow_phase) * 5)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_surf.set_alpha(50)
        pygame.draw.circle(glow_surf, main_color[:3],
                          (glow_size // 2, glow_size // 2), glow_size // 2)
        self.image.blit(glow_surf, (17 - glow_size // 2, 17 - glow_size // 2))

        if self.type == 'health':
            pygame.draw.rect(self.image, main_color, (8, 8, 19, 19), border_radius=5)
            pygame.draw.line(self.image, accent_color, (17, 11), (17, 24), 3)
            pygame.draw.line(self.image, accent_color, (11, 17), (23, 17), 3)
        elif self.type == 'shield':
            pygame.draw.circle(self.image, main_color, (17, 17), 12)
            pygame.draw.polygon(self.image, accent_color, [(17, 5), (5, 28), (29, 28)], 2)
        elif self.type == 'power':
            pts = [(17, 3), (8, 15), (15, 15), (10, 30), (25, 18), (18, 18)]
            pygame.draw.polygon(self.image, main_color, pts)
        elif self.type == 'bomb':
            pygame.draw.circle(self.image, main_color, (17, 17), 12)
            pygame.draw.circle(self.image, accent_color, (17, 17), 6)
        elif self.type == 'missile':
            pygame.draw.ellipse(self.image, main_color, (7, 5, 21, 25))
            pygame.draw.polygon(self.image, accent_color, [(17, 5), (10, 15), (24, 15)])
        else:
            pygame.draw.polygon(self.image, main_color, [(17, 5), (5, 17), (17, 29), (29, 17)])
            pygame.draw.circle(self.image, accent_color, (17, 17), 8)

    def update(self):
        self.rect.y += self.speed
        self.angle += 0.05
        self.glow_phase += 0.1
        self.rect.x += math.sin(self.angle) * 1.5
        self.draw_powerup()

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()