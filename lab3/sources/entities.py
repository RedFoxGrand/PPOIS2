import pygame
import math
import random

IMAGE_CACHE = {}


def get_image(path, size, color):
    key = (path, size)
    if key not in IMAGE_CACHE:
        try:
            image = pygame.image.load(path).convert_alpha()
            IMAGE_CACHE[key] = pygame.transform.scale(image, size)
        except FileNotFoundError:
            surf = pygame.Surface(size)
            surf.fill(color)
            IMAGE_CACHE[key] = surf
    return IMAGE_CACHE[key]


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, settings, sounds):
        super().__init__()
        self.settings = settings
        self.sounds = sounds
        self.score = 0
        self.animation_timer = 0

        images = self.settings.get("assets", {}).get("images", {})
        self.frames = [
            get_image(
                images.get("standing_mario", "icons/standing_mario.png"), (32, 64), (255, 0, 0)
            ),
            get_image(
                images.get("running_mario", "icons/running_mario.png"), (45, 64), (200, 0, 0)
            ),
        ]
        self.frames_super = [
            get_image(
                images.get("standing_super_mario", "icons/standing_super_mario.png"),
                (45, 64),
                (0, 255, 0),
            ),
            get_image(
                images.get("running_super_mario", "icons/running_super_mario.png"),
                (45, 64),
                (0, 200, 0),
            ),
        ]
        self.image_dead = get_image(
            images.get("dead_mario", "icons/dead_mario.png"), (64, 32), (100, 100, 100)
        )
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=pos)

        self.direction = pygame.math.Vector2(0, 0)
        self.speed = settings.get("player_speed", 5)
        self.gravity = settings.get("gravity", 0.5)
        self.jump_power = settings.get("jump_power", -10)
        self.base_jump_power = self.jump_power
        self.powerup_timer = 0
        self.is_super = False
        self.facing_right = True
        self.state = "idle"
        self.on_ground = False

    def get_input(self):
        if self.state == "dead":
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.state = "running"
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.state = "running"
        else:
            self.direction.x = 0
            if self.on_ground:
                self.state = "idle"
        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.jump()

    def jump(self):
        self.direction.y = self.jump_power
        self.state = "jumping"
        self.on_ground = False

        if "jump" in self.sounds:
            self.sounds["jump"].play()

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.rect.y += self.direction.y

    def die(self):
        self.state = "dead"
        self.direction.x = 0
        self.direction.y = -12
        self.image = self.image_dead

    def update(self):
        if self.state != "dead":
            self.get_input()

            if self.direction.x > 0:
                self.facing_right = True
            elif self.direction.x < 0:
                self.facing_right = False

            if self.is_super and pygame.time.get_ticks() > self.powerup_timer:
                self.jump_power = self.base_jump_power
                self.is_super = False
                print("Действие гриба закончилось!")

            active_frames = self.frames_super if self.is_super else self.frames
            if self.state == "running":
                self.animation_timer += 0.15
                if self.animation_timer >= len(active_frames):
                    self.animation_timer = 0
                self.image = active_frames[int(self.animation_timer)]
            else:
                self.image = active_frames[0]

            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, settings):
        super().__init__()

        images = settings.get("assets", {}).get("images", {})
        self.image = get_image(
            images.get("enemy", "icons/enemy.png"), (32, 32), (0, 0, 255)
        )
        self.rect = self.image.get_rect(topleft=pos)

        self.speed = 2
        self.direction = 1
        self.direction_y = 0
        self.gravity = settings.get("gravity", 0.5)

    def reverse(self):
        self.direction *= -1

    def update(self, x_shift):
        self.rect.x += x_shift


class Bonus(pygame.sprite.Sprite):
    def __init__(self, pos, bonus_type, settings):
        super().__init__()
        self.type = bonus_type
        images = settings.get("assets", {}).get("images", {})

        if self.type == "coin":
            self.image = get_image(
                images.get("coin", "icons/coin.png"), (30, 30), (255, 255, 0)
            )
        elif self.type == "mushroom":
            self.image = get_image(
                images.get("mushroom", "icons/mushroom.png"), (30, 30), (0, 255, 0)
            )
        elif self.type == "time":
            self.image = get_image(
                images.get("time", "icons/time.png"), (30, 30), (0, 255, 255)
            )

        self.rect = self.image.get_rect(topleft=pos)

        self.base_y = self.rect.y
        self.animation_timer = 0

    def update(self, x_shift):
        self.rect.x += x_shift

        self.animation_timer += 0.1
        self.rect.y = self.base_y + math.sin(self.animation_timer) * 4


class BlockCoin(pygame.sprite.Sprite):
    def __init__(self, center_pos, settings):
        super().__init__()
        images = settings.get("assets", {}).get("images", {})
        self.image = get_image(
            images.get("coin", "icons/coin.png"), (32, 32), (255, 255, 0)
        )

        self.rect = self.image.get_rect(center=center_pos)
        self.exact_y = float(self.rect.y)
        self.start_y = self.rect.y
        self.y_speed = -8
        self.gravity = settings.get("gravity", 0.5)

    def update(self, x_shift):
        self.rect.x += x_shift
        self.y_speed += self.gravity
        self.exact_y += self.y_speed
        self.rect.y = int(self.exact_y)

        if self.rect.y >= self.start_y and self.y_speed > 0:
            self.kill()


class Cloud(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((100, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 255, 255, 220), (0, 20, 50, 40))
        pygame.draw.ellipse(self.image, (255, 255, 255, 220), (25, 0, 50, 60))
        pygame.draw.ellipse(self.image, (255, 255, 255, 220), (50, 20, 50, 40))
        self.rect = self.image.get_rect(topleft=pos)
        self.wind_speed = random.uniform(0.3, 0.8)
        self.floating_x = float(self.rect.x)

    def update(self, x_shift):
        self.floating_x -= self.wind_speed
        self.floating_x += x_shift
        self.rect.x = int(self.floating_x)

        if self.rect.right < -100:
            self.floating_x = random.randint(1000, 1400)
            self.rect.x = int(self.floating_x)
            self.rect.y = random.randint(20, 200)


class Goal(pygame.sprite.Sprite):
    def __init__(self, pos, settings):
        super().__init__()
        images = settings.get("assets", {}).get("images", {})
        self.image = get_image(
            images.get("finish", "icons/finish.png"), (48, 64), (0, 255, 255)
        )
        self.rect = self.image.get_rect(topleft=pos)

    def update(self, x_shift):
        self.rect.x += x_shift
