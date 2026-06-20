"""Achievement tracking and persistence."""

import json
import os
import audio_manager

_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'achievements.json')

# Achievement definitions: (id, title, description, condition_key, threshold)
DEFINITIONS = [
    ('first_blood', 'First Blood', 'Destroy your first enemy', 'kills', 1),
    ('combo_10', 'Combo Chain', 'Reach a 10-hit combo', 'max_combo', 10),
    ('combo_25', 'Combo Master', 'Reach a 25-hit combo', 'max_combo', 25),
    ('combo_50', 'Combo Legend', 'Reach a 50-hit combo', 'max_combo', 50),
    ('boss_slayer', 'Boss Slayer', 'Defeat your first boss', 'boss_kills', 1),
    ('level_5', 'Space Cadet', 'Reach level 5', 'max_level', 5),
    ('level_10', 'Space Captain', 'Reach level 10', 'max_level', 10),
    ('level_20', 'Admiral', 'Reach level 20', 'max_level', 20),
    ('kills_100', 'Centurion', 'Destroy 100 enemies total', 'total_kills', 100),
    ('kills_500', 'War Machine', 'Destroy 500 enemies total', 'total_kills', 500),
    ('kills_1000', 'Annihilator', 'Destroy 1000 enemies total', 'total_kills', 1000),
    ('score_10k', 'Rising Star', 'Score 10,000 points', 'high_score', 10000),
    ('score_50k', 'Galaxy Hero', 'Score 50,000 points', 'high_score', 50000),
    ('score_100k', 'Legend', 'Score 100,000 points', 'high_score', 100000),
    ('survivor_5m', 'Survivor', 'Survive for 5 minutes', 'best_time', 300),
    ('survivor_10m', 'Endurance', 'Survive for 10 minutes', 'best_time', 600),
]

# Cumulative stats (persist across sessions)
_cumulative = {
    'total_kills': 0,
    'boss_kills': 0,
    'high_score': 0,
    'max_level': 0,
    'max_combo': 0,
    'best_time': 0,
}

_unlocked = set()
_pending_notifications = []


def load():
    """Load achievements from disk."""
    global _cumulative, _unlocked
    try:
        with open(_SAVE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _cumulative.update(data.get('stats', {}))
            _unlocked = set(data.get('unlocked', []))
    except Exception:
        pass


def save():
    """Save achievements to disk."""
    try:
        with open(_SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump({'stats': _cumulative, 'unlocked': list(_unlocked)},
                      f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def update_stats(session_stats):
    """Update cumulative stats from a game session and check for new achievements."""
    global _pending_notifications
    _cumulative['total_kills'] += session_stats.get('kills', 0)
    _cumulative['high_score'] = max(_cumulative['high_score'], session_stats.get('score', 0))
    _cumulative['max_level'] = max(_cumulative['max_level'], session_stats.get('level', 0))
    _cumulative['max_combo'] = max(_cumulative['max_combo'], session_stats.get('max_combo', 0))
    _cumulative['best_time'] = max(_cumulative['best_time'], session_stats.get('time', 0))
    if session_stats.get('boss_killed'):
        _cumulative['boss_kills'] += 1

    # Check for new unlocks
    new_unlocks = []
    for ach_id, title, desc, key, threshold in DEFINITIONS:
        if ach_id not in _unlocked and _cumulative.get(key, 0) >= threshold:
            _unlocked.add(ach_id)
            new_unlocks.append((ach_id, title, desc))
            _pending_notifications.append((title, desc))

    if new_unlocks:
        audio_manager.get().play('achievement')
        save()
    else:
        save()

    return new_unlocks


def get_notification():
    """Pop the next pending achievement notification, or None."""
    if _pending_notifications:
        return _pending_notifications.pop(0)
    return None


def get_all():
    """Return all achievements with unlock status."""
    result = []
    for ach_id, title, desc, key, threshold in DEFINITIONS:
        result.append({
            'id': ach_id,
            'title': title,
            'description': desc,
            'unlocked': ach_id in _unlocked,
            'progress': min(_cumulative.get(key, 0), threshold),
            'threshold': threshold,
        })
    return result


def is_unlocked(ach_id):
    return ach_id in _unlocked


# Load on import
load()
