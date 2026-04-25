import pygame
import random
import math

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED, GREEN, YELLOW,
    CYAN, ORANGE, PURPLE, GOLD, SILVER,
    font_large, font_medium, font_small, clock, FPS, screen,
)
from background import Star, Nebula
from effects import Explosion, LaserBeam, Particle
from player import Player
from enemies import Enemy, EnemyBullet, Boss
from weapons import Bomb


class Game:
    def __init__(self):
        self.reset_game()
        self.high_score = self.load_high_score()

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

        # Create player
        self.player = Player()

        # Enemy spawn
        self.enemy_timer = 0
        self.enemy_spawn_delay = 1200
        self.enemies_to_spawn = []

        # Boss
        self.boss = None
        self.boss_timer = 0
        self.boss_spawn_delay = 45000  # 45 seconds

        # Combo
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.total_kills = 0

        # Game state
        self.game_state = "start"
        self.paused = False
        self.game_time = 0

        # Screen shake
        self.shake_timer = 0
        self.shake_intensity = 0

    def load_high_score(self):
        try:
            with open('highscore.txt', 'r') as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def save_high_score(self):
        try:
            with open('highscore.txt', 'w') as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.enemies_destroyed = 0

    def spawn_enemy(self):
        if self.level >= 5:
            weights = [30, 40, 25, 5]
        elif self.level >= 3:
            weights = [40, 35, 20, 5]
        else:
            weights = [60, 30, 10, 0]

        enemy_type = random.choices([0, 1, 2, 3], weights=weights)[0]
        enemy = Enemy(enemy_type)
        self.enemies.add(enemy)

    def spawn_boss(self):
        self.boss = Boss()
        self.boss_timer = 0

    def add_explosion(self, x, y, size=40, damage=0, is_bomb=False):
        self.explosions.append(Explosion(x, y, size, damage, is_bomb))
        if size > 50:
            self.shake_timer = 20
            self.shake_intensity = size // 10

    def add_particles(self, x, y, color, count=10, speed=5):
        for _ in range(count):
            self.particles.append(
                Particle(x, y, color, speed, random.randint(20, 40)))

    def spawn_enemy_bullet(self, x, y, angle_x=0, speed=6, color=RED, damage=15):
        bullet = EnemyBullet(x, y, angle_x, speed, color, damage)
        self.enemy_bullets.add(bullet)

    def screen_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            return (offset_x, offset_y)
        return (0, 0)

    def check_collisions(self):
        # Player bullets hit enemies (swept collision for fast-moving bullets)
        hit_enemies = {}
        for bullet in list(self.player_bullets):
            # Expand rect downward to cover the bullet's travel path this frame
            expanded = pygame.Rect(
                bullet.rect.x, bullet.rect.y,
                bullet.rect.width, bullet.rect.height + abs(bullet.speed)
            )
            for enemy in self.enemies:
                if expanded.colliderect(enemy.rect):
                    hit_enemies.setdefault(enemy, []).append(bullet)

        for enemy, bullets in hit_enemies.items():
            for bullet in bullets:
                bullet.kill()

            damage = sum(b.damage for b in bullets)
            if enemy.take_damage(damage):
                self.add_explosion(enemy.rect.centerx, enemy.rect.centery,
                                 40 if enemy.enemy_type >= 2 else 25)
                self.add_particles(enemy.rect.centerx, enemy.rect.centery, ORANGE, 15)

                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                self.combo_timer = pygame.time.get_ticks()
                self.total_kills += 1

                multiplier = 1 + min(self.combo / 10, 5)
                self.score += int(enemy.score_value * multiplier)

                if random.random() < 0.2:
                    powerup = self._create_powerup(enemy.rect.center)
                    self.powerups.add(powerup)

                enemy.kill()
                self.enemies_destroyed += 1

        # Missiles hit enemies
        for missile in list(self.missiles):
            hits = pygame.sprite.spritecollide(missile, self.enemies, True)
            if hits:
                self.add_explosion(missile.rect.centerx, missile.rect.centery, 80, 100)
                self.add_particles(missile.rect.centerx, missile.rect.centery, RED, 30)
                missile.kill()
                for enemy in hits:
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    self.score += enemy.score_value

        # Boss collisions
        if self.boss:
            for projectile_group in [self.player_bullets, self.missiles]:
                for proj in list(projectile_group):
                    if self.boss.rect.colliderect(proj.rect):
                        proj.kill()
                        if self.boss.take_damage(proj.damage):
                            self.add_explosion(self.boss.rect.centerx,
                                             self.boss.rect.centery, 150)
                            self.add_particles(self.boss.rect.centerx,
                                             self.boss.rect.centery, GOLD, 50)
                            self.score += self.boss.score_value
                            self.shake_timer = 60
                            self.shake_intensity = 10
                            self.boss = None
                            break

        # Enemies hit player
        hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for enemy in hits:
            if not self.player.invincible:
                damage = 30 + enemy.enemy_type * 10
                self.player.health -= damage
                self.player.invincible = True
                self.player.invincible_timer = 90
                self.player.hit_effect_timer = 30
                self.add_explosion(self.player.rect.centerx,
                                 self.player.rect.centery, 50)
                self.shake_timer = 15
                self.shake_intensity = 5

        # Enemy bullets hit player
        hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for bullet in hits:
            if not self.player.invincible:
                damage = getattr(bullet, 'damage', 15)
                self.player.health -= damage
                self.player.invincible = True
                self.player.invincible_timer = 45
                self.player.hit_effect_timer = 15
                self.add_particles(self.player.rect.centerx,
                                 self.player.rect.centery, RED, 10)

        # Bombs
        for bomb in list(self.bombs):
            if bomb.should_explode():
                explosion = bomb.explode()
                self.explosions.append(explosion)
                self.shake_timer = 30
                self.shake_intensity = 8

                for enemy in list(self.enemies):
                    dist = math.hypot(
                        enemy.rect.centerx - bomb.rect.centerx,
                        enemy.rect.centery - bomb.rect.centery)
                    if dist < explosion.size:
                        if enemy.take_damage(explosion.damage):
                            self.add_explosion(enemy.rect.centerx,
                                             enemy.rect.centery, 30)
                            self.combo += 1
                            self.max_combo = max(self.max_combo, self.combo)
                            self.score += enemy.score_value
                            self.enemies_destroyed += 1
                            enemy.kill()
                bomb.kill()

        # Player collects power-ups
        hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in hits:
            self._apply_powerup(powerup)

        # Laser beam damage
        for beam in self.laser_beams:
            damage_rect = beam.get_damage_rect()
            if damage_rect and not self.player.invincible:
                if damage_rect.colliderect(self.player.rect):
                    self.player.health -= beam.damage
                    self.player.hit_effect_timer = 5

    def _create_powerup(self, center):
        from weapons import PowerUp
        return PowerUp(center)

    def _apply_powerup(self, powerup):
        if powerup.type == 'health':
            self.player.health = min(
                self.player.health + 40, self.player.max_health)
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, GREEN, 20)
        elif powerup.type == 'shield':
            self.player.shield = min(
                self.player.shield + 50, self.player.max_shield)
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, CYAN, 20)
        elif powerup.type == 'power':
            self.player.power_level = min(
                self.player.power_level + 1, 3)
            self.player.power_timer = pygame.time.get_ticks()
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, YELLOW, 20)
        elif powerup.type == 'bomb':
            self.player.bomb_count += 3
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, ORANGE, 15)
        elif powerup.type == 'missile':
            self.player.missile_count += 3
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, PURPLE, 15)
        elif powerup.type == 'energy':
            self.player.energy = self.player.max_energy
            self.add_particles(self.player.rect.centerx,
                             self.player.rect.centery, GREEN, 15)

    def update(self):
        if self.game_state != "playing" or self.paused:
            return

        self.game_time += 1

        # Update background
        time_offset = self.game_time
        for star in self.stars:
            star.update()
        for nebula in self.nebulae:
            nebula.update()

        # Update sprites
        self.player.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.missiles.update()
        self.bombs.update()

        # Update explosions
        self.explosions = [e for e in self.explosions if e.update()]
        self.particles = [p for p in self.particles if p.update()]
        self.laser_beams = [b for b in self.laser_beams if b.update()]

        # Player shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            bullets = self.player.shoot()
            for bullet in bullets:
                self.player_bullets.add(bullet)

        # Enemy spawning (frames between spawns, scales with difficulty)
        self.enemy_timer += 1
        spawn_delay = max(30, 90 - self.level * 5)
        if self.enemy_timer >= spawn_delay:
            if not self.boss:
                self.spawn_enemy()
            self.enemy_timer = 0

        # Boss spawning
        if self.boss is None and self.level >= 3:
            self.boss_timer += 1
            if self.boss_timer >= self.boss_spawn_delay:
                self.spawn_boss()
                self.boss_timer = 0

        # Enemy shooting
        for enemy in self.enemies:
            if enemy.can_shoot() and not self.boss:
                bullet_type = random.randint(0, 10)
                if bullet_type < 7:
                    self.spawn_enemy_bullet(enemy.rect.centerx, enemy.rect.bottom)
                else:
                    self.spawn_enemy_bullet(enemy.rect.centerx, enemy.rect.bottom,
                                          random.randint(-2, 2), 8, RED)

        # Boss attacks
        if self.boss:
            self.boss.update(self.player)
            if self.boss.can_attack():
                attack = self.boss.attack_pattern

                if attack == 0:
                    for angle in [-30, -15, 0, 15, 30]:
                        self.spawn_enemy_bullet(
                            self.boss.rect.centerx, self.boss.rect.bottom,
                            math.sin(math.radians(angle)) * 3, 6, PURPLE, 20)

                elif attack == 1:
                    dx = self.player.rect.centerx - self.boss.rect.centerx
                    horizontal_dist = max(abs(dx), 1)
                    self.spawn_enemy_bullet(
                        self.boss.rect.centerx, self.boss.rect.bottom,
                        dx / horizontal_dist * 5, 8, RED, 30)

                elif attack == 2:
                    beam = LaserBeam(
                        self.boss.rect.centerx, self.boss.rect.bottom + 50)
                    self.laser_beams.append(beam)

                else:
                    for i in range(8):
                        angle = i * 45 + self.game_time * 2
                        self.spawn_enemy_bullet(
                            self.boss.rect.centerx, self.boss.rect.bottom,
                            math.cos(math.radians(angle)) * 4,
                            math.sin(math.radians(angle)) * 4,
                            CYAN, 15)

        # Collision detection
        self.check_collisions()

        # Combo timer
        if self.combo > 0:
            if pygame.time.get_ticks() - self.combo_timer > 2000:
                self.combo = 0

        # Level up
        if self.enemies_destroyed >= self.level * 25:
            self.level += 1
            self.player.health = min(
                self.player.health + 30, self.player.max_health)
            self.player.shield = self.player.max_shield
            self.add_particles(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GOLD, 50)

        # Game over
        if self.player.health <= 0 and self.game_state == "playing":
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            self.game_state = "gameover"
            self.add_explosion(self.player.rect.centerx,
                             self.player.rect.centery, 100)

    def draw_start_screen(self):
        screen.fill(BLACK)

        for star in self.stars:
            star.draw(screen, self.game_time)
        for nebula in self.nebulae:
            nebula.draw(screen)

        title_glow = int(math.sin(self.game_time * 0.05) * 30 + 200)
        title = font_large.render("STAR WARS", True,
                                  (title_glow, title_glow, 0))
        screen.blit(title,
                   (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        title2 = font_large.render("GALAXY BATTLE", True, YELLOW)
        screen.blit(title2,
                   (SCREEN_WIDTH // 2 - title2.get_width() // 2, 200))

        subtitle = font_medium.render("A Space Shooter Epic", True, CYAN)
        screen.blit(subtitle,
                   (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 290))

        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 350, 400, 280)
        pygame.draw.rect(screen, (20, 20, 40), box_rect)
        pygame.draw.rect(screen, CYAN, box_rect, 2)

        instructions = [
            "CONTROLS",
            "Arrow Keys - Move",
            "Space - Shoot",
            "M - Launch Missile",
            "B - Drop Bomb",
            "P - Pause",
            "ESC - Exit",
            "",
            "Press SPACE to Start",
        ]

        for i, text in enumerate(instructions):
            color = YELLOW if i == 0 else (GREEN if "Press" in text else WHITE)
            rendered = font_small.render(text, True, color)
            screen.blit(rendered,
                       (SCREEN_WIDTH // 2 - rendered.get_width() // 2,
                        365 + i * 28))

        if self.high_score > 0:
            hs_text = font_medium.render(
                f"High Score: {self.high_score:,}", True, GOLD)
            screen.blit(hs_text,
                       (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 680))

    def draw_game_screen(self):
        # Apply screen shake
        shake = self.screen_shake()

        screen.fill(BLACK)
        for star in self.stars:
            star.draw(screen, self.game_time)
        for nebula in self.nebulae:
            nebula.draw(screen)

        # Draw player
        screen.blit(self.player.image, self.player.rect)
        for flame in self.player.engine_flames:
            flame.draw(screen)
        self.player.draw_hit_effect(screen)

        # Draw enemies
        for enemy in self.enemies:
            screen.blit(enemy.image, enemy.rect)

        # Draw boss
        if self.boss:
            screen.blit(self.boss.image, self.boss.rect)

        # Draw bullets with trails
        for bullet in self.player_bullets:
            if hasattr(bullet, 'draw'):
                bullet.draw(screen)
            else:
                screen.blit(bullet.image, bullet.rect)

        for bullet in self.enemy_bullets:
            screen.blit(bullet.image, bullet.rect)

        # Draw missiles
        for missile in self.missiles:
            missile.draw(screen)

        # Draw powerups
        for powerup in self.powerups:
            screen.blit(powerup.image, powerup.rect)

        # Draw explosions
        for explosion in self.explosions:
            explosion.draw(screen)

        # Draw particles
        for particle in self.particles:
            particle.draw(screen)

        # Draw laser beams
        for beam in self.laser_beams:
            beam.draw(screen)

        # UI
        self.player.draw_health(screen)

        score_text = font_small.render(f"Score: {self.score:,}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 200, 15))

        level_text = font_small.render(f"Level: {self.level}", True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH - 200, 45))

        kills_text = font_small.render(
            f"Kills: {self.enemies_destroyed}", True, WHITE)
        screen.blit(kills_text, (SCREEN_WIDTH - 200, 75))

        if self.combo > 1:
            combo_text = font_medium.render(
                f"COMBO x{self.combo}!", True, GOLD)
            screen.blit(combo_text,
                       (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 80))

        if self.boss:
            self.boss.draw_health_bar(screen)

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))
            pause_text = font_large.render("PAUSED", True, WHITE)
            screen.blit(pause_text,
                       (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                        SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))

    def draw_gameover_screen(self):
        screen.fill(BLACK)

        for star in self.stars:
            star.draw(screen, self.game_time)

        go_text = font_large.render("GAME OVER", True, RED)
        screen.blit(go_text,
                   (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 150))

        score_text = font_medium.render(
            f"Final Score: {self.score:,}", True, WHITE)
        screen.blit(score_text,
                   (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 260))

        stats = [
            f"Level Reached: {self.level}",
            f"Enemies Destroyed: {self.enemies_destroyed}",
            f"Max Combo: {self.max_combo}",
        ]
        for i, stat in enumerate(stats):
            text = font_small.render(stat, True, SILVER)
            screen.blit(text,
                       (SCREEN_WIDTH // 2 - text.get_width() // 2,
                        330 + i * 35))

        if self.score >= self.high_score and self.score > 0:
            new_hs = font_medium.render("NEW HIGH SCORE!", True, GOLD)
            screen.blit(new_hs,
                       (SCREEN_WIDTH // 2 - new_hs.get_width() // 2, 450))
        else:
            hs_text = font_small.render(
                f"High Score: {self.high_score:,}", True, CYAN)
            screen.blit(hs_text,
                       (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 460))

        restart_text = font_medium.render(
            "Press SPACE to Restart", True, GREEN)
        screen.blit(restart_text,
                   (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 550))

        back_text = font_small.render(
            "Press ESC for Main Menu", True, WHITE)
        screen.blit(back_text,
                   (SCREEN_WIDTH // 2 - back_text.get_width() // 2, 610))

    def draw(self):
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state == "playing":
            self.draw_game_screen()
        elif self.game_state == "gameover":
            self.draw_gameover_screen()

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.paused = not self.paused
                    elif self.game_state == "gameover":
                        self.game_state = "start"
                        self.reset_game()
                    else:
                        return False

                if self.game_state == "start" and event.key == pygame.K_SPACE:
                    self.game_state = "playing"

                if self.game_state == "gameover" and event.key == pygame.K_SPACE:
                    self._restart_game()

                if event.key == pygame.K_p and self.game_state == "playing":
                    self.paused = not self.paused

                if event.key == pygame.K_m and self.game_state == "playing" and not self.paused:
                    from weapons import Missile
                    missile = self.player.shoot_missile()
                    if missile:
                        self.missiles.add(missile)

                if event.key == pygame.K_b and self.game_state == "playing" and not self.paused:
                    bomb = self.player.drop_bomb()
                    if bomb:
                        self.bombs.add(bomb)

        return True

    def _restart_game(self):
        self.reset_game()
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.powerups.empty()
        self.missiles.empty()
        self.bombs.empty()
        self.explosions.clear()
        self.particles.clear()
        self.laser_beams.clear()
        self.boss = None
        self.player = Player()
        self.game_state = "playing"
        self.max_combo = 0

    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        import sys
        sys.exit()