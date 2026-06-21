"""Game over screen with detailed stats."""

import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED, GREEN, YELLOW, GOLD,
    CYAN, SILVER, NEON_GREEN, UI_TEXT, UI_TEXT_DIM, USE_OPENGL,
    font_large, font_medium, font_small, font_tiny,
)
from state_machine import State
from background import Star


class GameOverState(State):

    def __init__(self, machine, stats=None, new_achievements=None):
        super().__init__(machine)
        self.stats = stats or {}
        self.new_achievements = new_achievements or []
        self.selected = 0
        self.stars = [Star(layer=i % 3) for i in range(80)]
        self.time = 0

    def enter(self):
        self.selected = 0
        self.time = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % 2
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % 2
                elif event.key == pygame.K_RETURN:
                    if self.selected == 0:
                        from states.play_state import PlayState
                        self.machine.switch(PlayState(self.machine))
                    else:
                        from states.menu_state import MenuState
                        self.machine.switch(MenuState(self.machine))
                elif event.key == pygame.K_SPACE:
                    from states.play_state import PlayState
                    self.machine.switch(PlayState(self.machine))
                elif event.key == pygame.K_ESCAPE:
                    from states.menu_state import MenuState
                    self.machine.switch(MenuState(self.machine))

    def update(self):
        self.time += 1
        for star in self.stars:
            star.update()

    def draw(self, screen):
        screen.fill(BLACK)
        if not USE_OPENGL:
            for star in self.stars:
                star.draw(screen, self.time)

        # Game Over title
        pulse = int(math.sin(self.time * 0.08) * 20 + 200)
        go_text = font_large.render("GAME OVER", True, (pulse, 50, 50))
        screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 80))

        # Score
        score = self.stats.get('score', 0)
        score_text = font_medium.render(f"Score: {score:,}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 170))

        # New high score
        if self.stats.get('new_high'):
            nh_text = font_medium.render("NEW HIGH SCORE!", True, GOLD)
            screen.blit(nh_text, (SCREEN_WIDTH // 2 - nh_text.get_width() // 2, 220))

        # Stats box
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 270, 400, 220)
        pygame.draw.rect(screen, (15, 15, 35), box_rect, border_radius=8)
        pygame.draw.rect(screen, (50, 50, 80), box_rect, 2, border_radius=8)

        stats_list = [
            (f"Level Reached", f"{self.stats.get('level', 1)}"),
            (f"Enemies Destroyed", f"{self.stats.get('kills', 0)}"),
            (f"Max Combo", f"{self.stats.get('max_combo', 0)}"),
            (f"Time Survived", self._format_time(self.stats.get('time', 0))),
            (f"High Score", f"{self.stats.get('high_score', 0):,}"),
        ]

        for i, (label, value) in enumerate(stats_list):
            y = 285 + i * 38
            lbl = font_small.render(label, True, UI_TEXT_DIM)
            val = font_small.render(value, True, CYAN)
            screen.blit(lbl, (SCREEN_WIDTH // 2 - 170, y))
            screen.blit(val, (SCREEN_WIDTH // 2 + 100, y))

        # New achievements unlocked
        ach_y = 500
        if self.new_achievements:
            ach_header = font_small.render("Achievements Unlocked!", True, GOLD)
            screen.blit(ach_header, (SCREEN_WIDTH // 2 - ach_header.get_width() // 2, ach_y))
            ach_y += 30
            for ach_id, title, desc in self.new_achievements[:3]:  # Show max 3
                ach_text = font_tiny.render(f"{title} — {desc}", True, NEON_GREEN)
                screen.blit(ach_text, (SCREEN_WIDTH // 2 - ach_text.get_width() // 2, ach_y))
                ach_y += 22

        # Options
        opt_start_y = max(580, ach_y + 20)
        options = ['Play Again', 'Main Menu']
        for i, opt in enumerate(options):
            y = opt_start_y + i * 50
            if i == self.selected:
                color = CYAN
                prefix = "> "
            else:
                color = UI_TEXT
                prefix = "  "
            text = font_medium.render(f"{prefix}{opt}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))

        # Hints
        hint_y = opt_start_y + len(options) * 50 + 20
        hint = font_tiny.render("SPACE: Quick Restart  |  ESC: Menu", True, UI_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, min(hint_y, 720)))

    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
