import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK


# Star color tints (subtle variations)
STAR_COLORS = [
    (255, 255, 255),   # pure white
    (200, 220, 255),   # blue-white
    (255, 240, 200),   # warm white
    (255, 255, 220),   # yellow-white
    (220, 200, 255),   # violet-white
    (200, 255, 255),   # cyan-white
]

# Nebula cloud colors (richer palette)
NEBULA_COLORS = [
    (20, 0, 60),       # deep purple
    (0, 20, 80),       # deep blue
    (60, 0, 80),       # violet
    (0, 60, 80),       # teal-blue
    (80, 0, 40),       # dark magenta
    (40, 10, 60),      # plum
    (10, 40, 70),      # ocean blue
    (50, 0, 50),       # dark purple
    (0, 30, 50),       # midnight teal
]


class Star:
    """A single parallax star with twinkling and color tint."""

    # Speed/size by layer for external callers (menu_state)
    LAYER_SPEEDS = {0: (0.3, 0.8), 1: (1.2, 2.0), 2: (2.5, 4.0)}
    LAYER_SIZES = {0: [1], 1: [1, 1, 2], 2: [1, 2, 2]}

    def __init__(self, layer=None):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        if layer is not None:
            lo, hi = self.LAYER_SPEEDS.get(layer, (0.5, 1.0))
            self.speed = random.uniform(lo, hi)
            self.size = random.choice(self.LAYER_SIZES.get(layer, [1]))
        else:
            self.speed = 0.5
            self.size = 1
        self.base_color = random.choice(STAR_COLORS)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, math.pi * 2)
        self.brightness_base = random.uniform(0.4, 1.0)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface, time):
        # Twinkle: oscillate brightness
        brightness = self.brightness_base + (1.0 - self.brightness_base) * (
            0.5 + 0.5 * math.sin(time * self.twinkle_speed + self.twinkle_offset)
        )
        r = int(self.base_color[0] * brightness)
        g = int(self.base_color[1] * brightness)
        b = int(self.base_color[2] * brightness)
        color = (min(r, 255), min(g, 255), min(b, 255))

        if self.size <= 1:
            surface.set_at((int(self.x), int(self.y)), color)
        else:
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


class ShootingStar:
    """A fast-moving bright streak across the screen."""

    def __init__(self):
        # Start from top-left area, move diagonally
        self.x = random.randint(SCREEN_WIDTH // 4, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT // 4)
        angle = random.uniform(0.6, 1.0)  # ~35-57 degrees
        speed = random.uniform(12, 20)
        self.vx = -speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.life = random.randint(15, 30)
        self.max_life = self.life
        self.tail_length = random.randint(40, 80)
        self.color = random.choice([
            (255, 255, 255),
            (255, 255, 200),
            (200, 220, 255),
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0 and self.x > -50 and self.y < SCREEN_HEIGHT + 50

    def draw(self, surface):
        alpha = self.life / self.max_life
        # Draw tail as a line with fading alpha
        tail_x = self.x - self.vx * (self.tail_length / abs(self.vx)) * 0.5
        tail_y = self.y - self.vy * (self.tail_length / abs(self.vx)) * 0.5

        # Draw multiple segments for gradient tail
        segments = 6
        for i in range(segments):
            t = i / segments
            sx = self.x * (1 - t) + tail_x * t
            sy = self.y * (1 - t) + tail_y * t
            seg_alpha = int(255 * alpha * (1 - t * 0.8))
            seg_color = (
                min(int(self.color[0] * (1 - t * 0.3)), 255),
                min(int(self.color[1] * (1 - t * 0.3)), 255),
                min(int(self.color[2] * (1 - t * 0.3)), 255),
            )
            radius = max(1, int(2 * (1 - t * 0.7)))
            # Use a temporary surface for alpha blending
            temp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp, (*seg_color, seg_alpha), (radius, radius), radius)
            surface.blit(temp, (int(sx) - radius, int(sy) - radius))

        # Bright head
        head_alpha = int(255 * alpha)
        head_radius = 3
        temp = pygame.Surface((head_radius * 4, head_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(temp, (255, 255, 255, head_alpha), (head_radius * 2, head_radius * 2), head_radius)
        # Glow
        pygame.draw.circle(temp, (255, 255, 200, head_alpha // 3), (head_radius * 2, head_radius * 2), head_radius * 2)
        surface.blit(temp, (int(self.x) - head_radius * 2, int(self.y) - head_radius * 2))


class DistantPlanet:
    """A large, faint planet scrolling slowly in the background."""

    def __init__(self):
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = -100
        self.speed = random.uniform(0.2, 0.5)
        self.radius = random.randint(60, 120)
        self.color = random.choice([
            (60, 40, 80),    # purple
            (40, 60, 90),    # blue-gray
            (80, 60, 40),    # brown
            (50, 70, 60),    # teal-gray
            (70, 50, 60),    # dusty rose
        ])
        self.alpha = random.randint(25, 45)
        self._surface = self._render()

    def _render(self):
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        cx, cy = self.radius, self.radius
        # Gradient: solid center → transparent edge
        for r in range(self.radius, 0, -1):
            t = r / self.radius
            a = int(self.alpha * (1 - t * t))  # quadratic falloff
            c = (
                int(self.color[0] * (1 - t * 0.3)),
                int(self.color[1] * (1 - t * 0.3)),
                int(self.color[2] * (1 - t * 0.3)),
                a,
            )
            pygame.draw.circle(surf, c, (cx, cy), r)
        return surf

    def update(self):
        self.y += self.speed

    @property
    def alive(self):
        return self.y < SCREEN_HEIGHT + self.radius

    def draw(self, surface):
        surface.blit(self._surface, (int(self.x - self.radius), int(self.y - self.radius)))


class Nebula:
    """Pre-rendered static nebula with drifting animation."""

    def __init__(self):
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._render()
        self.drift_offset = 0.0
        self.drift_speed = 0.15  # pixels per frame
        self.pulse_offset = 0.0
        # Second surface for seamless horizontal wrap
        self.surface_copy = self.surface.copy()

    def _render(self):
        """Generate random nebula clouds once."""
        # Deep space base
        self.surface.fill((5, 2, 15))

        for _ in range(30):
            cx = random.randint(0, SCREEN_WIDTH)
            cy = random.randint(0, SCREEN_HEIGHT)
            radius = random.randint(100, 350)
            color = random.choice(NEBULA_COLORS)
            alpha = random.randint(15, 45)

            temp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            # Draw layered circles for softer edges
            for r in range(radius, radius // 3, -2):
                a = int(alpha * (r / radius) * 0.6)
                c = (
                    max(0, min(color[0] + random.randint(-5, 5), 255)),
                    max(0, min(color[1] + random.randint(-5, 5), 255)),
                    max(0, min(color[2] + random.randint(-5, 5), 255)),
                    a,
                )
                pygame.draw.circle(temp, c, (radius, radius), r)
            self.surface.blit(temp, (cx - radius, cy - radius))

    def update(self):
        self.drift_offset += self.drift_speed
        self.pulse_offset += 0.01

    def draw(self, surface):
        # Slow horizontal drift with seamless wrap
        dx = int(self.drift_offset) % SCREEN_WIDTH
        # Subtle brightness pulse (±8 alpha)
        pulse = int(8 * math.sin(self.pulse_offset))

        # Blit two copies side by side for seamless scrolling
        self.surface_copy.blit(self.surface, (-dx, 0))
        self.surface_copy.blit(self.surface, (SCREEN_WIDTH - dx, 0))

        # Apply brightness pulse
        if pulse > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((pulse, pulse, pulse, pulse))
            self.surface_copy.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        elif pulse < 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((-pulse, -pulse, -pulse, -pulse))
            self.surface_copy.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        surface.blit(self.surface_copy, (0, 0))


class Background:
    """Scrolling starfield with twinkling, shooting stars, nebula, and distant planets."""

    def __init__(self):
        # 3 parallax star layers
        self.stars_slow = []
        self.stars_mid = []
        self.stars_fast = []

        for _ in range(120):
            s = Star()
            s.speed = random.uniform(0.3, 0.8)
            s.size = 1
            self.stars_slow.append(s)

        for _ in range(80):
            s = Star()
            s.speed = random.uniform(1.2, 2.0)
            s.size = random.choice([1, 1, 2])
            self.stars_mid.append(s)

        for _ in range(40):
            s = Star()
            s.speed = random.uniform(2.5, 4.0)
            s.size = random.choice([1, 2, 2])
            self.stars_fast.append(s)

        self.stars = self.stars_slow + self.stars_mid + self.stars_fast

        self.nebula = Nebula()
        self.shooting_stars = []
        self.shoot_timer = random.randint(180, 480)  # frames until next shooting star
        self.planets = []
        self.planet_timer = random.randint(1200, 2400)
        self.time = 0

    def update(self):
        self.time += 1
        for star in self.stars:
            star.update()
        self.nebula.update()

        # Shooting stars
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting_stars.append(ShootingStar())
            self.shoot_timer = random.randint(180, 480)
        for ss in self.shooting_stars:
            ss.update()
        self.shooting_stars = [ss for ss in self.shooting_stars if ss.alive]

        # Distant planets
        self.planet_timer -= 1
        if self.planet_timer <= 0:
            self.planets.append(DistantPlanet())
            self.planet_timer = random.randint(1200, 2400)
        for p in self.planets:
            p.update()
        self.planets = [p for p in self.planets if p.alive]

    def draw(self, surface):
        # Nebula (deepest layer)
        self.nebula.draw(surface)

        # Distant planets (between nebula and stars)
        for p in self.planets:
            p.draw(surface)

        # Stars (all layers, with twinkling)
        for star in self.stars:
            star.draw(surface, self.time)

        # Shooting stars (topmost layer)
        for ss in self.shooting_stars:
            ss.draw(surface)
