"""Procedural audio generation and playback management.

All sounds are generated with numpy — zero external audio files needed.
"""

import math
import numpy as np
import pygame

import settings

# Audio constants
SAMPLE_RATE = 44100
CHANNELS = 2


def _stereo(mono):
    """Convert mono samples to stereo."""
    return np.column_stack((mono, mono)).astype(np.float32)


def _envelope(samples, attack=0.01, decay=0.1, sustain_level=0.7, release=0.1):
    """Apply ADSR envelope to samples."""
    n = len(samples)
    attack_samples = int(attack * SAMPLE_RATE)
    decay_samples = int(decay * SAMPLE_RATE)
    release_samples = int(release * SAMPLE_RATE)
    sustain_samples = max(0, n - attack_samples - decay_samples - release_samples)

    env = np.zeros(n)
    idx = 0

    # Attack
    a = min(attack_samples, n)
    env[idx:idx + a] = np.linspace(0, 1, a)
    idx += a

    # Decay
    d = min(decay_samples, n - idx)
    if d > 0:
        env[idx:idx + d] = np.linspace(1, sustain_level, d)
        idx += d

    # Sustain
    s = min(sustain_samples, n - idx)
    if s > 0:
        env[idx:idx + s] = sustain_level
        idx += s

    # Release
    r = min(release_samples, n - idx)
    if r > 0:
        env[idx:idx + r] = np.linspace(sustain_level, 0, r)
        idx += r

    if idx < n:
        env[idx:] = 0

    return samples * env


def _noise(duration):
    """White noise."""
    return np.random.uniform(-1, 1, int(duration * SAMPLE_RATE)).astype(np.float32)


def _tone(freq, duration, wave='sine'):
    """Generate a tone."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    if wave == 'sine':
        return np.sin(2 * math.pi * freq * t).astype(np.float32)
    elif wave == 'square':
        return np.sign(np.sin(2 * math.pi * freq * t)).astype(np.float32)
    elif wave == 'saw':
        return (2 * (freq * t % 1) - 1).astype(np.float32)
    return np.sin(2 * math.pi * freq * t).astype(np.float32)


def _make_sound(samples):
    """Convert float32 numpy array to pygame Sound."""
    # Clamp to [-1, 1] and convert to int16
    samples = np.clip(samples, -1, 1)
    pcm = (samples * 32767).astype(np.int16)
    # Ensure contiguous
    pcm = np.ascontiguousarray(pcm)
    sound = pygame.sndarray.make_sound(pcm)
    return sound


# ── Sound generators ──────────────────────────────────────────────

def _shoot_sound():
    """Short laser pew."""
    dur = 0.08
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    freq = 1200 * np.exp(-t * 30)
    samples = np.sin(2 * math.pi * freq * t) * 0.4
    samples = _envelope(samples.astype(np.float32), attack=0.005, decay=0.03, sustain_level=0.3, release=0.04)
    return _make_sound(_stereo(samples))


def _hit_sound():
    """Metallic hit."""
    dur = 0.1
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    freq = 800 * np.exp(-t * 20)
    s1 = np.sin(2 * math.pi * freq * t) * 0.3
    s2 = _noise(dur) * np.exp(-t * 30) * 0.3
    samples = (s1 + s2).astype(np.float32)
    samples = _envelope(samples, attack=0.002, decay=0.03, sustain_level=0.2, release=0.06)
    return _make_sound(_stereo(samples))


def _explosion_sound():
    """Low boom + high crackle."""
    dur = 0.4
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    boom = np.sin(2 * math.pi * 60 * t) * np.exp(-t * 8) * 0.5
    crackle = _noise(dur) * np.exp(-t * 12) * 0.4
    rumble = np.sin(2 * math.pi * 30 * t) * np.exp(-t * 4) * 0.3
    samples = (boom + crackle + rumble).astype(np.float32)
    samples = _envelope(samples, attack=0.005, decay=0.1, sustain_level=0.4, release=0.25)
    return _make_sound(_stereo(samples))


def _big_explosion_sound():
    """Bigger explosion for bosses/bombs."""
    dur = 0.7
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    boom = np.sin(2 * math.pi * 40 * t) * np.exp(-t * 5) * 0.6
    crackle = _noise(dur) * np.exp(-t * 8) * 0.5
    rumble = np.sin(2 * math.pi * 20 * t) * np.exp(-t * 3) * 0.4
    sizzle = np.sin(2 * math.pi * 2000 * t) * np.exp(-t * 15) * 0.2
    samples = (boom + crackle + rumble + sizzle).astype(np.float32)
    samples = _envelope(samples, attack=0.005, decay=0.15, sustain_level=0.5, release=0.4)
    return _make_sound(_stereo(samples))


def _powerup_sound():
    """Rising chime."""
    dur = 0.3
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    freq = 400 + 800 * t / dur
    s1 = np.sin(2 * math.pi * freq * t) * 0.3
    s2 = np.sin(2 * math.pi * freq * 1.5 * t) * 0.15
    samples = (s1 + s2).astype(np.float32)
    samples = _envelope(samples, attack=0.01, decay=0.05, sustain_level=0.6, release=0.15)
    return _make_sound(_stereo(samples))


def _combo_sound(combo_level=1):
    """Combo notification — pitch rises with combo."""
    dur = 0.15
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    base = 300 + combo_level * 80
    freq = base + 200 * t / dur
    samples = np.sin(2 * math.pi * freq * t) * 0.25
    samples = _envelope(samples.astype(np.float32), attack=0.005, decay=0.03, sustain_level=0.4, release=0.08)
    return _make_sound(_stereo(samples))


def _player_hit_sound():
    """Player takes damage — heavy thud."""
    dur = 0.2
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    freq = 100 * np.exp(-t * 10)
    boom = np.sin(2 * math.pi * freq * t) * 0.5
    noise_hit = _noise(dur) * np.exp(-t * 20) * 0.3
    samples = (boom + noise_hit).astype(np.float32)
    samples = _envelope(samples, attack=0.002, decay=0.05, sustain_level=0.3, release=0.12)
    return _make_sound(_stereo(samples))


def _boss_warning_sound():
    """Low pulsing warning before boss."""
    dur = 0.6
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    pulse = np.sin(2 * math.pi * 80 * t) * (0.5 + 0.5 * np.sin(2 * math.pi * 3 * t))
    rumble = np.sin(2 * math.pi * 50 * t) * 0.3
    samples = (pulse * 0.4 + rumble).astype(np.float32)
    samples = _envelope(samples, attack=0.1, decay=0.1, sustain_level=0.6, release=0.3)
    return _make_sound(_stereo(samples))


def _level_up_sound():
    """Triumphant ascending arpeggio."""
    dur = 0.5
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n, endpoint=False)
    freqs = [523, 659, 784, 1047]  # C5, E5, G5, C6
    samples = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(freqs):
        start = int(i * 0.1 * SAMPLE_RATE)
        end = min(start + int(0.2 * SAMPLE_RATE), n)
        if start < n:
            seg_t = np.linspace(0, (end - start) / SAMPLE_RATE, end - start, endpoint=False)
            seg = np.sin(2 * math.pi * f * seg_t) * 0.25
            seg = _envelope(seg.astype(np.float32), attack=0.01, decay=0.05, sustain_level=0.5, release=0.1)
            samples[start:end] += seg
    return _make_sound(_stereo(samples))


def _achievement_sound():
    """Sparkle notification."""
    dur = 0.4
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    s1 = np.sin(2 * math.pi * 880 * t) * np.exp(-t * 8) * 0.2
    s2 = np.sin(2 * math.pi * 1320 * t) * np.exp(-t * 10) * 0.15
    s3 = np.sin(2 * math.pi * 1760 * t) * np.exp(-t * 12) * 0.1
    samples = (s1 + s2 + s3).astype(np.float32)
    samples = _envelope(samples, attack=0.005, decay=0.05, sustain_level=0.4, release=0.25)
    return _make_sound(_stereo(samples))


# ── BGM generator ─────────────────────────────────────────────────

def _generate_bgm_loop(duration=16):
    """Generate a looping electronic BGM."""
    n = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, n, endpoint=False)
    samples = np.zeros(n, dtype=np.float32)

    # Bass line (simple 4-bar loop)
    bass_notes = [65.41, 65.41, 82.41, 73.42]  # C2, C2, E2, D2
    bar_len = duration / 4
    for i, note in enumerate(bass_notes):
        start = int(i * bar_len * SAMPLE_RATE)
        end = int((i + 1) * bar_len * SAMPLE_RATE)
        seg_t = np.linspace(0, bar_len, end - start, endpoint=False)
        bass = np.sin(2 * math.pi * note * seg_t) * 0.15
        # Add sub-bass
        sub = np.sin(2 * math.pi * note * 0.5 * seg_t) * 0.1
        samples[start:end] += (bass + sub).astype(np.float32)

    # Kick drum on beats (4 per bar, 16 total)
    beat_len = bar_len / 4
    for i in range(16):
        start = int(i * beat_len * SAMPLE_RATE)
        kick_dur = 0.1
        kick_n = min(int(kick_dur * SAMPLE_RATE), n - start)
        if kick_n <= 0:
            continue
        kt = np.linspace(0, kick_dur, kick_n, endpoint=False)
        kick_freq = 150 * np.exp(-kt * 40)
        kick = np.sin(2 * math.pi * kick_freq * kt) * np.exp(-kt * 20) * 0.2
        samples[start:start + kick_n] += kick.astype(np.float32)

    # Hi-hat on off-beats
    for i in range(16):
        start = int((i + 0.5) * beat_len * SAMPLE_RATE)
        hh_dur = 0.05
        hh_n = min(int(hh_dur * SAMPLE_RATE), n - start)
        if hh_n <= 0:
            continue
        ht = np.linspace(0, hh_dur, hh_n, endpoint=False)
        hh = _noise(hh_dur)[:hh_n] * np.exp(-ht * 60) * 0.08
        samples[start:start + hh_n] += hh.astype(np.float32)

    # Pad synth (ambient texture)
    pad_freq = 130.81  # C3
    pad = np.sin(2 * math.pi * pad_freq * t) * 0.04
    pad += np.sin(2 * math.pi * pad_freq * 1.01 * t) * 0.04  # Slight detune
    samples += pad.astype(np.float32)

    # Normalize
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak * 0.7

    return _stereo(samples)


# ── AudioManager ──────────────────────────────────────────────────

class AudioManager:
    """Manages all game audio."""

    def __init__(self):
        self._sounds = {}
        self._bgm = None
        self._muted = False
        self._init_mixer()
        self._generate_sounds()

    def _init_mixer(self):
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)

    def _generate_sounds(self):
        """Pre-generate all sound effects."""
        self._sounds['shoot'] = _shoot_sound()
        self._sounds['hit'] = _hit_sound()
        self._sounds['explosion'] = _explosion_sound()
        self._sounds['big_explosion'] = _big_explosion_sound()
        self._sounds['powerup'] = _powerup_sound()
        self._sounds['player_hit'] = _player_hit_sound()
        self._sounds['boss_warning'] = _boss_warning_sound()
        self._sounds['level_up'] = _level_up_sound()
        self._sounds['achievement'] = _achievement_sound()
        # Combo sounds at different pitches
        for i in range(1, 6):
            self._sounds[f'combo_{i}'] = _combo_sound(i)

        # BGM
        bgm_data = _generate_bgm_loop(16)
        pcm = (np.clip(bgm_data, -1, 1) * 32767).astype(np.int16)
        pcm = np.ascontiguousarray(pcm)
        self._bgm = pygame.sndarray.make_sound(pcm)

    def play(self, name, volume=None):
        """Play a named sound effect."""
        if self._muted:
            return
        sound = self._sounds.get(name)
        if sound:
            if volume is None:
                vol = settings.get('sfx_volume') / 100.0
            else:
                vol = volume
            sound.set_volume(vol)
            sound.play()

    def play_combo(self, combo):
        """Play combo sound with pitch based on combo level."""
        tier = min(5, max(1, (combo // 10) + 1))
        self.play(f'combo_{tier}')

    def start_bgm(self):
        """Start background music loop."""
        if self._bgm and not self._muted:
            vol = settings.get('bgm_volume') / 100.0
            self._bgm.set_volume(vol)
            self._bgm.play(-1)

    def stop_bgm(self):
        """Stop background music."""
        if self._bgm:
            self._bgm.stop()

    def update_bgm_volume(self):
        """Update BGM volume from settings."""
        if self._bgm:
            vol = settings.get('bgm_volume') / 100.0 if not self._muted else 0
            self._bgm.set_volume(vol)

    def toggle_mute(self):
        """Toggle global mute."""
        self._muted = not self._muted
        if self._muted:
            self.stop_bgm()
        else:
            self.start_bgm()
        return self._muted


# Singleton instance
_audio = None


def get():
    """Get the global AudioManager instance."""
    global _audio
    if _audio is None:
        _audio = AudioManager()
    return _audio
