import random
import math
import pygame

from config import (
    SCREEN_HEIGHT, RED, ORANGE, YELLOW, WHITE, CYAN, LIGHT_YELLOW,
)


class Particle:
    """Particle effects for explosions, thrusters, etc."""
    def __init__(self, x, y, color, speed, lifetime, size=3, angle=None):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        if angle is None:
            self.angle = random.uniform(0, math.pi * 2)
        else:
            self.angle = angle + random.uniform(-0.3, 0.3)
        self.speed = random.uniform(speed * 0.5, speed * 1.5)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        self.gravity = 0
        self.friction = 0.98
        self.fade_rate = 255 / lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.friction
        self.vy *= self.friction
        self.vy += self.gravity
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, surface):
        if self.size > 1:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, self.size))


class EngineFlame:
    """Engine flame effect for player ship"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_height = random.randint(20, 40)
        self.width = random.randint(8, 15)
        self.lifetime = random.randint(3, 8)
        self.max_lifetime = self.lifetime

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.lifetime = random.randint(3, 8)
            self.base_height = random.randint(20, 40)
        return True

    def draw(self, surface):
        flicker = random.randint(-3, 3)
        height = self.base_height + flicker

        points = [
            (self.x - self.width // 2, self.y),
            (self.x, self.y + height),
            (self.x + self.width // 2, self.y),
        ]
        pygame.draw.polygon(surface, ORANGE, points)

        inner_points = [
            (self.x - self.width // 4, self.y),
            (self.x, self.y + height * 0.7),
            (self.x + self.width // 4, self.y),
        ]
        pygame.draw.polygon(surface, YELLOW, inner_points)


class Explosion:
    """Detailed explosion effect"""
    def __init__(self, x, y, size=40, damage=0, is_bomb=False):
        self.x = x
        self.y = y
        self.size = size
        self.max_size = size
        self.frame = 0
        self.max_frames = 25
        self.damage = damage
        self.is_bomb = is_bomb
        self.particles = []
        self.shockwave = 0
        self.active = True

        num_particles = size * 2
        for _ in range(num_particles):
            color = random.choice([RED, ORANGE, YELLOW, WHITE])
            if is_bomb:
                color = random.choice([RED, ORANGE, WHITE, (100, 100, 100)])
            speed = random.uniform(3, 10)
            lifetime = random.randint(20, 40)
            p_size = random.randint(2, 6)
            self.particles.append(Particle(x, y, color, speed, lifetime, p_size))

    def update(self):
        self.frame += 1
        self.shockwave = self.frame * 3

        self.particles = [p for p in self.particles if p.update()]

        if self.frame >= self.max_frames and not self.particles:
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active:
            return

        # Shockwave
        if self.frame < 10:
            alpha = int(200 * (1 - self.frame / 10))
            shock_surf = pygame.Surface((self.shockwave * 2, self.shockwave * 2), pygame.SRCALPHA)
            shock_surf.set_alpha(alpha)
            pygame.draw.circle(shock_surf, (255, 255, 200),
                             (self.shockwave, self.shockwave), self.shockwave)
            surface.blit(shock_surf, (self.x - self.shockwave, self.y - self.shockwave))

        # Main explosion body
        radius = int(self.size * (self.frame / self.max_frames) * 2)
        if radius > 0:
            alpha = int(255 * (1 - self.frame / self.max_frames))

            outer_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            outer_surf.set_alpha(alpha)
            pygame.draw.circle(outer_surf, (255, 100, 0), (radius, radius), radius)
            surface.blit(outer_surf, (self.x - radius, self.y - radius))

            inner_radius = radius // 2
            if inner_radius > 0:
                inner_surf = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
                inner_surf.set_alpha(alpha)
                pygame.draw.circle(inner_surf, (255, 255, 100),
                                 (inner_radius, inner_radius), inner_radius)
                surface.blit(inner_surf, (self.x - inner_radius, self.y - inner_radius))

        for p in self.particles:
            p.draw(surface)

    def get_damage_rect(self):
        if self.frame == 5:
            return pygame.Rect(self.x - self.size, self.y - self.size,
                             self.size * 2, self.size * 2)
        return None


class LaserBeam:
    """Boss super laser attack"""
    def __init__(self, x, y, duration=100):
        self.x = x
        self.y = y
        self.width = 30
        self.duration = duration
        self.charge_time = 60
        self.fire_time = duration
        self.cooldown = 30
        self.state = 'charging'
        self.particles = []
        self.damage = 2
        self.active = True

    def update(self):
        if self.state == 'charging':
            self.charge_time -= 1
            if self.charge_time <= 0:
                self.state = 'firing'
        elif self.state == 'firing':
            self.fire_time -= 1
            for _ in range(5):
                self.particles.append(Particle(
                    self.x + random.randint(-15, 15),
                    random.randint(self.y, SCREEN_HEIGHT),
                    (200, 100, 0), 5, 10, 5
                ))
            self.particles = [p for p in self.particles if p.update()]

            if self.fire_time <= 0:
                self.state = 'cooldown'
        else:
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.active = False

        return self.active

    def draw(self, surface):
        if self.state == 'charging':
            for i in range(3):
                offset = math.sin(pygame.time.get_ticks() * 0.1 + i) * 10
                pygame.draw.line(surface, (255, 100, 0),
                               (self.x + offset, self.y),
                               (self.x + offset, self.y + 50), 5)

        elif self.state == 'firing':
            pygame.draw.rect(surface, (255, 255, 200),
                           (self.x - self.width // 2, self.y,
                            self.width, SCREEN_HEIGHT - self.y))
            pygame.draw.rect(surface, (255, 150, 50),
                           (self.x - self.width // 4, self.y,
                            self.width // 2, SCREEN_HEIGHT - self.y))

            for p in self.particles:
                p.draw(surface)

    def get_damage_rect(self):
        if self.state == 'firing':
            return pygame.Rect(self.x - self.width // 2, self.y,
                             self.width, SCREEN_HEIGHT - self.y)
        return None