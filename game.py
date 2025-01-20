import os
import pygame
from pygame.locals import JOYDEVICEADDED, JOYDEVICEREMOVED, KEYDOWN, KEYUP, QUIT
import random

from asteroid import Asteroid
from person import Person
from ship import Ship

DEBUG_TEXT_COLOR = (180, 0, 150)

class Game:
    MAX_FPS = 60.0
    MAX_FRAME_TIME_MS = 1000 / MAX_FPS

    RESET_GAME_EVENT = pygame.event.custom_type()

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        self._fps_clock = pygame.time.Clock()
        self._frame_time = 0.0
        self._work_time_ms = 0

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self._display_surf.fill((0, 0, 0))

        display_width, display_height = self._display_surf.get_size()
        self._space_background = self._create_star_background((display_width // 2, display_height))
        self._interior_view_surface = self._space_background.copy()
        self._flight_view_surface = self._space_background.copy()

        self._divider = pygame.surface.Surface((8, display_height))
        self._divider.fill((130, 130, 130))

        self._debug = False
        self._can_change_debug = True
        self._debug_font = pygame.font.SysFont('Courier', 20)

        self._interior_view_sprites = pygame.sprite.Group()
        self._flight_view_sprites = pygame.sprite.Group()
        self._interior_solid_sprites = pygame.sprite.Group()
        self._flight_collision_sprites = pygame.sprite.Group()

        self._joysticks: list[pygame.joystick.JoystickType] = []

        self._playing_mission = False
        self._ship: Ship|None = None
        self._asteroid_count = 0
        self._asteroid_create_count = 0

    @property
    def frame_time(self) -> float:
        return self._frame_time

    @property
    def interior_view_sprites(self) -> pygame.sprite.Group:
        return self._interior_view_sprites

    @property
    def flight_view_sprites(self) -> pygame.sprite.Group:
        return self._flight_view_sprites

    @property
    def interior_solid_sprites(self) -> pygame.sprite.Group:
        return self._interior_solid_sprites

    @property
    def flight_collision_sprites(self) -> pygame.sprite.Group:
        return self._flight_collision_sprites

    @property
    def interior_view_size(self) -> tuple[int, int]:
        return self._interior_view_surface.get_size()

    @property
    def flight_view_size(self) -> tuple[int, int]:
        return self._flight_view_surface.get_size()

    @property
    def ship(self) -> Ship:
        assert self._ship is not None, 'ship is None'
        return self._ship

    def update_asteroid_count(self, change: int) -> None:
        self._asteroid_count += change

        if self._asteroid_count == 0:
            self._create_asteroids()

    def _display_debug(self) -> None:
        y = 0

        fps = self._fps_clock.get_fps()
        text_surface = self._debug_font.render(f'FPS: {fps:.1f}', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        work_time_percentage = self._work_time_ms / Game.MAX_FRAME_TIME_MS * 100
        text_surface = self._debug_font.render(f'Frame time: {self._work_time_ms}/{Game.MAX_FRAME_TIME_MS:.1f} ms ({work_time_percentage:.0f}%)', False, DEBUG_TEXT_COLOR)
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

            axes_str = ', '.join(f'{i}: {joystick.get_axis(i):.1f}' for i in range(joystick.get_numaxes()))
            text_surface = self._debug_font.render(f'  axes: {axes_str}', False, DEBUG_TEXT_COLOR)
            self._display_surf.blit(text_surface, (0, y))
            y += text_surface.get_rect().bottom

            buttons_str = ', '.join(f'{i}: {joystick.get_button(i)}' for i in range(joystick.get_numbuttons()))
            text_surface = self._debug_font.render(f'  buttons: {buttons_str}', False, DEBUG_TEXT_COLOR)
            self._display_surf.blit(text_surface, (0, y))
            y += text_surface.get_rect().bottom

    def _create_star_background(self, size: tuple[int, int]) -> pygame.surface.Surface:
        surface = pygame.surface.Surface(size)
        surface.fill((0, 0, 0))
        width = surface.get_width()
        height = surface.get_height()
        num_stars = width * height // 5000
        num_white_stars = random.randint(num_stars * 3 // 8, num_stars * 5 // 8)
        num_remaining = num_stars - num_white_stars
        num_yellow_stars = random.randint(num_remaining * 1 // 2, num_remaining * 5 // 8)
        num_red_stars = max(0, num_stars - num_white_stars - num_yellow_stars)

        star_info = [
            # white
            (num_white_stars, (250, 250, 250)),
            # yellow
            (num_yellow_stars, (255, 255, 180)),
            # red
            (num_red_stars, (255, 160, 180)),
        ]

        star_surface = pygame.surface.Surface((1, 1))
        for num, color in star_info:
            for _ in range(num):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                star_surface.set_at((0, 0), color)
                star_surface.set_alpha(random.randint(60, 255))
                surface.blit(star_surface, (x, y))

        galaxy_images = [
            pygame.image.load(os.path.join('images', f'galaxy{i+1}.png'))
            for i in range(2)
        ]
        num_galaxies = random.choice([2, 3])
        for i in range(num_galaxies):
            galaxy_surface = galaxy_images[i % len(galaxy_images)]
            x = (width // num_galaxies * i) + random.randint(0, width // num_galaxies)
            y = random.randint(50, height - 50)
            galaxy_surface.set_alpha(random.randint(100, 200))
            angle = random.random() * 40.0 - 20.0
            galaxy_surface_rotated = pygame.transform.rotate(galaxy_surface, angle)
            surface.blit(galaxy_surface_rotated, (x, y))

        nebula_part_images = [
            pygame.image.load(os.path.join('images', f'nebula_part{i+1}.png'))
            for i in range(5)
        ]
        num_nebulas = 2
        for i in range(num_nebulas):
            nebula_width = 100 + random.randint(-20, 20)
            nebula_heigh = 140 + random.randint(-25, 25)
            nebula_surface = pygame.surface.Surface((nebula_width, nebula_heigh))
            num_parts = (nebula_width * nebula_heigh) // 50 + random.randint(0, 50)
            for _ in range(num_parts):
                part = random.choice(nebula_part_images)
                part.set_alpha(random.randint(10, 30))
                part_width = part.get_rect().width
                part_height = part.get_rect().height
                x = int(random.normalvariate(nebula_width / 2, nebula_width / 6) - part_width / 2)
                y = int(random.normalvariate(nebula_heigh / 2, nebula_heigh / 6) - part_height / 2)
                nebula_surface.blit(part, (x, y))
            x = random.randint(100, width - 100)
            y = (height // num_nebulas * i) + random.randint(100, height // num_nebulas - 100)
            nebula_surface.set_alpha(130)
            surface.blit(nebula_surface, (x, y))

        return surface

    def _reset_game(self) -> None:
        self._interior_view_sprites.empty()
        self._flight_view_sprites.empty()
        self._interior_solid_sprites.empty()
        self._flight_collision_sprites.empty()

        self._ship = None

    def _create_asteroids(self) -> None:
        flight_view_size = self._flight_view_surface.get_size()
        flight_view_width, flight_view_height = flight_view_size

        self._asteroid_create_count += 1
        self._asteroid_count = self._asteroid_create_count
        for _ in range(self._asteroid_count):
            x = random.randint(0, flight_view_width - 1)
            y = random.randint(0, flight_view_height // 10)
            Asteroid(self, Asteroid.Size.Big, (x, y))

    def start_mission(self) -> None:
        interior_view_width, interior_view_height = self._interior_view_surface.get_size()
        interior_view_center = (interior_view_width // 2, interior_view_height // 2)

        self._playing_mission = True

        # create ship
        self._ship = Ship(self, interior_view_center)

        self._asteroid_create_count = 0
        self._create_asteroids()

        # create people
        people: list[Person] = []
        y = interior_view_center[1] - 40
        for joystick in self._joysticks:
            person = Person(self, (interior_view_center[0], y), joystick)
            people.append(person)
            y += 20

    def end_mission(self) -> None:
        self._playing_mission = False
        pygame.time.set_timer(Game.RESET_GAME_EVENT, 3_000, 1)

    def mainloop(self) -> None:
        quit_game = False
        work_loop_start_ms = pygame.time.get_ticks()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
                elif event.type == KEYDOWN:
                    if event.key == pygame.K_F1:
                        if self._can_change_debug:
                            self._debug = not self._debug
                            self._can_change_debug = False
                    elif event.key == pygame.K_SPACE:
                        # this is a bit hacky
                        if self._ship is None:
                            self.start_mission()
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
                elif event.type == Game.RESET_GAME_EVENT:
                    self._reset_game()

            if quit_game:
                break

            if self._playing_mission and self._ship is not None:
                self._ship.update(self)
            for sprite in self.interior_view_sprites:
                sprite.update(self)
            for sprite in self.flight_view_sprites:
                sprite.update(self)

            self._interior_view_surface.blit(self._space_background, (0, 0))
            self._flight_view_surface.blit(self._space_background, (0, 0))

            self._interior_view_sprites.draw(self._interior_view_surface)
            self._flight_view_sprites.draw(self._flight_view_surface)

            window_width, _ = pygame.display.get_window_size()
            self._display_surf.blit(self._interior_view_surface, (0, 0))
            self._display_surf.blit(self._flight_view_surface, (window_width // 2, 0))
            self._display_surf.blit(self._divider, (window_width // 2 - 4, 0))

            if self._debug:
                self._display_debug()

            pygame.display.update()

            self._work_time_ms = pygame.time.get_ticks() - work_loop_start_ms
            frame_time_ms = self._fps_clock.tick(Game.MAX_FPS)
            self._frame_time = frame_time_ms / 1000

            work_loop_start_ms = pygame.time.get_ticks()
