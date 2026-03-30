import json
import pygame
import random
from sources.entities import Player, Enemy, Bonus, BlockCoin, Cloud, Goal, get_image


class Block(pygame.sprite.Sprite):
    def __init__(self, pos, size, tile_type, settings):
        super().__init__()
        self.tile_type = tile_type
        self.is_empty = False

        images = settings.get("assets", {}).get("images", {})

        if tile_type == "X":
            self.image = get_image(
                images.get("block", "icons/block.png"), (size, size), (139, 69, 19)
            )
        elif tile_type == "?":
            self.image = get_image(
                images.get("lucky_block", "icons/lucky_block.png"),
                (size, size),
                (255, 215, 0),
            )

        self.rect = self.image.get_rect(topleft=pos)

    def update(self, x_shift):
        self.rect.x += x_shift


class Level:
    def __init__(self, level_data_path, settings, sounds):
        self.display_surface = pygame.display.get_surface()
        self.settings = settings
        self.sounds = sounds

        self.blocks = pygame.sprite.Group()
        self.player = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.bonuses = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()
        self.goal = pygame.sprite.GroupSingle()

        self.world_shift = 0
        self.world_offset = 0
        self.paused = False
        self.is_completed = False
        self.level_width = 0
        self.time_left = 60
        self.setup_level(level_data_path)

    def setup_level(self, path):
        with open(path, "r") as f:
            level_data = json.load(f)

        layout = level_data["map"]

        for row_index, row in enumerate(layout):
            for col_index, cell in enumerate(row):
                x = col_index * self.settings["block_size"]
                y = row_index * self.settings["block_size"]

                if cell in ["X", "?"]:
                    tile = Block(
                        (x, y), self.settings["block_size"], cell, self.settings
                    )
                    self.blocks.add(tile)
                elif cell == "P":
                    player_sprite = Player((x, y), self.settings, self.sounds)
                    self.player.add(player_sprite)
                elif cell == "E":
                    enemy = Enemy((x, y), self.settings)
                    self.enemies.add(enemy)
                elif cell == "C":
                    bonus = Bonus((x, y), "coin", self.settings)
                    self.bonuses.add(bonus)
                elif cell == "M":
                    bonus = Bonus((x, y), "mushroom", self.settings)
                    self.bonuses.add(bonus)
                elif cell == "T":
                    bonus = Bonus((x, y), "time", self.settings)
                    self.bonuses.add(bonus)
                elif cell == "F":
                    finish = Goal((x, y), self.settings)
                    self.goal.add(finish)

        self.level_width = (
            len(layout[0]) * self.settings["block_size"] if layout else 2000
        )
        screen_width = self.settings.get("width", 800)
        for _ in range(6):
            x = random.randint(0, screen_width + 400)
            y = random.randint(20, 150)
            self.clouds.add(Cloud((x, y)))

    def horizontal_movement_collision(self):
        player = self.player.sprite
        if player.state == "dead":
            return

        player.rect.x += player.direction.x * player.speed
        for sprite in pygame.sprite.spritecollide(player, self.blocks, False):
            if player.direction.x < 0:
                player.rect.left = sprite.rect.right
            elif player.direction.x > 0:
                player.rect.right = sprite.rect.left

    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()
        if player.state == "dead":
            return

        collided_sprites = pygame.sprite.spritecollide(player, self.blocks, False)

        if player.direction.y < 0:
            for sprite in collided_sprites:
                if (
                    sprite.tile_type == "?"
                    and not sprite.is_empty
                    and sprite.rect.collidepoint(player.rect.midtop)
                ):
                    sprite.is_empty = True
                    images = self.settings.get("assets", {}).get("images", {})
                    sprite.image = get_image(
                        images.get("block", "icons/block.png"),
                        (sprite.rect.width, sprite.rect.height),
                        (139, 69, 19),
                    )

                    coin_effect = BlockCoin(sprite.rect.center, self.settings)
                    self.effects.add(coin_effect)
                    player.score += 100
                    if "coin" in self.sounds:
                        self.sounds["coin"].play()

                    player.rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    return
                
        for sprite in collided_sprites:
            if player.direction.y > 0:
                player.rect.bottom = sprite.rect.top
                player.direction.y = 0
                player.on_ground = True
            elif player.direction.y < 0:
                player.rect.top = sprite.rect.bottom
                player.direction.y = 0

        if player.on_ground and player.direction.y > player.gravity:
            player.on_ground = False

    def check_bonus_collisions(self):
        player = self.player.sprite
        if player.state == "dead":
            return

        collided_bonuses = pygame.sprite.spritecollide(player, self.bonuses, True)
        for bonus in collided_bonuses:
            if bonus.type == "coin":
                player.score += 100
                if "coin" in self.sounds:
                    self.sounds["coin"].play()
            elif bonus.type == "mushroom":
                player.is_super = True
                player.jump_power = player.base_jump_power - 4
                player.powerup_timer = pygame.time.get_ticks() + 15000
                player.score += 500
                if "powerup" in self.sounds:
                    self.sounds["powerup"].play()
            elif bonus.type == "time":
                self.time_left += 10
                player.score += 200
                if "powerup" in self.sounds:
                    self.sounds["powerup"].play()

    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        screen_width = self.settings["width"]
        left_bound = screen_width // 4
        right_bound = screen_width - (screen_width // 4)

        if player_x < left_bound and direction_x < 0:
            self.world_shift = player.settings.get("player_speed", 5)
            player.speed = 0

        elif player_x > right_bound and direction_x > 0:
            self.world_shift = -player.settings.get("player_speed", 5)
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = player.settings.get("player_speed", 5)

        self.world_offset -= self.world_shift

    def enemy_physics(self):
        for enemy in self.enemies.sprites():
            enemy.rect.x += enemy.speed * enemy.direction
            for sprite in pygame.sprite.spritecollide(enemy, self.blocks, False):
                if enemy.direction > 0:
                    enemy.rect.right = sprite.rect.left
                elif enemy.direction < 0:
                    enemy.rect.left = sprite.rect.right
                enemy.reverse()

            if enemy.direction_y == 0:
                check_x = (
                    enemy.rect.right + 2 if enemy.direction > 0 else enemy.rect.left - 2
                )
                check_y = enemy.rect.bottom + 2

                has_ground = any(
                    sprite.rect.collidepoint(check_x, check_y)
                    for sprite in self.blocks.sprites()
                )

                if not has_ground:
                    enemy.rect.x -= enemy.speed * enemy.direction
                    enemy.reverse()

            enemy.direction_y += enemy.gravity
            enemy.rect.y += enemy.direction_y
            for sprite in pygame.sprite.spritecollide(enemy, self.blocks, False):
                if enemy.direction_y > 0:
                    enemy.rect.bottom = sprite.rect.top
                    enemy.direction_y = 0

    def check_enemy_collisions(self):
        player = self.player.sprite
        if player.state == "dead":
            return

        collided_enemies = pygame.sprite.spritecollide(player, self.enemies, False)
        if collided_enemies:
            for enemy in collided_enemies:
                if player.direction.y > 0 and player.rect.bottom <= enemy.rect.centery:
                    enemy.kill()
                    player.score += 200
                    player.direction.y = player.jump_power / 1.5
                    if "stomp" in self.sounds:
                        self.sounds["stomp"].play()
                else:
                    if player.state != "dead":
                        player.die()

    def draw_pause_screen(self):
        overlay = pygame.Surface(
            (self.settings["width"], self.settings["height"]), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 128))
        self.display_surface.blit(overlay, (0, 0))

        font = pygame.font.SysFont("Arial", 64, bold=True)
        text_surf = font.render("PAUSE", True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(self.settings["width"] // 2, self.settings["height"] // 2)
        )
        self.display_surface.blit(text_surf, text_rect)

    def run(self):
        player = self.player.sprite
        self.display_surface.fill((135, 206, 235))

        if not self.paused:
            if player.state != "dead" and not self.is_completed:
                self.time_left -= 1 / self.settings.get("fps", 60)
                if self.time_left <= 0:
                    self.time_left = 0
                    player.die()

            self.clouds.update(self.world_shift)
            self.blocks.update(self.world_shift)
            self.enemies.update(self.world_shift)
            self.bonuses.update(self.world_shift)
            self.effects.update(self.world_shift)
            self.goal.update(self.world_shift)

            player.update()
            self.scroll_x()
            self.horizontal_movement_collision()
            self.vertical_movement_collision()

            self.enemy_physics()
            self.check_enemy_collisions()
            self.check_bonus_collisions()

        self.clouds.draw(self.display_surface)
        self.effects.draw(self.display_surface)
        self.goal.draw(self.display_surface)
        self.blocks.draw(self.display_surface)
        self.enemies.draw(self.display_surface)
        self.bonuses.draw(self.display_surface)
        self.player.draw(self.display_surface)

        if self.paused:
            self.draw_pause_screen()

        if self.goal.sprite and player.rect.centerx >= self.goal.sprite.rect.centerx:
            self.is_completed = True
        elif (
            not self.goal.sprite
            and player.rect.x + self.world_offset >= self.level_width
        ):
            self.is_completed = True
