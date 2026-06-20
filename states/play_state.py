"""Main gameplay state — all in-game logic lives here."""

import os
import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED, GREEN, YELLOW,
    CYAN, ORANGE, PURPLE, GOLD, SILVER, UI_TEXT, UI_TEXT_DIM,
    DAMAGE_COLOR, HEAL_COLOR,
    font_large, font_medium, font_small, font_tiny, font_damage,
)
from state_machine import State
from background import Star, Nebula
from effects import Explosion, LaserBeam, Particle, DamageNumber
from player import Player
from enemies import Enemy, EnemyBullet, Boss
from weapons import Bomb
import audio_manager
import settings
import achievements


class PlayState(State):

    def enter(self):
        # Sprite groups
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.missiles = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()

        # Effects
        self.stars = [Star(layer=i % 3) for i in range(150)]
        self.nebulae = [Nebula() for _ in range(5)]
        self.explosions = []
        self.particles = []
        self.laser_beams = []
        self.damage_numbers = []

        # Player
        self.player = Player()

        # Enemy spawn
        self.enemy_timer = 0
        self.boss = None
        self.boss_timer = 0
        self.boss_spawn_delay = 45000  # 45 seconds
        self.boss_warning_played = False

        # Combo
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.total_kills = 0

        # Level
        self.score = 0
        self.level = 1
        self.enemies_destroyed = 0

        # Game time
        self.game_time = 0
        self.start_ticks = pygame.time.get_ticks()

        # Screen shake
        self.shake_timer = 0
        self.shake_intensity = 0

        # Hitstop
        self.hitstop_timer = 0

        # Flash overlay (full-screen white flash on big hits)
        self.flash_timer = 0
        self.flash_alpha = 0

        # Vignette (red edge flash when player hit)
        self.vignette_timer = 0

        # Difficulty settings
        self.diff = settings.get_difficulty()

        # High score
        self.high_score = self._load_high_score()

        # Achievement notification queue
        self.achievement_notifications = []  # list of (title, timer)

        # Boss tracking
        self.boss_killed = False

        # Pre-render vignette surface (reusable)
        self._vignette_surf = self._create_vignette()

        # Start BGM
        audio_manager.get().start_bgm()

    def exit(self):
        audio_manager.get().stop_bgm()

    # ── High score ────────────────────────────────────────────────

    def _load_high_score(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'highscore.txt')
            with open(path, 'r') as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def _save_high_score(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'highscore.txt')
            with open(path, 'w') as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    # ── Event handling ────────────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    from states.pause_state import PauseState
                    self.machine.push(PauseState(self.machine))
                    return

                if event.key == pygame.K_m:
                    missile = self.player.shoot_missile()
                    if missile:
                        self.missiles.add(missile)
                        audio_manager.get().play('shoot')

                if event.key == pygame.K_b:
                    bomb = self.player.drop_bomb()
                    if bomb:
                        self.bombs.add(bomb)

    # ── Update ────────────────────────────────────────────────────

    def update(self):
        # Hitstop: freeze game logic for a few frames
        if self.hitstop_timer > 0:
            self.hitstop_timer -= 1
            # Still update visual-only effects during hitstop
            self._update_visual_effects()
            return

        self.game_time += 1

        # Background
        for star in self.stars:
            star.update()
        for nebula in self.nebulae:
            nebula.update()

        # Sprites
        self.player.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.missiles.update()
        self.bombs.update()

        # Effects
        self._update_visual_effects()

        # Player shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            bullets = self.player.shoot()
            for bullet in bullets:
                self.player_bullets.add(bullet)
                audio_manager.get().play('shoot', volume=0.3)

        # Enemy spawning
        self._update_spawning()

        # Enemy shooting
        self._update_enemy_attacks()

        # Collision detection
        self._check_collisions()

        # Combo timer
        if self.combo > 0:
            if pygame.time.get_ticks() - self.combo_timer > 2000:
                self.combo = 0

        # Level up
        if self.enemies_destroyed >= self.level * 25:
            self._level_up()

        # Achievement notifications
        self.achievement_notifications = [
            (title, timer - 1) for title, timer in self.achievement_notifications
            if timer > 1
        ]
        notif = achievements.get_notification()
        if notif:
            self.achievement_notifications.append((notif[0], 180))  # 3 seconds

        # Game over
        if self.player.health <= 0:
            self._game_over()

    def _update_visual_effects(self):
        self.explosions = [e for e in self.explosions if e.update()]
        self.particles = [p for p in self.particles if p.update()]
        self.laser_beams = [b for b in self.laser_beams if b.update()]
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]

        # Flash timer
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Vignette timer
        if self.vignette_timer > 0:
            self.vignette_timer -= 1

    def _update_spawning(self):
        self.enemy_timer += 1
        diff_mult = self.diff['enemy_count_mult']
        spawn_delay = max(30, int((90 - self.level * 5) / diff_mult))
        if self.enemy_timer >= spawn_delay:
            if not self.boss:
                self._spawn_enemy()
            self.enemy_timer = 0

        # Boss spawning
        if self.boss is None and self.level >= 3:
            self.boss_timer += 1
            # Boss warning at 80% of spawn delay
            if self.boss_timer >= self.boss_spawn_delay * 0.8 and not self.boss_warning_played:
                audio_manager.get().play('boss_warning')
                self.boss_warning_played = True
                self.shake_timer = 30
                self.shake_intensity = 3
            if self.boss_timer >= self.boss_spawn_delay:
                self._spawn_boss()

    def _update_enemy_attacks(self):
        for enemy in self.enemies:
            if enemy.can_shoot() and not self.boss:
                bullet_type = random.randint(0, 10)
                dmg_mult = self.diff['enemy_damage_mult']
                if bullet_type < 7:
                    self._spawn_enemy_bullet(enemy.rect.centerx, enemy.rect.bottom,
                                             damage=int(15 * dmg_mult))
                else:
                    self._spawn_enemy_bullet(enemy.rect.centerx, enemy.rect.bottom,
                                             random.randint(-2, 2), 8, RED,
                                             damage=int(15 * dmg_mult))

        if self.boss:
            self.boss.update(self.player)
            if self.boss.can_attack():
                self._boss_attack()

    def _level_up(self):
        self.level += 1
        self.player.health = min(self.player.health + 30, self.player.max_health)
        self._add_particles(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GOLD, 50)
        audio_manager.get().play('level_up')
        self.flash_timer = 10
        self.flash_alpha = 100

    def _game_over(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()
        self._add_explosion(self.player.rect.centerx, self.player.rect.centery, 100)
        audio_manager.get().play('big_explosion')
        self.hitstop_timer = 15
        self.flash_timer = 20
        self.flash_alpha = 200

        survival_time = (pygame.time.get_ticks() - self.start_ticks) // 1000
        stats = {
            'score': self.score,
            'level': self.level,
            'kills': self.enemies_destroyed,
            'max_combo': self.max_combo,
            'time': survival_time,
            'high_score': self.high_score,
            'new_high': self.score >= self.high_score and self.score > 0,
            'boss_killed': self.boss_killed,
        }

        # Update achievements
        new_achievements = achievements.update_stats(stats)

        from states.gameover_state import GameOverState
        self.machine.switch(GameOverState(self.machine, stats, new_achievements))

    # ── Spawning helpers ──────────────────────────────────────────

    def _spawn_enemy(self):
        if self.level >= 5:
            weights = [30, 40, 25, 5]
        elif self.level >= 3:
            weights = [40, 35, 20, 5]
        else:
            weights = [60, 30, 10, 0]
        enemy_type = random.choices([0, 1, 2, 3], weights=weights)[0]
        enemy = Enemy(enemy_type)
        enemy.health = int(enemy.health * self.diff['enemy_hp_mult'])
        enemy.max_health = enemy.health
        self.enemies.add(enemy)

    def _spawn_boss(self):
        self.boss = Boss()
        self.boss_timer = 0
        self.boss_warning_played = False

    def _spawn_enemy_bullet(self, x, y, angle_x=0, speed=6, color=RED, damage=15):
        bullet = EnemyBullet(x, y, angle_x, speed, color, damage)
        self.enemy_bullets.add(bullet)

    # ── Boss attacks ──────────────────────────────────────────────

    def _boss_attack(self):
        attack = self.boss.attack_pattern
        if attack == 0:
            for angle in [-30, -15, 0, 15, 30]:
                self._spawn_enemy_bullet(
                    self.boss.rect.centerx, self.boss.rect.bottom,
                    math.sin(math.radians(angle)) * 3, 6, PURPLE, 20)
        elif attack == 1:
            dx = self.player.rect.centerx - self.boss.rect.centerx
            horizontal_dist = max(abs(dx), 1)
            self._spawn_enemy_bullet(
                self.boss.rect.centerx, self.boss.rect.bottom,
                dx / horizontal_dist * 5, 8, RED, 30)
        elif attack == 2:
            beam = LaserBeam(self.boss.rect.centerx, self.boss.rect.bottom + 50)
            self.laser_beams.append(beam)
        else:
            for i in range(8):
                angle = i * 45 + self.game_time * 2
                self._spawn_enemy_bullet(
                    self.boss.rect.centerx, self.boss.rect.bottom,
                    math.cos(math.radians(angle)) * 4,
                    math.sin(math.radians(angle)) * 4,
                    CYAN, 15)

    # ── Collision detection ───────────────────────────────────────

    def _check_collisions(self):
        # Player bullets → enemies
        hit_enemies = {}
        for bullet in list(self.player_bullets):
            expanded = pygame.Rect(
                bullet.rect.x, bullet.rect.y,
                bullet.rect.width, bullet.rect.height + abs(bullet.speed))
            for enemy in self.enemies:
                if expanded.colliderect(enemy.rect):
                    hit_enemies.setdefault(enemy, []).append(bullet)

        for enemy, bullets in hit_enemies.items():
            for bullet in bullets:
                bullet.kill()
            damage = sum(b.damage for b in bullets)
            if enemy.take_damage(damage):
                self._on_enemy_killed(enemy, 40 if enemy.enemy_type >= 2 else 25)
            else:
                audio_manager.get().play('hit', volume=0.4)
                # Show damage number
                self.damage_numbers.append(
                    DamageNumber(enemy.rect.centerx, enemy.rect.top, damage))

        # Missiles → enemies
        for missile in list(self.missiles):
            hits = pygame.sprite.spritecollide(missile, self.enemies, False)
            if hits:
                explosion = missile.explode()
                self.explosions.append(explosion)
                self.shake_timer = 20
                self.shake_intensity = 6
                self._add_particles(missile.rect.centerx, missile.rect.centery, RED, 30)
                missile.kill()
                audio_manager.get().play('explosion')
                for enemy in list(self.enemies):
                    dist = math.hypot(
                        enemy.rect.centerx - explosion.x,
                        enemy.rect.centery - explosion.y)
                    if dist < explosion.size:
                        if enemy.take_damage(explosion.damage):
                            self._on_enemy_killed(enemy)

        # Boss collisions
        if self.boss:
            for proj in list(self.player_bullets):
                if self.boss.rect.colliderect(proj.rect):
                    proj.kill()
                    if self.boss.take_damage(proj.damage):
                        self._add_explosion(self.boss.rect.centerx,
                                            self.boss.rect.centery, 150)
                        self._add_particles(self.boss.rect.centerx,
                                            self.boss.rect.centery, GOLD, 50)
                        self.score += self.boss.score_value
                        self.shake_timer = 60
                        self.shake_intensity = 10
                        audio_manager.get().play('big_explosion')
                        self.boss_killed = True
                        self.boss = None
                        break
                    else:
                        audio_manager.get().play('hit', volume=0.5)
            if self.boss:
                for missile in list(self.missiles):
                    if self.boss.rect.colliderect(missile.rect):
                        explosion = missile.explode()
                        self.explosions.append(explosion)
                        self.shake_timer = 20
                        self.shake_intensity = 6
                        self._add_particles(missile.rect.centerx, missile.rect.centery, RED, 30)
                        missile.kill()
                        audio_manager.get().play('explosion')
                        boss_died = self.boss.take_damage(explosion.damage)
                        boss_cx, boss_cy = self.boss.rect.centerx, self.boss.rect.centery
                        if boss_died:
                            self._add_explosion(boss_cx, boss_cy, 150)
                            self._add_particles(boss_cx, boss_cy, GOLD, 50)
                            self.score += self.boss.score_value
                            self.shake_timer = 60
                            self.shake_intensity = 10
                            audio_manager.get().play('big_explosion')
                            self.boss_killed = True
                            self.boss = None
                        for enemy in list(self.enemies):
                            dist = math.hypot(
                                enemy.rect.centerx - explosion.x,
                                enemy.rect.centery - explosion.y)
                            if dist < explosion.size:
                                if enemy.take_damage(explosion.damage):
                                    self._on_enemy_killed(enemy)
                        break

        # Enemies → player
        hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for enemy in hits:
            if not self.player.invincible:
                damage = int((30 + enemy.enemy_type * 10) * self.diff['enemy_damage_mult'])
                self.player.take_damage(damage)
                self.player.invincible = True
                self.player.invincible_timer = 90
                self.player.hit_effect_timer = 30
                self._add_explosion(self.player.rect.centerx,
                                    self.player.rect.centery, 50)
                self.shake_timer = 15
                self.shake_intensity = 5
                self.hitstop_timer = 3
                self.vignette_timer = 20
                audio_manager.get().play('player_hit')

        # Enemy bullets → player
        hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for bullet in hits:
            if not self.player.invincible:
                damage = bullet.damage
                self.player.take_damage(damage)
                self.player.invincible = True
                self.player.invincible_timer = 45
                self.player.hit_effect_timer = 15
                self._add_particles(self.player.rect.centerx,
                                    self.player.rect.centery, RED, 10)
                self.hitstop_timer = 2
                self.vignette_timer = 15
                audio_manager.get().play('player_hit', volume=0.6)

        # Bombs
        for bomb in list(self.bombs):
            if bomb.should_explode():
                explosion = bomb.explode()
                self.explosions.append(explosion)
                self.shake_timer = 30
                self.shake_intensity = 8
                self.flash_timer = 8
                self.flash_alpha = 150
                audio_manager.get().play('big_explosion')
                for enemy in list(self.enemies):
                    dist = math.hypot(
                        enemy.rect.centerx - bomb.rect.centerx,
                        enemy.rect.centery - bomb.rect.centery)
                    if dist < explosion.size:
                        if enemy.take_damage(explosion.damage):
                            self._on_enemy_killed(enemy)
                bomb.kill()

        # Power-up collection
        hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in hits:
            self._apply_powerup(powerup)

        # Laser beam → player
        for beam in self.laser_beams:
            damage_rect = beam.get_damage_rect()
            if damage_rect and not self.player.invincible:
                if damage_rect.colliderect(self.player.rect):
                    self.player.take_damage(beam.damage)
                    self.player.hit_effect_timer = 5

    def _on_enemy_killed(self, enemy, explosion_size=30):
        self._add_explosion(enemy.rect.centerx, enemy.rect.centery, explosion_size)
        self._add_particles(enemy.rect.centerx, enemy.rect.centery, ORANGE, 15)
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.combo_timer = pygame.time.get_ticks()
        self.total_kills += 1
        multiplier = 1 + min(self.combo / 10, 5)
        self.score += int(enemy.score_value * multiplier)
        audio_manager.get().play('explosion', volume=0.5)
        # Hitstop on kill
        self.hitstop_timer = 3
        # Combo sound
        if self.combo > 1 and self.combo % 5 == 0:
            audio_manager.get().play_combo(self.combo)
        # Drop powerup
        if random.random() < self.diff['drop_rate']:
            from weapons import PowerUp
            self.powerups.add(PowerUp(enemy.rect.center))
        self.enemies_destroyed += 1
        enemy.kill()

    def _apply_powerup(self, powerup):
        audio_manager.get().play('powerup')
        if powerup.type == 'health':
            self.player.health = min(self.player.health + 40, self.player.max_health)
            self._add_particles(self.player.rect.centerx,
                                self.player.rect.centery, GREEN, 20)
        elif powerup.type == 'power':
            self.player.power_level = min(self.player.power_level + 1, 3)
            self.player.power_timer = pygame.time.get_ticks()
            self._add_particles(self.player.rect.centerx,
                                self.player.rect.centery, YELLOW, 20)
        elif powerup.type == 'bomb':
            self.player.bomb_count += 3
            self._add_particles(self.player.rect.centerx,
                                self.player.rect.centery, ORANGE, 15)
        elif powerup.type == 'missile':
            self.player.missile_count += 3
            self._add_particles(self.player.rect.centerx,
                                self.player.rect.centery, PURPLE, 15)
        elif powerup.type == 'energy':
            self.player.energy = self.player.max_energy
            self._add_particles(self.player.rect.centerx,
                                self.player.rect.centery, GREEN, 15)

    # ── Visual helpers ────────────────────────────────────────────

    def _add_explosion(self, x, y, size=40, damage=0, is_bomb=False):
        self.explosions.append(Explosion(x, y, size, damage, is_bomb))
        if size > 50:
            self.shake_timer = 20
            self.shake_intensity = size // 10

    def _add_particles(self, x, y, color, count=10, speed=5):
        for _ in range(count):
            self.particles.append(
                Particle(x, y, color, speed, random.randint(20, 40)))

    @staticmethod
    def _create_vignette():
        """Pre-render vignette surface at full alpha (scaled per frame)."""
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(40):
            a = int(120 * (1 - i / 40))
            pygame.draw.rect(surf, (200, 0, 0, a),
                             (i, i, SCREEN_WIDTH - 2 * i, SCREEN_HEIGHT - 2 * i), 3)
        return surf

    def _screen_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            intensity = self.shake_intensity * (self.shake_timer / 20)
            offset_x = random.randint(-int(intensity), int(intensity))
            offset_y = random.randint(-int(intensity), int(intensity))
            return (offset_x, offset_y)
        return (0, 0)

    # ── Draw ──────────────────────────────────────────────────────

    def draw(self, screen):
        shake = self._screen_shake()
        # Apply shake via offset (we draw everything offset)
        ox, oy = shake

        screen.fill(BLACK)

        # Background
        for star in self.stars:
            star.draw(screen, self.game_time)
        for nebula in self.nebulae:
            nebula.draw(screen)

        # Player
        screen.blit(self.player.image, (self.player.rect.x + ox, self.player.rect.y + oy))
        for flame in self.player.engine_flames:
            flame.draw(screen, ox, oy)
        self.player.draw_hit_effect(screen)

        # Enemies
        for enemy in self.enemies:
            screen.blit(enemy.image, (enemy.rect.x + ox, enemy.rect.y + oy))

        # Boss
        if self.boss:
            screen.blit(self.boss.image, (self.boss.rect.x + ox, self.boss.rect.y + oy))

        # Bullets
        for bullet in self.player_bullets:
            if hasattr(bullet, 'draw'):
                bullet.draw(screen, ox, oy)
            else:
                screen.blit(bullet.image, (bullet.rect.x + ox, bullet.rect.y + oy))
        for bullet in self.enemy_bullets:
            screen.blit(bullet.image, (bullet.rect.x + ox, bullet.rect.y + oy))

        # Missiles
        for missile in self.missiles:
            missile.draw(screen, ox, oy)

        # Power-ups
        for powerup in self.powerups:
            screen.blit(powerup.image, (powerup.rect.x + ox, powerup.rect.y + oy))

        # Explosions
        for explosion in self.explosions:
            explosion.draw(screen, ox, oy)

        # Particles
        for particle in self.particles:
            particle.draw(screen, ox, oy)

        # Laser beams
        for beam in self.laser_beams:
            beam.draw(screen)

        # Damage numbers
        for dn in self.damage_numbers:
            dn.draw(screen)

        # ── UI overlay ────────────────────────────────────────────

        # Health/Energy bars
        self.player.draw_health(screen)

        # Score / Level / Kills (top right)
        score_text = font_small.render(f"Score: {self.score:,}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 200, 15))
        level_text = font_small.render(f"Level: {self.level}", True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH - 200, 45))
        kills_text = font_small.render(f"Kills: {self.enemies_destroyed}", True, WHITE)
        screen.blit(kills_text, (SCREEN_WIDTH - 200, 75))

        # Combo
        if self.combo > 1:
            scale = min(1.5, 1.0 + self.combo * 0.02)
            combo_size = int(48 * scale)
            if not hasattr(self, '_combo_font') or self._combo_font_size != combo_size:
                self._combo_font = pygame.font.Font(None, combo_size)
                self._combo_font_size = combo_size
            combo_text = self._combo_font.render(f"COMBO x{self.combo}!", True, GOLD)
            screen.blit(combo_text,
                        (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 80))

        # Boss health bar
        if self.boss:
            self.boss.draw_health_bar(screen)

        # ── Post-processing effects ───────────────────────────────

        # Full-screen flash
        if self.flash_timer > 0:
            alpha = int(self.flash_alpha * (self.flash_timer / 20))
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, min(255, alpha)))
            screen.blit(flash_surf, (0, 0))

        # Vignette (red edge when hit)
        if self.vignette_timer > 0:
            alpha = int(255 * (self.vignette_timer / 20))
            self._vignette_surf.set_alpha(alpha)
            screen.blit(self._vignette_surf, (0, 0))

        # Achievement notifications (top center, fade in/out)
        for i, (title, timer) in enumerate(self.achievement_notifications[:3]):
            notif_y = 130 + i * 40
            alpha = min(255, timer * 4) if timer > 150 else min(255, (180 - timer) * 4)
            alpha = min(alpha, 255)
            notif_surf = pygame.Surface((400, 32), pygame.SRCALPHA)
            notif_surf.fill((20, 60, 20, min(180, alpha)))
            pygame.draw.rect(notif_surf, (80, 200, 80, min(200, alpha)),
                             (0, 0, 400, 32), 2)
            ach_text = font_tiny.render(f"Achievement: {title}", True, (100, 255, 100))
            if alpha < 255:
                ach_text.set_alpha(alpha)
            notif_surf.blit(ach_text, (10, 6))
            screen.blit(notif_surf, (SCREEN_WIDTH // 2 - 200, notif_y))
