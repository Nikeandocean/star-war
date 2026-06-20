"""Pause menu overlay."""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, CYAN, UI_BG, UI_BORDER,
    UI_HIGHLIGHT, UI_TEXT, font_large, font_medium, font_small,
)
from state_machine import State


class PauseState(State):
    OPTIONS = ['Continue', 'Settings', 'Quit to Menu']

    def __init__(self, machine):
        super().__init__(machine)
        self.selected = 0
        self.overlay = None

    def enter(self):
        self.selected = 0
        # Capture current screen for dimmed background
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    self.machine.pop()
                    return
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.OPTIONS)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.OPTIONS)
                elif event.key == pygame.K_RETURN:
                    self._select()

    def _select(self):
        choice = self.OPTIONS[self.selected]
        if choice == 'Continue':
            self.machine.pop()
        elif choice == 'Quit to Menu':
            # Pop self, then switch play state to menu
            self.machine.pop()
            from states.menu_state import MenuState
            self.machine.switch(MenuState(self.machine))

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))

        # Title
        title = font_large.render("PAUSED", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))

        # Options
        for i, option in enumerate(self.OPTIONS):
            if i == self.selected:
                color = CYAN
                prefix = "> "
            else:
                color = UI_TEXT
                prefix = "  "
            text = font_medium.render(f"{prefix}{option}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 340 + i * 55))

        # Hint
        hint = font_small.render("ESC / P to resume", True, UI_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 550))
