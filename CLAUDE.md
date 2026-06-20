# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Pygame-based space shooter game ("Galaxy Battle"). The project uses a state machine architecture with procedurally generated audio — zero external asset files.

## Running the Game

```bash
# Activate venv (Windows)
.venv\Scripts\activate

python main.py
```

No build step, no package manager, no tests. Dependencies: `pygame`, `numpy` (installed in `.venv`).

## Architecture

The codebase follows a state machine pattern with manager singletons.

| File | Purpose |
|------|---------|
| `main.py` | Entry point — instantiates `Game()` and calls `game.run()` |
| `game.py` | Thin controller — bootstraps `StateMachine`, runs main loop |
| `state_machine.py` | `State` base class + `StateMachine` with push/pop/switch |
| `config.py` | Global constants — screen, colors, fonts, FPS, shared `screen` surface |
| `settings.py` | Persistent settings (JSON) — volume, difficulty, fullscreen |
| `audio_manager.py` | Procedural audio generation (numpy) + playback management |
| `achievements.py` | Achievement tracking, persistence, notification queue |
| `player.py` | `Player` class — ship, movement physics, combat, HUD |
| `enemies.py` | `Enemy` (4 types), `EnemyBullet`, `Boss` — AI, attacks, drawing |
| `weapons.py` | `Bullet`, `Missile`, `Bomb`, `PowerUp` — projectiles and collectibles |
| `effects.py` | `Particle`, `EngineFlame`, `Explosion`, `LaserBeam`, `DamageNumber` |
| `background.py` | `Star` (parallax), `Nebula` — scrolling space background |
| `states/` | Game states (see below) |

### State Machine

| State | File | Purpose |
|-------|------|---------|
| `MenuState` | `states/menu_state.py` | Main menu — start, difficulty, settings |
| `PlayState` | `states/play_state.py` | Core gameplay — all combat, spawning, effects |
| `PauseState` | `states/pause_state.py` | Pause overlay (pushed on top of PlayState) |
| `GameOverState` | `states/gameover_state.py` | Stats display, achievements, restart/menu |

States use `machine.push()` (pause over gameplay), `machine.pop()` (resume), and `machine.switch()` (replace).

### Key Design Patterns

- **State Machine**: `StateMachine` manages a stack of `State` objects. Supports overlays (push/pop) and full transitions (switch).
- **Procedural Audio**: `audio_manager.py` generates all sounds with numpy — no audio files. Sounds include shoot, hit, explosion, powerup, combo, boss warning, level up, achievement, and BGM loop.
- **Singleton Managers**: `audio_manager.get()` and `settings` module-level state.
- **Lazy imports**: `player.py` imports `Bullet`/`Missile`/`Bomb` inside methods to avoid circular imports.
- **Sprite-based**: All game objects extend `pygame.sprite.Sprite` (except `Boss` and `LaserBeam`).
- **Procedural rendering**: All sprites drawn via `pygame.draw.*` — no image files.
- **Draw offsets**: All `draw()` methods accept `(ox, oy)` offset parameters for screen shake support.

### Game Feel Systems

| System | Implementation | Trigger |
|--------|---------------|---------|
| **Screen Shake** | Random offset applied to all draw calls | Explosions, boss attacks, player hit |
| **Hitstop** | `hitstop_timer` freezes game logic for N frames | Enemy kill (3f), player hit (2-3f) |
| **Flash** | Full-screen white overlay with alpha decay | Bomb explosion, level up |
| **Vignette** | Red edge overlay on screen perimeter | Player takes damage |
| **Damage Numbers** | `DamageNumber` floating text (rise + fade) | Every hit on enemy |
| **Combo Scaling** | Font size scales with combo count | Combo > 1 |
| **Boss Warning** | Shake + warning sound at 80% spawn timer | Boss about to spawn |

### Difficulty System

Settings stored in `settings.json`, loaded by `settings.py`. `DIFFICULTY_TABLE` provides multipliers for:
- Enemy count, damage, HP
- Drop rate
- Player starting health

### Achievement System

16 achievements tracked in `achievements.json`. Stats accumulate across sessions. Notifications appear as in-game banners (3s fade in/out) and on the game over screen.

## Important Notes

- `config.py` has side effects (`pygame.init()`) on import.
- `pygame.mixer.init()` is called by `audio_manager.py`, not `config.py`.
- `highscore.txt` and `settings.json` are runtime data (in `.gitignore`).
- `achievements.json` is also runtime data.
- `Boss` does NOT extend `pygame.sprite.Sprite` — handled separately in collision detection.
- `Enemy.update()` restores `original_image` before applying hit flash to prevent color accumulation.
- `Player.take_damage()` applies damage directly to health.
- `Bomb` detonates based on distance traveled (50px upward from spawn).
- `LaserBeam` has 3 phases: `charging` (60f) → `firing` (100f) → `cooldown` (30f).
- `DamageNumber` floats upward and fades over 40 frames.
- Screen shake uses decay curve (intensity decreases over timer duration).
- All draw methods support `(ox, oy)` offset for screen shake.
