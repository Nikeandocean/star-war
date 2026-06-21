"""Main menu screen with animated background."""

import math
import os
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED, GREEN, YELLOW, CYAN, GOLD,
    NEON_BLUE, UI_BG, UI_BORDER, UI_HIGHLIGHT, UI_TEXT, UI_TEXT_DIM, USE_OPENGL,
    font_large, font_medium, font_small,
)
from state_machine import State
from background import Star, Nebula
import settings
import audio_manager


class MenuState(State):
    ITEMS = ['Start Game', 'Difficulty', 'Settings', 'Quit']

    def __init__(self, machine):
        super().__init__(machine)
        self.selected = 0
        self.stars = [Star(layer=i % 3) for i in range(100)]
        self.nebulae = [Nebula() for _ in range(3)]
        self.time = 0
        self.ship_y = 0

    def enter(self):
        self.selected = 0
        self.time = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.ITEMS)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.ITEMS)
                elif event.key == pygame.K_RETURN:
                    self._select()
                elif event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _select(self):
        choice = self.ITEMS[self.selected]
        if choice == 'Start Game':
            from states.play_state import PlayState
            self.machine.switch(PlayState(self.machine))
        elif choice == 'Difficulty':
            self._cycle_difficulty()
        elif choice == 'Quit':
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _cycle_difficulty(self):
        current = settings.get('difficulty')
        order = ['Easy', 'Normal', 'Hard']
        idx = order.index(current) if current in order else 1
        settings.set_value('difficulty', order[(idx + 1) % len(order)])
        settings.save()

    def update(self):
        self.time += 1
        for star in self.stars:
            star.update()
        for nebula in self.nebulae:
            nebula.update()
        self.ship_y = math.sin(self.time * 0.03) * 10

    def draw(self, screen):
        screen.fill(BLACK)

        if not USE_OPENGL:
            for star in self.stars:
                star.draw(screen, self.time)
            for nebula in self.nebulae:
                nebula.draw(screen)

        # Title with glow
        glow = int(math.sin(self.time * 0.05) * 30 + 200)
        title = font_large.render("GALAXY BATTLE", True, (glow, glow, 0))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100 + self.ship_y))

        subtitle = font_medium.render("A Space Shooter Epic", True, CYAN)
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 190))

        # Ship preview (simple triangle)
        ship_x = SCREEN_WIDTH // 2
        ship_y = 280 + self.ship_y
        pts = [(ship_x, ship_y - 25), (ship_x - 20, ship_y + 15), (ship_x + 20, ship_y + 15)]
        pygame.draw.polygon(screen, NEON_BLUE, pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)
        # Engine glow
        glow_alpha = int(150 + math.sin(self.time * 0.2) * 50)
        glow_surf = pygame.Surface((20, 15), pygame.SRCALPHA)
        glow_surf.fill((255, 150, 0, glow_alpha))
        screen.blit(glow_surf, (ship_x - 10, ship_y + 15))

        # Menu items
        for i, item in enumerate(self.ITEMS):
            if i == self.selected:
                color = CYAN
                prefix = "> "
                # Highlight bar
                bar_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160, 365 + i * 50, 320, 40)
                pygame.draw.rect(screen, (20, 40, 80), bar_rect, border_radius=5)
                pygame.draw.rect(screen, UI_HIGHLIGHT, bar_rect, 2, border_radius=5)
            else:
                color = UI_TEXT
                prefix = "  "

            text = font_medium.render(f"{prefix}{item}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 370 + i * 50))

        # Difficulty indicator
        diff = settings.get('difficulty')
        diff_colors = {'Easy': GREEN, 'Normal': YELLOW, 'Hard': RED}
        diff_text = font_small.render(f"Difficulty: {diff}", True, diff_colors.get(diff, WHITE))
        screen.blit(diff_text, (SCREEN_WIDTH // 2 - diff_text.get_width() // 2, 580))

        # High score
        hs = self._load_high_score()
        if hs > 0:
            hs_text = font_small.render(f"High Score: {hs:,}", True, GOLD)
            screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 620))

        # Controls hint
        hint = font_small.render("Arrow Keys: Navigate  |  Enter: Select  |  ESC: Quit", True, UI_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 700))

    def _load_high_score(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'highscore.txt')
            with open(path, 'r') as f:
                return int(f.read().strip())
        except Exception:
            return 0
