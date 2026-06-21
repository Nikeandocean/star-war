"""Game controller — bootstraps state machine and runs the main loop."""

import sys
import pygame

from config import clock, FPS, screen, USE_OPENGL, SCREEN_WIDTH, SCREEN_HEIGHT
from state_machine import StateMachine
from states.menu_state import MenuState
import settings

# Lazy import GL renderer (only if OpenGL available)
gl_renderer = None
if USE_OPENGL:
    from gl_renderer import GLRenderer


class Game:
    def __init__(self):
        self.state_machine = StateMachine()
        self.state_machine.push(MenuState(self.state_machine))

        # Initialize GL renderer
        global gl_renderer
        if USE_OPENGL:
            try:
                gl_renderer = GLRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
            except Exception as e:
                print(f"OpenGL init failed, falling back to software: {e}")
                # Can't switch to software mid-run, but game_surface still works

        self.game_time = 0.0

    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            self.game_time += 1.0 / FPS

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

            if running:
                self.state_machine.handle_events(events)
                self.state_machine.update()

                if gl_renderer:
                    # GPU path: shader background + post-processing
                    gl_renderer.draw_background(self.game_time)

                    # States draw to offscreen surface (normal opaque)
                    self.state_machine.draw(screen)

                    # Upload and composite
                    gl_renderer.upload_game_surface(screen)

                    # Get post-processing params from current state
                    state = self.state_machine.current
                    vig = getattr(state, 'vignette_alpha', 0.0)
                    flash = getattr(state, 'flash_alpha', 0.0)
                    sx = getattr(state, 'shake_offset_x', 0.0)
                    sy = getattr(state, 'shake_offset_y', 0.0)

                    gl_renderer.composite_and_postprocess(vig, flash, sx, sy)
                    pygame.display.flip()
                else:
                    # CPU fallback: states draw directly
                    screen.fill((0, 0, 0))
                    self.state_machine.draw(screen)
                    pygame.display.flip()

        settings.save()
        if gl_renderer:
            gl_renderer.cleanup()
        pygame.quit()
        sys.exit()
