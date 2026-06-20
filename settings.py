"""Persistent game settings."""

import json
import os

_DEFAULTS = {
    'sfx_volume': 70,       # 0-100
    'bgm_volume': 50,       # 0-100
    'difficulty': 'Normal',  # Easy / Normal / Hard
    'fullscreen': False,
}

_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

_data = dict(_DEFAULTS)


def get(key):
    return _data.get(key, _DEFAULTS.get(key))


def set_value(key, value):
    _data[key] = value


def save():
    try:
        with open(_SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load():
    global _data
    try:
        with open(_SAVE_PATH, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            _data = dict(_DEFAULTS)
            _data.update(loaded)
    except Exception:
        _data = dict(_DEFAULTS)


# Load on import
load()

# Difficulty multipliers
DIFFICULTY_TABLE = {
    'Easy': {
        'enemy_count_mult': 0.7,
        'enemy_damage_mult': 0.6,
        'enemy_hp_mult': 0.8,
        'drop_rate': 0.30,
        'player_start_health': 150,
    },
    'Normal': {
        'enemy_count_mult': 1.0,
        'enemy_damage_mult': 1.0,
        'enemy_hp_mult': 1.0,
        'drop_rate': 0.20,
        'player_start_health': 100,
    },
    'Hard': {
        'enemy_count_mult': 1.5,
        'enemy_damage_mult': 1.5,
        'enemy_hp_mult': 1.3,
        'drop_rate': 0.15,
        'player_start_health': 80,
    },
}


def get_difficulty():
    return DIFFICULTY_TABLE.get(get('difficulty'), DIFFICULTY_TABLE['Normal'])
