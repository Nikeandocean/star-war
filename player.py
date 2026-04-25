import pygame
import math

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, RED, GREEN, YELLOW, CYAN,
    ORANGE, SILVER, NEON_BLUE, LIGHT_YELLOW, font_small, font_tiny,
)
from effects import EngineFlame, Particle


class Player(pygame.sprite.Sprite):
    """Player spaceship with detailed graphics"""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 100), pygame.SRCALPHA)
        self.original_image = None
        self.draw_ship()
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20

        # Movement
        self.speed = 8
        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = 0.92
        self.acceleration = 0.8

        # Stats
        self.health = 100
        self.max_health = 100
        self.shield = 100
        self.max_shield = 100
        self.shield_regen = 0.1
        self.energy = 100
        self.max_energy = 100

        # Combat
        self.invincible = False
        self.invincible_timer = 0
        self.shoot_delay = 120
        self.last_shot = pygame.time.get_ticks()
        self.power_level = 1
        self.power_timer = 0
        self.bomb_count = 3
        self.missile_count = 5

        # Visual effects
        self.engine_flames = [EngineFlame(25, 85), EngineFlame(55, 85)]
        self.bank_angle = 0
        self.hit_effect_timer = 0

    def draw_ship(self):
        img = self.image

        body_points = [
            (40, 0), (15, 40), (10, 70), (20, 90), (40, 85),
            (60, 90), (70, 70), (65, 40),
        ]
        pygame.draw.polygon(img, (50, 80, 120), body_points)

        cockpit_pts = [(40, 15), (35, 25), (35, 40), (45, 40), (45, 25)]
        pygame.draw.polygon(img, NEON_BLUE, cockpit_pts)
        pygame.draw.ellipse(img, (100, 200, 255), (32, 18, 16, 20))

        wing_l = [(15, 40), (0, 55), (5, 65), (20, 55)]
        wing_r = [(65, 40), (80, 55), (75, 65), (60, 55)]
        pygame.draw.polygon(img, (70, 100, 140), wing_l)
        pygame.draw.polygon(img, (70, 100, 140), wing_r)

        pygame.draw.line(img, SILVER, (8, 58), (18, 50), 2)
        pygame.draw.line(img, SILVER, (72, 58), (62, 50), 2)

        pygame.draw.ellipse(img, (40, 40, 40), (18, 72, 12, 15))
        pygame.draw.ellipse(img, (40, 40, 40), (50, 72, 12, 15))

        pygame.draw.ellipse(img, (100, 50, 0), (20, 85, 8, 10))
        pygame.draw.ellipse(img, (100, 50, 0), (52, 85, 8, 10))

        pygame.draw.circle(img, RED, (10, 60), 3)
        pygame.draw.circle(img, RED, (70, 60), 3)

        pygame.draw.polygon(img, SILVER, [(40, 0), (38, 10), (42, 10)])

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.velocity_x -= self.acceleration
            self.bank_angle = max(-30, self.bank_angle - 3)
        elif keys[pygame.K_RIGHT]:
            self.velocity_x += self.acceleration
            self.bank_angle = min(30, self.bank_angle + 3)
        else:
            self.bank_angle *= 0.9

        if keys[pygame.K_UP]:
            self.velocity_y -= self.acceleration
        if keys[pygame.K_DOWN]:
            self.velocity_y += self.acceleration

        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.velocity_x = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity_y = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.velocity_y = 0

        if self.shield < self.max_shield:
            self.shield += self.shield_regen

        if self.energy < self.max_energy:
            self.energy += 0.3

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        if pygame.time.get_ticks() - self.power_timer > 15000:
            self.power_level = 1

        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= 1

        for flame in self.engine_flames:
            flame.update()

    def take_damage(self, damage):
        """Apply damage to shield first, then overflow to health.
        Returns True if player died."""
        shield_absorbed = min(damage, self.shield)
        self.shield -= shield_absorbed
        self.health -= (damage - shield_absorbed)
        return self.health <= 0

    def shoot(self):
        from weapons import Bullet
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and self.energy >= 2:
            self.last_shot = now
            self.energy -= 2

            if self.power_level == 1:
                return [Bullet(self.rect.centerx, self.rect.top, 0)]
            elif self.power_level == 2:
                return [Bullet(self.rect.left + 15, self.rect.top, 0),
                       Bullet(self.rect.right - 15, self.rect.top, 0)]
            else:
                bullets = [Bullet(self.rect.centerx, self.rect.top, 0)]
                bullets.append(Bullet(self.rect.left + 10, self.rect.top + 10, -15))
                bullets.append(Bullet(self.rect.right - 10, self.rect.top + 10, 15))
                return bullets
        return []

    def shoot_missile(self, target=None):
        from weapons import Missile
        if self.missile_count > 0 and self.energy >= 20:
            self.missile_count -= 1
            self.energy -= 20
            return Missile(self.rect.centerx, self.rect.top, target)
        return None

    def drop_bomb(self):
        from weapons import Bomb
        if self.bomb_count > 0:
            self.bomb_count -= 1
            return Bomb(self.rect.centerx, self.rect.centery)
        return None

    def draw_health(self, surface):
        bar_x, bar_y = 15, 15
        bar_width, bar_height = 200, 25

        pygame.draw.rect(surface, (30, 30, 30),
                        (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), border_radius=5)
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=3)

        health_width = int(bar_width * (self.health / self.max_health))
        if health_width > 0:
            color = GREEN if self.health > 50 else (YELLOW if self.health > 25 else RED)
            pygame.draw.rect(surface, color, (bar_x, bar_y, health_width, bar_height), border_radius=3)

        pygame.draw.rect(surface, WHITE,
                        (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2, border_radius=5)

        health_text = font_small.render(f"HP: {int(self.health)}", True, WHITE)
        surface.blit(health_text, (bar_x + 10, bar_y + 3))

        shield_y = bar_y + 35
        pygame.draw.rect(surface, (30, 30, 30),
                        (bar_x - 2, shield_y - 2, bar_width + 4, 18), border_radius=3)
        shield_width = int(bar_width * (self.shield / self.max_shield))
        if shield_width > 0:
            pygame.draw.rect(surface, CYAN, (bar_x, shield_y, shield_width, 18), border_radius=3)
        pygame.draw.rect(surface, CYAN, (bar_x - 2, shield_y - 2, bar_width + 4, 18), 2, border_radius=3)

        energy_y = shield_y + 25
        pygame.draw.rect(surface, (30, 30, 30),
                        (bar_x - 2, energy_y - 2, bar_width + 4, 18), border_radius=3)
        energy_width = int(bar_width * (self.energy / self.max_energy))
        if energy_width > 0:
            pygame.draw.rect(surface, YELLOW, (bar_x, energy_y, energy_width, 18), border_radius=3)
        pygame.draw.rect(surface, YELLOW, (bar_x - 2, energy_y - 2, bar_width + 4, 18), 2, border_radius=3)

        surface.blit(font_tiny.render(f"Bombs: {self.bomb_count}", True, ORANGE), (bar_x, energy_y + 28))
        surface.blit(font_tiny.render(f"Missiles: {self.missile_count}", True, RED), (bar_x + 100, energy_y + 28))

    def draw_hit_effect(self, surface):
        if self.hit_effect_timer > 0:
            alpha = min(255, self.hit_effect_timer * 20)
            flash = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha // 2))
            surface.blit(flash, self.rect.topleft)


