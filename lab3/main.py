import pygame
import sys
import json
from sources.level_parser import Level
from sources.records import RecordsManager


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.settings = self.load_settings("sources/json/settings.json")
        self.flags = pygame.RESIZABLE | pygame.SCALED
        self.screen = pygame.display.set_mode(
            (self.settings["width"], self.settings["height"]), self.flags
        )
        self.is_fullscreen = False
        pygame.display.set_caption("Super Mario Bros")
        self.clock = pygame.time.Clock()

        self.sounds = {}
        assets_sounds = self.settings.get("assets", {}).get("sounds", {})
        try:
            self.sounds["jump"] = pygame.mixer.Sound(
                assets_sounds.get("jump", "music/jump.wav")
            )
            self.sounds["coin"] = pygame.mixer.Sound(
                assets_sounds.get("coin", "music/coin.wav")
            )
            self.sounds["powerup"] = pygame.mixer.Sound(
                assets_sounds.get("powerup", "music/powerup.wav")
            )
            self.sounds["stomp"] = pygame.mixer.Sound(
                assets_sounds.get("stomp", "music/stomp.wav")
            )
            for sound in self.sounds.values():
                sound.set_volume(0.2)
        except (FileNotFoundError, pygame.error) as e:
            print(f"Проблема со звуковыми файлами ({e}). Запуск без звука.")

        pygame.font.init()
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 24)

        self.records_manager = RecordsManager()
        self.player_name_input = ""
        self.final_score = 0

        self.backgrounds = {}
        images = self.settings.get("assets", {}).get("images", {})
        screen_size = (self.settings["width"], self.settings["height"])
        for state_key, image_key, default_path in [
            ("menu", "menu_miniature", "icons/menu_miniature.png"),
            ("level_completed", "victory_miniature", "icons/victory_miniature.png"),
            ("game_over", "defeat_miniature", "icons/defeat_miniature.png"),
            ("records", "records_miniature", "icons/records_miniature.png"),
            ("help", "help_miniature", "icons/help_miniature.png"),
            ("name_input", "new_record_miniature", "icons/new_record_miniature.png"),
        ]:
            try:
                image = pygame.image.load(images.get(image_key, default_path)).convert()
                scaled_image = pygame.transform.scale(image, screen_size)
                scaled_image.set_alpha(128)
                self.backgrounds[state_key] = scaled_image
            except (FileNotFoundError, pygame.error):
                self.backgrounds[state_key] = None

        self.current_music = None
        self.level = None
        self.set_state("menu")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        pygame.display.toggle_fullscreen()

    def load_settings(self, filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"width": 800, "height": 600, "fps": 60}

    def change_music(self, track_key, loops=-1):
        if self.current_music == track_key:
            return
        self.current_music = track_key
        assets_sounds = self.settings.get("assets", {}).get("sounds", {})
        defaults = {
            "theme": "music/theme.mp3",
            "menu_theme": "music/menu_theme.mp3",
            "victory_theme": "music/victory_theme.mp3",
            "defeat_theme": "music/defeat_theme.mp3",
        }
        track_path = assets_sounds.get(track_key, defaults.get(track_key))
        if track_path:
            try:
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(loops)
            except (FileNotFoundError, pygame.error) as e:
                print(f"Не удалось загрузить музыку {track_path}: {e}")

    def set_state(self, new_state):
        self.state = new_state
        if new_state in ["menu", "records", "help", "name_input"]:
            self.change_music("menu_theme")
        elif new_state == "playing":
            self.change_music("theme")
        elif new_state == "level_completed":
            self.change_music("victory_theme", 0)
        elif new_state == "game_over":
            self.change_music("defeat_theme", 0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()

                if self.state == "menu":
                    if event.key == pygame.K_RETURN:
                        self.set_state("playing")
                        self.level = Level("sources/json/level1.json", self.settings, self.sounds)
                    elif event.key == pygame.K_h:
                        self.set_state("help")
                    elif event.key == pygame.K_r:
                        self.set_state("records")
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif self.state in ["help", "records"]:
                    if event.key == pygame.K_ESCAPE:
                        self.set_state("menu")

                elif self.state in ["level_completed", "game_over"]:
                    if event.key == pygame.K_RETURN:
                        if self.records_manager.is_new_record(self.final_score):
                            self.set_state("name_input")
                        else:
                            self.set_state("menu")

                elif self.state == "name_input":
                    if event.key == pygame.K_RETURN:
                        name = (
                            self.player_name_input
                            if self.player_name_input
                            else "Player"
                        )
                        self.records_manager.add_record(name, self.final_score)
                        self.player_name_input = ""
                        self.set_state("menu")
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name_input = self.player_name_input[:-1]
                    else:
                        if len(self.player_name_input) < 15:
                            self.player_name_input += event.unicode

                elif self.state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        self.level.paused = not self.level.paused

    def update(self):
        if self.state == "playing":
            if self.level.player.sprite.rect.y > self.settings["height"]:
                self.final_score = self.level.player.sprite.score
                self.set_state("game_over")

            elif self.level.is_completed:
                self.final_score = self.level.player.sprite.score
                self.set_state("level_completed")

    def draw_text_centered(self, text_surface, y):
        x = self.settings["width"] // 2 - text_surface.get_width() // 2
        self.screen.blit(text_surface, (x, y))

    def draw(self):
        self.screen.fill((30, 30, 30))

        if self.state == "menu":
            if self.backgrounds.get("menu"):
                self.screen.blit(self.backgrounds["menu"], (0, 0))

            title = self.font_large.render("SUPER MARIO BROS", True, (0, 255, 0))
            start_btn = self.font_small.render(
                "Нажмите ENTER чтобы начать игру", True, (255, 255, 255)
            )
            records_btn = self.font_small.render(
                "Нажмите R для рекордов", True, (255, 255, 255)
            )
            help_btn = self.font_small.render(
                "Нажмите H для вызова справки", True, (255, 255, 255)
            )
            exit_btn = self.font_small.render(
                "Нажмите ESC для выхода", True, (255, 255, 255)
            )

            self.draw_text_centered(title, 150)
            self.draw_text_centered(start_btn, 300)
            self.draw_text_centered(records_btn, 350)
            self.draw_text_centered(help_btn, 400)
            self.draw_text_centered(exit_btn, 450)

        elif self.state == "records":
            if self.backgrounds.get("records"):
                self.screen.blit(self.backgrounds["records"], (0, 0))

            title = self.font_large.render("ТАБЛИЦА РЕКОРДОВ", True, (255, 215, 0))
            self.screen.blit(title, (50, 50))

            for i, record in enumerate(self.records_manager.records):
                text = f"{i + 1}. {record['name']} - {record['score']}"
                rec_surface = self.font_small.render(text, True, (255, 255, 255))
                self.screen.blit(rec_surface, (50, 150 + i * 40))

        elif self.state == "name_input":
            if self.backgrounds.get("name_input"):
                self.screen.blit(self.backgrounds["name_input"], (0, 0))

            msg = self.font_large.render("НОВЫЙ РЕКОРД!", True, (0, 255, 0))
            prompt = self.font_small.render(
                "Введите ваше имя и нажмите ENTER:", True, (255, 255, 255)
            )
            name_surface = self.font_large.render(
                self.player_name_input, True, (0, 255, 255)
            )

            self.screen.blit(msg, (50, 150))
            self.screen.blit(prompt, (50, 250))
            self.screen.blit(name_surface, (50, 320))

        elif self.state == "help":
            if self.backgrounds.get("help"):
                self.screen.blit(self.backgrounds["help"], (0, 0))

            title = self.font_large.render("ПРАВИЛА ИГРЫ", True, (255, 215, 0))
            rules1 = self.font_small.render(
                "Стрелки влево/вправо - движение", True, (255, 255, 255)
            )
            rules2 = self.font_small.render(
                "Стрелка вверх или ПРОБЕЛ - прыжок", True, (255, 255, 255)
            )
            rules3 = self.font_small.render(
                "Собирайте монеты и грибы, побеждайте врагов!", True, (255, 255, 255)
            )
            rules4 = self.font_small.render(
                "F11 - полноэкранный режим", True, (255, 255, 255)
            )
            back_btn = self.font_small.render(
                "Нажмите ESC для возврата в меню", True, (255, 255, 255)
            )
            self.screen.blit(title, (50, 50))
            self.screen.blit(rules1, (50, 150))
            self.screen.blit(rules2, (50, 190))
            self.screen.blit(rules3, (50, 230))
            self.screen.blit(rules4, (50, 270))
            self.screen.blit(back_btn, (50, 350))

        elif self.state == "level_completed":
            if self.backgrounds.get("level_completed"):
                self.screen.blit(self.backgrounds["level_completed"], (0, 0))

            msg = self.font_large.render("УРОВЕНЬ ПРОЙДЕН!", True, (0, 255, 0))
            score_msg = self.font_small.render(
                f"Итоговый счет: {self.final_score}", True, (255, 0, 255)
            )
            prompt = self.font_small.render(
                "Нажмите ENTER для продолжения", True, (255, 255, 255)
            )

            self.draw_text_centered(msg, 200)
            self.draw_text_centered(score_msg, 300)
            self.draw_text_centered(prompt, 400)

        elif self.state == "game_over":
            if self.backgrounds.get("game_over"):
                self.screen.blit(self.backgrounds["game_over"], (0, 0))

            msg = self.font_large.render("ИГРА ОКОНЧЕНА", True, (255, 0, 0))
            score_msg = self.font_small.render(
                f"Итоговый счет: {self.final_score}", True, (255, 0, 255)
            )
            prompt = self.font_small.render(
                "Нажмите ENTER для продолжения", True, (255, 255, 255)
            )

            self.draw_text_centered(msg, 200)
            self.draw_text_centered(score_msg, 300)
            self.draw_text_centered(prompt, 400)

        elif self.state == "playing":
            self.level.run()

            player = self.level.player.sprite
            score_text = self.font_small.render(
                f"Очки: {player.score}", True, (255, 0, 255)
            )
            self.screen.blit(score_text, (20, 20))

            time_text = self.font_small.render(
                f"Время: {int(self.level.time_left)}", True, (255, 140, 0)
            )
            x_pos = self.settings["width"] // 2 - time_text.get_width() // 2
            self.screen.blit(time_text, (x_pos, 20))

            if player.is_super:
                time_left = max(
                    0, (player.powerup_timer - pygame.time.get_ticks()) // 1000
                )
                time_text = self.font_small.render(
                    f"Супер-сила: {time_left} сек", True, (255, 215, 0)
                )
                self.screen.blit(
                    time_text, (self.settings["width"] - time_text.get_width() - 20, 20)
                )

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.settings["fps"])


if __name__ == "__main__":
    game = Game()
    game.run()
