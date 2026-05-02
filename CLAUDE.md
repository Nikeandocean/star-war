# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Pygame-based Star Wars space shooter game ("Star Wars: Galaxy Battle"). The project was refactored from a monolithic `star_wars_game.py` into a modular structure (commit `2a7e670`).

## Running the Game

```bash
python main.py
```

No build step, no package manager, no tests. The only dependency is `pygame`, installed in a `.venv` virtual environment (Python 3.11).

## Architecture

The codebase follows a flat single-layer module structure — no subpackages, no deep hierarchy.

| File | Purpose |
|------|---------|
| `main.py` | Entry point — instantiates `Game()` and calls `game.run()` |
| `game.py` | Central `Game` class — main loop, event handling, collision detection, all game state, rendering for all screens (start/playing/gameover) |
| `player.py` | `Player` class — ship rendering, movement with physics (friction/acceleration), health/shield/energy stats, shooting, bomb/missile abilities, HUD drawing |
| `enemies.py` | `Enemy` (4 types: TIE Fighter, Interceptor, Bomber, Elite), `EnemyBullet`, `Boss` — enemy AI movement patterns, attack patterns, drawing |
| `weapons.py` | `Bullet`, `Missile`, `Bomb`, `PowerUp` — player projectiles and collectible items |
| `effects.py` | `Particle`, `EngineFlame`, `Explosion`, `LaserBeam` — all visual effects |
| `background.py` | `Star` (parallax, twinkling), `Nebula` — scrolling space background |
| `config.py` | Global constants — screen dimensions (1024x768), colors, fonts, FPS (60), `pygame.init()` and `pygame.mixer.init()` side effects, shared `screen` surface and `clock` |

### Key Design Patterns

- **Sprite-based**: All game objects extend `pygame.sprite.Sprite` (except `Boss` and `LaserBeam` which are custom classes).
- **Centralized Game Loop**: `Game.run()` handles the main loop; `Game.update()` updates all state; `Game.draw()` renders all screens.
- **Lazy imports**: `player.py` imports `Bullet`/`Missile`/`Bomb` inside methods to avoid circular imports.
- **Procedural rendering**: All sprites are drawn programmatically via `pygame.draw.*` calls — no image/asset files are used.
- **Shared mutable globals**: `config.py` creates a module-level `screen` surface and `clock` that all modules import directly.

## Game Mechanics

- **Controls**: Arrow keys (move), Space (shoot), M (missile), B (bomb), P (pause), ESC (exit)
- **Difficulty scaling**: Enemy spawn rate and type weights change with `level` (every 25*level enemies destroyed)
- **Boss**: Spawns every 45s after level 3, cycles through 4 attack patterns (spread shot, aimed shot, laser beam, radial burst)
- **Combo system**: Kill streaks multiply score (up to 6x), resets after 2s
- **Power-ups**: 6 types (health, shield, power, bomb, missile, energy), 20% drop chance, weighted spawn

## Important Notes

- `config.py` has side effects (`pygame.init()`) on import — all modules implicitly depend on this.
- `highscore.txt` is runtime data (in `.gitignore`), persisted via simple file I/O in `game.py`.
- The `.claudeignore` explicitly excludes all media assets (`*.mp3`, `*.png`, etc.) — the game generates everything procedurally.
- No `requirements.txt` exists; `pygame` is the only external dependency.
- Recent fix (commit `3d8a679`): Bomb now detonates above the player (at spawn Y offset) rather than at a fixed bottom-screen position.
- `Boss` does NOT extend `pygame.sprite.Sprite` — it's a standalone class with manual `rect`/`image` management, handled separately in collision detection in `game.py`.
- Enemy `update()` properly restores `original_image` before applying hit flash to prevent color accumulation.
