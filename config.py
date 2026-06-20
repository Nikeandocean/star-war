import pygame

pygame.init()

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("Galaxy Battle")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
DARK_RED = (139, 0, 0)
NEON_BLUE = (0, 200, 255)
NEON_GREEN = (0, 255, 100)
NEON_PINK = (255, 0, 150)
DARK_BLUE = (0, 0, 50)
LIGHT_YELLOW = (255, 255, 200)
PINK = (255, 100, 150)

# UI colors
UI_BG = (15, 15, 30)
UI_BORDER = (60, 60, 100)
UI_HIGHLIGHT = (80, 120, 200)
UI_TEXT = (200, 200, 220)
UI_TEXT_DIM = (120, 120, 140)
DAMAGE_COLOR = (255, 80, 80)
HEAL_COLOR = (80, 255, 80)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font_large = pygame.font.Font(None, 80)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)
font_tiny = pygame.font.Font(None, 22)
font_damage = pygame.font.Font(None, 36)
