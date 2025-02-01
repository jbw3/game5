import logging
import os
import pygame
from pygame.locals import JOYDEVICEADDED, JOYDEVICEREMOVED, KEYDOWN, KEYUP, QUIT
import random

from asteroid import Asteroid
from image_loader import ImageLoader
from person import Person
from ship import Ship
from sprite import Sprite

DEBUG_TEXT_COLOR = (180, 0, 150)

class Game:
    MAX_FPS = 60.0
    MAX_FRAME_TIME_MS = 1000 / MAX_FPS

    RESET_GAME_EVENT = pygame.event.custom_type()

    def __init__(self):
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(filename=os.path.join(log_dir, 'game.log'), filemode='w', level=logging.INFO)
        self._logger = logging.getLogger('Game')

        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        self._image_loader = ImageLoader()

        self._fps_clock = pygame.time.Clock()
        self._frame_time = 0.0

        self._work_times_ms = [0] * int(Game.MAX_FPS)
        self._update_times_ms = [0] * int(Game.MAX_FPS)
        self._draw_times_ms = [0] * int(Game.MAX_FPS)
        self._blit_times_ms = [0] * int(Game.MAX_FPS)
        self._display_update_times_ms = [0] * int(Game.MAX_FPS)

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)

        display_width, display_height = self._display_surf.get_size()
        self._interior_view_surface = self._display_surf.subsurface((0, 0), (display_width//2, display_height))
        self._flight_view_surface = self._display_surf.subsurface((display_width//2, 0), (display_width//2, display_height))

        self._space_background = self._create_star_background((display_width // 2, display_height))

        self._full_space_background = pygame.surface.Surface(pygame.display.get_window_size())
        self._full_space_background.blit(self._space_background, (0, 0))
        self._full_space_background.blit(self._space_background, (display_width//2, 0))

        self._background = self._full_space_background.copy()
        self._interior_view_background = self._background.subsurface((0, 0), (display_width//2, display_height))
        self._flight_view_background = self._background.subsurface((display_width//2, 0), (display_width//2, display_height))

        self._display_surf.blit(self._background, (0, 0))

        divider_surface = pygame.surface.Surface((8, display_height))
        divider_surface.fill((130, 130, 130))
        self._divider = Sprite(divider_surface)
        self._divider.rect.topleft = (display_width // 2 - 4, 0)

        self._update_rects: list[pygame.rect.Rect] = []

        # need to update the whole screen the first time
        self._update_rects.append(self._display_surf.get_rect())

        self._pressed_keys: set[int] = set()

        self._timing_debug = False
        self._joystick_debug = False
        self._debug_font = pygame.font.SysFont('Courier', 20)
        self._debug_rect = pygame.rect.Rect(0, 0, 0, 0)

        self._interior_view_sprites = pygame.sprite.RenderUpdates()
        self._flight_view_sprites = pygame.sprite.RenderUpdates()
        self._interior_solid_sprites = pygame.sprite.Group()
        self._flight_collision_sprites = pygame.sprite.Group()
        self._info_overlay_sprites = pygame.sprite.RenderUpdates()
        self._people_sprites = pygame.sprite.Group()

        self._joysticks: list[pygame.joystick.JoystickType] = []

        self._playing_mission = False
        self._ship: Ship|None = None
        self._asteroid_count = 0
        self._asteroid_create_count = 0

    @property
    def image_loader(self) -> ImageLoader:
        return self._image_loader

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
    def info_overlay_sprites(self) -> pygame.sprite.Group:
        return self._info_overlay_sprites

    @property
    def people_sprites(self) -> pygame.sprite.Group:
        return self._people_sprites

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

    def _build_timing_string(self, title: str, indent: int, times: list[int]) -> str:
        num_times = len(times)
        times_avg = sum(times) / num_times
        times_max = max(times)
        times_min = min(times)
        times_avg_percentage = times_avg / Game.MAX_FRAME_TIME_MS * 100
        title += ':'
        padded_title = f'{title:<8}'
        indent_str = ' ' * indent
        s = f'{indent_str}{padded_title} avg: {times_avg:4.1f}/{Game.MAX_FRAME_TIME_MS:.1f} ms ({times_avg_percentage:2.0f}%), min: {times_min:2} ms, max: {times_max:2} ms'
        return s

    def _display_debug(self) -> None:
        text_strings: list[str] = []

        if self._timing_debug:
            # FPS
            fps = self._fps_clock.get_fps()
            text_strings.append(f'FPS: {fps:.1f}')

            # Frame times
            num_frames = len(self._work_times_ms)
            text_strings.append(f'Frame times for past {num_frames} frames:')
            text_strings.append(self._build_timing_string('Total', 1, self._work_times_ms))
            text_strings.append(self._build_timing_string('Update', 1, self._update_times_ms))
            text_strings.append(self._build_timing_string('Draw', 1, self._draw_times_ms))
            text_strings.append(self._build_timing_string('Blit', 2, self._blit_times_ms))
            text_strings.append(self._build_timing_string('Display', 2, self._display_update_times_ms))

        if self._joystick_debug:
            # Joystick info
            joystick_count = pygame.joystick.get_count()
            text_strings.append(f'Joystick info ({joystick_count}):')

            for joystick in self._joysticks:
                i = joystick.get_instance_id()
                name = joystick.get_name()
                text_strings.append(f' {i}: {name}')

                axes_str = ', '.join(f'{j}: {joystick.get_axis(j):.1f}' for j in range(joystick.get_numaxes()))
                text_strings.append(f'  axes: {axes_str}')

                buttons_str = ', '.join(f'{j}: {joystick.get_button(j)}' for j in range(joystick.get_numbuttons()))
                text_strings.append(f'  buttons: {buttons_str}')

                hats_str = ', '.join(f'{j}: {joystick.get_hat(j)}' for j in range(joystick.get_numhats()))
                text_strings.append(f'  hats: {hats_str}')

        y = 0
        for s in text_strings:
            text_surface = self._debug_font.render(s, False, DEBUG_TEXT_COLOR)
            self._display_surf.blit(text_surface, (0, y))
            rect = text_surface.get_rect()
            y += rect.bottom
            self._debug_rect.width = max(self._debug_rect.width, rect.width)
            self._debug_rect.height = y

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
            self.image_loader.load(f'galaxy{i+1}.png')
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
            self.image_loader.load(f'nebula_part{i+1}.png')
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
        self._info_overlay_sprites.empty()

        self._ship = None

        # reset background
        self._background.blit(self._full_space_background, (0, 0))
        self._display_surf.blit(self._background, (0, 0))
        self._update_rects.append(self._display_surf.get_rect())

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

        self._ship.blit_interior_view(self._interior_view_background)
        self._display_surf.blit(self._interior_view_background, (0, 0))
        self._update_rects.append(self._interior_view_surface.get_rect())

        self._asteroid_create_count = 0
        self._create_asteroids()

        # create people
        for i, joystick in enumerate(self._joysticks):
            if i % 2 == 0:
                x = interior_view_center[0] - 20
            else:
                x = interior_view_center[0] + 20
            y = interior_view_center[1] - 130 + (i // 2 * 15)

            person = Person(self, (x, y), joystick)
            self._people_sprites.add(person)

    def end_mission(self) -> None:
        self._playing_mission = False
        pygame.time.set_timer(Game.RESET_GAME_EVENT, 3_000, 1)

    def mainloop(self) -> None:
        quit_game = False
        work_loop_start_ms = pygame.time.get_ticks()
        while True:
            self._logger.debug(f'Ticks: {pygame.time.get_ticks()}')

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
                elif event.type == KEYDOWN:
                    if event.key == pygame.K_F1 and pygame.K_F1 not in self._pressed_keys:
                        self._timing_debug = not self._timing_debug
                    elif event.key == pygame.K_F2 and pygame.K_F2 not in self._pressed_keys:
                        self._joystick_debug = not self._joystick_debug
                    elif event.key == pygame.K_SPACE:
                        # this is a bit hacky
                        if self._ship is None:
                            self.start_mission()
                    self._pressed_keys.add(event.key)
                elif event.type == KEYUP:
                    self._pressed_keys.remove(event.key)
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

            # Update sprites

            update_time_start_ms = pygame.time.get_ticks()

            if self._playing_mission and self._ship is not None:
                self._ship.update(self)
            for sprite in self.interior_view_sprites:
                sprite.update(self)
            for sprite in self.flight_view_sprites:
                sprite.update(self)

            update_time_ms = pygame.time.get_ticks() - update_time_start_ms

            # Draw sprites

            draw_time_start_ms = pygame.time.get_ticks()
            blit_time_start_ms = draw_time_start_ms

            rect = self._display_surf.blit(self._background, (0, 0), self._debug_rect)
            self._update_rects.append(rect)

            self._interior_view_sprites.clear(self._interior_view_surface, self._interior_view_background)
            self._flight_view_sprites.clear(self._flight_view_surface, self._flight_view_background)
            self._info_overlay_sprites.clear(self._display_surf, self._background)

            rects = self._interior_view_sprites.draw(self._interior_view_surface)
            self._update_rects += rects

            rects = self._flight_view_sprites.draw(self._flight_view_surface)
            offset = self._display_surf.get_rect().width // 2
            for rect in rects:
                adjusted_rect = rect.copy()
                adjusted_rect.x += offset
                self._update_rects.append(adjusted_rect)

            self._display_surf.blit(self._divider.image, self._divider.rect)
            self._update_rects.append(self._divider.rect)

            rects = self._info_overlay_sprites.draw(self._display_surf)
            self._update_rects += rects

            if self._timing_debug or self._joystick_debug:
                self._display_debug()
            else:
                self._debug_rect.size = (0, 0)

            blit_time_ms = pygame.time.get_ticks() - blit_time_start_ms

            update_rects_str = ', '.join(f'({r.x}, {r.y})' for r in self._update_rects)
            self._logger.debug(f'Update rects: {update_rects_str}')

            display_update_start_ms = pygame.time.get_ticks()
            pygame.display.update(self._update_rects)
            self._update_rects.clear()

            now = pygame.time.get_ticks()
            display_update_time_ms = now - display_update_start_ms
            draw_time_ms = now - draw_time_start_ms

            self._update_times_ms.append(update_time_ms)
            self._update_times_ms.pop(0)

            self._draw_times_ms.append(draw_time_ms)
            self._draw_times_ms.pop(0)

            self._blit_times_ms.append(blit_time_ms)
            self._blit_times_ms.pop(0)

            self._display_update_times_ms.append(display_update_time_ms)
            self._display_update_times_ms.pop(0)

            work_time_ms = pygame.time.get_ticks() - work_loop_start_ms
            self._work_times_ms.append(work_time_ms)
            self._work_times_ms.pop(0)

            frame_time_ms = self._fps_clock.tick(Game.MAX_FPS)
            self._frame_time = frame_time_ms / 1000

            work_loop_start_ms = pygame.time.get_ticks()
