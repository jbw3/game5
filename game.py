import pygame
from pygame.locals import JOYDEVICEADDED, JOYDEVICEREMOVED, KEYDOWN, KEYUP, QUIT
import random
from ship import Ship

DEBUG_TEXT_COLOR = (180, 0, 150)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        self._fps_clock = pygame.time.Clock()
        self._tick_delta = 0.0

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self._display_surf.fill((0, 0, 0))

        self._background_surf = self._create_star_background()

        self._debug = False
        self._can_change_debug = True
        self._debug_font = pygame.font.SysFont('Courier', 20)

        self._sprites = pygame.sprite.Group()
        self._joysticks: list[pygame.joystick.JoystickType] = []

        self.ship: Ship|None = None

    @property
    def sprites(self) -> pygame.sprite.Group:
        return self._sprites

    def _display_debug(self) -> None:
        y = 0

        fps = self._fps_clock.get_fps()
        text_surface = self._debug_font.render(f'FPS: {fps:.1f}', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        tick_delta_ms = self._tick_delta * 1000
        text_surface = self._debug_font.render(f'Tick delta: {tick_delta_ms:.1f} ms', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        joystick_count = pygame.joystick.get_count()
        text_surface = self._debug_font.render(f'Joystick info ({joystick_count}):', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        for joystick in self._joysticks:
            i = joystick.get_instance_id()
            name = joystick.get_name()
            text_surface = self._debug_font.render(f' {i}: {name}', False, DEBUG_TEXT_COLOR)
            self._display_surf.blit(text_surface, (0, y))
            y += text_surface.get_rect().bottom

    def _create_star_background(self) -> pygame.surface.Surface:
        surface = pygame.surface.Surface(self._display_surf.get_size())
        surface.fill((0, 0, 0))
        width = surface.get_width()
        height = surface.get_height()
        num_stars = width * height // 5000
        num_white_stars = random.randint(num_stars * 3 // 8, num_stars * 5 // 8)
        num_remaining = num_stars - num_white_stars
        num_yellow_stars = random.randint(num_remaining * 1 // 2, num_remaining * 5 // 8)
        num_red_stars = max(0, num_stars - num_white_stars - num_yellow_stars)

        print(num_white_stars, num_yellow_stars, num_red_stars)

        star_info = [
            # white
            (num_white_stars, (250, 250, 250)),
            # yellow
            (num_yellow_stars, (255, 255, 180)),
            # red
            (num_red_stars, (255, 160, 180)),
        ]

        for num, color in star_info:
            for _ in range(num):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                surface.set_at((x, y), color)

        return surface

    def start_mission(self) -> None:
        self.ship = Ship(self)

    def mainloop(self) -> None:
        self.start_mission()
        assert self.ship is not None

        quit_game = False
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
                elif event.type == KEYDOWN:
                    if event.key == pygame.K_F1 and self._can_change_debug:
                        self._debug = not self._debug
                        self._can_change_debug = False
                elif event.type == KEYUP:
                    if event.key == pygame.K_F1:
                        self._can_change_debug = True
                elif event.type == JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    self._joysticks.append(joystick)
                elif event.type == JOYDEVICEREMOVED:
                    idx = event.instance_id
                    for joystick in self._joysticks:
                        if joystick.get_id() == idx:
                            self._joysticks.pop(idx)
                            break

            if quit_game:
                break

            self.ship.update(self)

            self._display_surf.blit(self._background_surf, (0, 0))
            self._sprites.draw(self._display_surf)

            if self._debug:
                self._display_debug()

            pygame.display.update()
            tick_delta_ms = self._fps_clock.tick(60.0)
            self._tick_delta = tick_delta_ms / 1000
