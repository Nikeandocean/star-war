"""Game controller — bootstraps state machine and runs the main loop."""

import sys
import pygame

from config import clock, FPS, screen
from state_machine import StateMachine
from states.menu_state import MenuState
import settings


class Game:
    def __init__(self):
        self.state_machine = StateMachine()
        self.state_machine.push(MenuState(self.state_machine))

    def run(self):
        running = True
        while running:
            clock.tick(FPS)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

            if running:
                self.state_machine.handle_events(events)
                self.state_machine.update()
                self.state_machine.draw(screen)
                pygame.display.flip()

        settings.save()
        pygame.quit()
        sys.exit()
