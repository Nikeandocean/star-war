# Star Wars: Galaxy Battle

A Pygame-based space shooter game featuring Star Wars-inspired ships, epic boss battles, and combo scoring.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Pygame](https://img.shields.io/badge/pygame-2.x-green)

## Screenshots

> The game features procedurally rendered sprites — no external assets required.

## Features

- 4 enemy types: TIE Fighter, Interceptor, Bomber, Elite
- Boss battles with 4 attack patterns (spread shot, aimed shot, laser beam, radial burst)
- Combo scoring system (up to 6x multiplier)
- 6 power-up types: health, shield, power, bomb, missile, energy
- Parallax starfield with twinkling and nebula background effects
- Screen shake, explosion particles, engine flame effects
- Difficulty scaling across levels
- High score persistence

## Requirements

- Python 3.11+
- pygame

## Installation

```bash
# Create virtual environment (optional)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install pygame

# Run the game
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **Arrow Keys** | Move ship |
| **Space** | Shoot |
| **M** | Launch homing missile |
| **B** | Drop bomb |
| **P** | Pause / Resume |
| **ESC** | Exit game / Go to main menu |

## How to Play

1. Press **Space** on the title screen to start.
2. Destroy enemy ships to earn points.
3. Collect power-ups dropped by destroyed enemies (20% drop chance).
4. Survive and level up — difficulty increases every 25 × level enemies destroyed.
5. Boss ships appear every 45 seconds after reaching level 3.
6. When your health reaches 0, the game ends. Beat your high score!

### Scoring

- Base enemy score: 100 (TIE) → 300 (Interceptor) → 500 (Bomber) → 700 (Elite)
- Boss score: 5,000
- Combo multiplier: `1 + min(combo / 10, 5)` — chain kills to maximize your score
- Combo resets after 2 seconds without a kill

### Power-Ups

| Power-Up | Effect |
|----------|--------|
| Health (red) | Restores 40 HP |
| Shield (cyan) | Restores 50 shield |
| Power (yellow) | Increases weapon level (max 3) |
| Bomb (orange) | Adds 3 bombs |
| Missile (purple) | Adds 3 homing missiles |
| Energy (green) | Fully restores energy |

### Weapons

- **Main Cannon** (Space): Auto-fires when held, costs 2 energy per shot. Weapon level 2 fires dual shots, level 3 adds angled spread.
- **Missile** (M): Homing missile that tracks enemies. Costs 20 energy.
- **Bomb** (B): Area-of-effect explosion. Instantly kills all enemies within blast radius.

## Project Structure

```
star_war/
├── main.py          # Entry point
├── game.py          # Main game loop, event handling, rendering
├── player.py        # Player ship, movement, stats, shooting
├── enemies.py       # Enemy types, Boss AI
├── weapons.py       # Bullets, missiles, bombs, power-ups
├── effects.py       # Particles, explosions, laser beams
├── background.py    # Parallax stars, nebula clouds
├── config.py        # Screen settings, colors, fonts, constants
└── highscore.txt    # Persisted high score (runtime)
```

## License

This is a fan project and is not affiliated with or endorsed by Lucasfilm Ltd. or Disney. All Star Wars related materials are property of their respective owners.
