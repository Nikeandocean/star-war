import random
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, ORANGE, YELLOW, GREEN, CYAN,
    PURPLE, WHITE, GOLD, NEON_GREEN, NEON_PINK, DARK_RED, SILVER,
    font_small,
)


class Enemy(pygame.sprite.Sprite):
    """Enemy spaceship with varied types"""
    def __init__(self, enemy_type=0):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.draw_enemy()
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(0, 100)

        self.start_x = self.rect.x
        self.move_pattern = random.randint(0, 3)
        self.move_timer = 0
        self.move_amplitude = random.randint(30, 80)
        self.move_frequency = random.uniform(0.02, 0.05)

        self.speed_x = random.randint(-1, 1)
        self.speed_y = random.randint(2, 5)
        self.health = 50 + enemy_type * 30
        self.max_health = self.health
        self.score_value = 100 + enemy_type * 200
        self.shoot_delay = max(800, 2000 - enemy_type * 400)
        self.last_shot = pygame.time.get_ticks()
        self.hit_flash = 0

    def draw_enemy(self):
        img = self.image

        if self.enemy_type == 0:
            # TIE Fighter
            pygame.draw.circle(img, (80, 80, 80), (30, 30), 18)
            pygame.draw.circle(img, (100, 100, 100), (30, 30), 15)
            pygame.draw.circle(img, DARK_RED, (30, 30), 8)
            pygame.draw.polygon(img, (120, 120, 120), [(10, 5), (10, 55), (5, 55), (5, 5)])
            pygame.draw.polygon(img, (120, 120, 120), [(50, 5), (50, 55), (55, 55), (55, 5)])
            for i in range(5):
                pygame.draw.line(img, (80, 80, 80), (7, 10 + i*10), (13, 10 + i*10), 2)
                pygame.draw.line(img, (80, 80, 80), (47, 10 + i*10), (53, 10 + i*10), 2)
            pygame.draw.line(img, (100, 100, 100), (30, 12), (30, 5), 4)
            pygame.draw.line(img, (100, 100, 100), (30, 48), (30, 55), 4)

        elif self.enemy_type == 1:
            # Interceptor
            body_pts = [(30, 0), (15, 20), (10, 50), (30, 60), (50, 50), (45, 20)]
            pygame.draw.polygon(img, (100, 80, 60), body_pts)
            pygame.draw.polygon(img, (139, 69, 19), [(15, 20), (0, 35), (5, 45), (20, 35)])
            pygame.draw.polygon(img, (139, 69, 19), [(45, 20), (60, 35), (55, 45), (40, 35)])
            pygame.draw.ellipse(img, NEON_GREEN, (25, 25, 10, 15))
            pygame.draw.ellipse(img, ORANGE, (25, 50, 10, 10))

        elif self.enemy_type == 2:
            # Bomber
            pygame.draw.ellipse(img, (60, 60, 80), (10, 10, 40, 45))
            pygame.draw.polygon(img, (80, 80, 100), [(30, 5), (5, 25), (10, 35), (30, 20)])
            pygame.draw.polygon(img, (80, 80, 100), [(30, 5), (55, 25), (50, 35), (30, 20)])
            pygame.draw.ellipse(img, (40, 40, 40), (25, 30, 10, 20))
            pygame.draw.circle(img, RED, (30, 20), 6)

        else:
            # Elite
            elite_pts = [(30, 0), (10, 30), (0, 50), (15, 55), (30, 60),
                        (45, 55), (60, 50), (50, 30)]
            pygame.draw.polygon(img, (50, 30, 80), elite_pts)
            inner_pts = [(30, 10), (20, 35), (30, 50), (40, 35)]
            pygame.draw.polygon(img, (80, 50, 120), inner_pts)
            pygame.draw.circle(img, PURPLE, (30, 35), 8)
            pygame.draw.circle(img, NEON_PINK, (30, 35), 4)

    def update(self):
        # Restore original image before applying any flash effect
        if self.original_image:
            self.image = self.original_image.copy()

        self.move_timer += 1

        if self.move_pattern == 0:
            self.rect.y += self.speed_y
        elif self.move_pattern == 1:
            self.rect.y += self.speed_y
            self.rect.x = self.start_x + math.sin(self.move_timer * self.move_frequency) * self.move_amplitude
        elif self.move_pattern == 2:
            self.rect.y += self.speed_y
            if self.move_timer % 60 < 30:
                self.rect.x += 2
            else:
                self.rect.x -= 2
        else:
            self.rect.y += self.speed_y
            self.rect.x = self.start_x + math.cos(self.move_timer * 0.05) * self.move_amplitude

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # Apply hit flash on the fresh copy (won't accumulate)
        if self.hit_flash > 0:
            self.hit_flash -= 1
            if self.hit_flash > 0:
                self.image.fill((255, 255, 255, 100), special_flags=pygame.BLEND_ADD)

    def can_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            return True
        return False

    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 3
        return self.health <= 0


class EnemyBullet(pygame.sprite.Sprite):
    """Enemy bullet with varied types"""
    def __init__(self, x, y, angle_x=0, speed=6, color=RED, damage=15):
        super().__init__()
        self.image = pygame.Surface((10, 20), pygame.SRCALPHA)
        self.color = color

        if color == PURPLE:
            pygame.draw.circle(self.image, color, (5, 10), 8)
            pygame.draw.circle(self.image, (150, 50, 150), (5, 10), 5)
        elif color == CYAN:
            pygame.draw.ellipse(self.image, color, (0, 0, 10, 20))
            pygame.draw.ellipse(self.image, WHITE, (2, 5, 6, 10))
        else:
            pygame.draw.ellipse(self.image, color, (0, 0, 10, 20))
            pygame.draw.ellipse(self.image, (255, 100, 100), (2, 5, 6, 10))

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.angle_x = angle_x
        self.speed = speed
        self.damage = damage

    def update(self):
        self.rect.y += self.speed
        self.rect.x += self.angle_x

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Boss:
    """Boss ship with multiple phases and attacks"""
    def __init__(self):
        self.width = 200
        self.height = 150
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - self.width // 2, -self.height,
                               self.width, self.height)

        self.health = 1000
        self.max_health = 1000
        self.phase = 1
        self.score_value = 5000

        self.target_x = SCREEN_WIDTH // 2 - self.width // 2
        self.target_y = 50
        self.speed = 2
        self.move_pattern = 0
        self.move_timer = 0

        self.attack_timer = 0
        self.attack_pattern = 0
        self.shoot_delay = 1000

        self.engine_glow = 0
        self.hit_flash = 0
        self.draw_boss()
        self.original_image = self.image.copy()

    def draw_boss(self):
        img = self.image

        hull_pts = [(100, 0), (20, 50), (10, 120), (50, 140), (150, 140),
                    (190, 120), (180, 50)]
        pygame.draw.polygon(img, (60, 60, 80), hull_pts)

        inner_pts = [(100, 20), (40, 60), (40, 110), (100, 125),
                     (160, 110), (160, 60)]
        pygame.draw.polygon(img, (80, 80, 100), inner_pts)

        pygame.draw.polygon(img, (100, 100, 120), [(100, 30), (70, 60), (130, 60)])
        pygame.draw.circle(img, RED, (100, 50), 15)
        pygame.draw.circle(img, (200, 50, 50), (100, 50), 8)

        pygame.draw.ellipse(img, (70, 70, 90), (20, 100, 40, 40))
        pygame.draw.ellipse(img, (70, 70, 90), (140, 100, 40, 40))

        glow_intensity = 100 + int(math.sin(pygame.time.get_ticks() * 0.01) * 50)
        pygame.draw.ellipse(img, (glow_intensity, 50, 0), (30, 125, 20, 20))
        pygame.draw.ellipse(img, (glow_intensity, 50, 0), (150, 125, 20, 20))
        pygame.draw.ellipse(img, (255, 200, 0), (35, 130, 10, 10))
        pygame.draw.ellipse(img, (255, 200, 0), (155, 130, 10, 10))

        pygame.draw.circle(img, (50, 50, 50), (30, 80), 8)
        pygame.draw.circle(img, (50, 50, 50), (170, 80), 8)
        pygame.draw.circle(img, (50, 50, 50), (50, 130), 10)
        pygame.draw.circle(img, (50, 50, 50), (150, 130), 10)

        pygame.draw.rect(img, (70, 70, 90), (0, 70, 25, 30))
        pygame.draw.rect(img, (70, 70, 90), (175, 70, 25, 30))

    def update(self, player=None):
        # Restore original image before applying flash
        self.image = self.original_image.copy()

        self.move_timer += 1

        if self.rect.y < self.target_y:
            self.rect.y += self.speed
        else:
            if self.move_pattern == 0:
                self.rect.x += math.sin(self.move_timer * 0.02) * 3
            elif self.move_pattern == 1:
                self.rect.x = self.target_x + math.cos(self.move_timer * 0.01) * 200
            else:
                if self.move_timer % 120 < 60:
                    self.rect.x += 2
                else:
                    self.rect.x -= 2

        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Apply hit flash on fresh copy (won't accumulate)
        if self.hit_flash > 0:
            self.hit_flash -= 1
            if self.hit_flash % 2 == 0:
                self.image.fill((100, 100, 100, 50), special_flags=pygame.BLEND_ADD)

        if self.health < self.max_health * 0.3:
            self.phase = 3
            self.shoot_delay = 400
        elif self.health < self.max_health * 0.6:
            self.phase = 2
            self.shoot_delay = 600

        self.attack_timer += 1

    def can_attack(self):
        if self.attack_timer >= self.shoot_delay:
            self.attack_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 4
            return True
        return False

    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 5
        return self.health <= 0

    def draw_health_bar(self, surface):
        bar_width = 400
        bar_height = 25
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 10

        pygame.draw.rect(surface, (40, 20, 20),
                        (bar_x - 3, bar_y - 3, bar_width + 6, bar_height + 6))

        health_pct = self.health / self.max_health
        if health_pct > 0.6:
            color = GREEN
        elif health_pct > 0.3:
            color = YELLOW
        else:
            color = RED

        pygame.draw.rect(surface, color,
                        (bar_x, bar_y, int(bar_width * health_pct), bar_height))

        pygame.draw.rect(surface, WHITE,
                        (bar_x - 3, bar_y - 3, bar_width + 6, bar_height + 6), 3)

        label = font_small.render("BOSS", True, WHITE)
        surface.blit(label, (bar_x + bar_width // 2 - label.get_width() // 2, bar_y + 3))