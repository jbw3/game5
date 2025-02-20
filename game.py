from enum import Enum, IntEnum, unique
import logging
import pygame
import pygame.locals
import random
import sys

from asteroid import Asteroid
from controller import Controller
from enemy_ship import EnemyShip, EnemyShipConfig
from person import Person
from resource_loader import ResourceLoader
from ship import Ship
from sprite import FlightCollisionSprite, Sprite
from stopwatch import Stopwatch

DEBUG_TEXT_COLOR = (180, 0, 150)

@unique
class GameMode(IntEnum):
    AsteroidField = 0
    Combat = 1

GameModeInts = set(GameMode)

def game_mode_to_str(game_mode: GameMode) -> str:
    match game_mode:
        case GameMode.AsteroidField:
            return 'Asteroid Field'
        case GameMode.Combat:
            return 'Combat'
        case _:
            assert False, f'Unknown game mode: {game_mode}'

class OptionsMenu:
    def __init__(self, options: list[str], font: pygame.font.Font, color: pygame.color.Color, x: int, top: int):
        self._options_text = options[:]
        self._font = font
        self._color = color

        self._option_index = 0
        self._options_sprites: list[Sprite] = []
        self._axis_was_centered = False
        self._controller: Controller|None = None

        for text in self._options_text:
            sprite = Sprite(self._font.render(text, True, self._color))
            sprite.rect.centerx = x
            sprite.rect.top = top
            self._options_sprites.append(sprite)
            top = sprite.rect.bottom

    @property
    def option_index(self) -> int:
        return self._option_index

    @property
    def controller(self) -> Controller|None:
        return self._controller

    @controller.setter
    def controller(self, new_controller: Controller|None) -> None:
        self._controller = new_controller

    def _update_options(self) -> None:
        for i, sprite in enumerate(self._options_sprites):
            old_center = sprite.rect.center
            text = self._options_text[i]
            if self._option_index == i:
                text = f'< {text} >'
            sprite.image = self._font.render(text, True, self._color)
            sprite.rect.center = old_center

    def set_option_text(self, index: int, text: str) -> None:
        self._options_text[index] = text
        self._update_options()

    def show(self, game: 'Game') -> None:
        self._axis_was_centered = False
        self._option_index = 0

        for sprite in self._options_sprites:
            game.menu_sprites.add(sprite)

        self._update_options()

    def hide(self, game: 'Game') -> None:
        for sprite in self._options_sprites:
            game.menu_sprites.remove(sprite)

    def update(self, game: 'Game') -> None:
        if self._controller is not None:
            # check if selected option is changing
            axis = self._controller.get_move_y_axis()
            if abs(axis) < 0.001:
                self._axis_was_centered = True
            elif self._axis_was_centered:
                self._axis_was_centered = False
                if axis < 0.0 and self._option_index > 0:
                    self._option_index -= 1
                elif axis > 0.0 and self._option_index < len(self._options_sprites) - 1:
                    self._option_index += 1
                self._update_options()

class SetupMenu:
    TextColor = pygame.color.Color(240, 11, 32)

    @unique
    class State(Enum):
        Start = 0
        Setup = 1

    def __init__(self, game: 'Game'):
        self._font = pygame.font.SysFont('Courier', 60)
        self._num_players = 1
        self._game_mode = GameMode.AsteroidField
        self._axis_was_centered = False
        self._button_was_released = False

        window_width, window_height = pygame.display.get_window_size()
        start_options = [
            'Start',
            'Quit',
        ]
        self._start_options = OptionsMenu(start_options, self._font, SetupMenu.TextColor, window_width//2, window_height//2 - 50)

        setup_options = [
            f'Players: {self._num_players}',
        ]
        if game.debug:
            setup_options.append(f'Mode: {game_mode_to_str(game.mode)}')
        self._setup_options = OptionsMenu(setup_options, self._font, SetupMenu.TextColor, window_width//2, window_height//2 - 50)

        self._state = SetupMenu.State.Start

    def start(self, game: 'Game') -> None:
        self._button_was_released = False

        match self._state:
            case SetupMenu.State.Start:
                if len(game.controllers) == 0:
                    self._start_options.controller = None
                else:
                    self._start_options.controller = game.controllers[0]
                self._start_options.show(game)
            case SetupMenu.State.Setup:
                self._num_players = min(self._num_players, len(game.controllers))
                self._game_mode = game.mode
                self._axis_was_centered = False
                self._setup_options.show(game)
            case _:
                assert False, f'Unknown state {self._state}'

    def _update_start(self, game: 'Game') -> None:
        if self._start_options.controller is not None and len(game.controllers) == 0:
            self._start_options.controller = None
        elif self._start_options.controller is None and len(game.controllers) > 0:
            self._start_options.controller = game.controllers[0]

        self._start_options.update(game)

        if len(game.controllers) > 0:
            if self._button_was_released and game.controllers[0].get_activate_button():
                match self._start_options.option_index:
                    case 0:
                        self._start_options.hide(game)
                        self._setup_options.show(game)
                        self._state = SetupMenu.State.Setup
                    case 1:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _update_setup(self, game: 'Game') -> None:
        old_num_players = self._num_players
        old_game_mode = self._game_mode

        num_controllers = len(game.controllers)
        self._num_players = min(self._num_players, num_controllers)

        if num_controllers > 0:
            controller = game.controllers[0]
            self._setup_options.controller = controller
            self._setup_options.update(game)

            if self._num_players == 0:
                self._num_players = 1

            axis = controller.get_move_x_axis()
            if abs(axis) < 0.001:
                self._axis_was_centered = True
            elif self._axis_was_centered:
                self._axis_was_centered = False
                if axis < 0.0:
                    self._setup_option_decrement(game)
                elif axis > 0.0:
                    self._setup_option_increment(game)

            if self._button_was_released:
                if controller.get_activate_button():
                    game.menu_sprites.empty()
                    game.start_mission(self._num_players, self._game_mode)
                elif controller.get_deactivate_button():
                    self._setup_options.hide(game)
                    self._start_options.show(game)
                    self._state = SetupMenu.State.Start

        else: # num_controllers == 0
            self._setup_options.controller = None

        if self._num_players != old_num_players:
            self._setup_options.set_option_text(0, f'Players: {self._num_players}')

        if self._game_mode != old_game_mode:
            self._setup_options.set_option_text(1, f'Mode: {game_mode_to_str(self._game_mode)}')

    def _setup_option_increment(self, game: 'Game') -> None:
        match self._setup_options.option_index:
            case 0:
                num_controllers = len(game.controllers)
                if self._num_players < num_controllers:
                    self._num_players += 1
            case 1:
                if self._game_mode + 1 in GameModeInts:
                    self._game_mode = GameMode(self._game_mode + 1)
            case _:
                assert False, f'Unknown option index: {self._setup_options.option_index}'

    def _setup_option_decrement(self, game: 'Game') -> None:
        match self._setup_options.option_index:
            case 0:
                if self._num_players > 1:
                    self._num_players -= 1
            case 1:
                if self._game_mode - 1 in GameModeInts:
                    self._game_mode = GameMode(self._game_mode - 1)
            case _:
                assert False, f'Unknown option index: {self._setup_options.option_index}'

    def update(self, game: 'Game') -> None:
        match self._state:
            case SetupMenu.State.Start:
                self._update_start(game)
            case SetupMenu.State.Setup:
                self._update_setup(game)
            case _:
                assert False, f'Unknown state {self._state}'

        if len(game.controllers) > 0:
            activate_button = game.controllers[0].get_activate_button()
            if activate_button:
                self._button_was_released = False
            else:
                self._button_was_released = True

class PauseMenu:
    TextColor = pygame.color.Color(240, 11, 32)

    @unique
    class State(Enum):
        PausePress = 0
        PauseRelease = 1
        UnpausePress = 2

    def __init__(self):
        window_width, window_height = pygame.display.get_window_size()
        self._paused_font = pygame.font.SysFont('Courier', 90)
        self._paused_sprite = Sprite(self._paused_font.render('Paused', True, PauseMenu.TextColor))
        self._paused_sprite.rect.center = (window_width // 2, window_height // 2 - 100)

        option_font = pygame.font.SysFont('Courier', 60)
        options = [
            'Resume',
            'Quit',
        ]
        self._options_menu = OptionsMenu(options, option_font, PauseMenu.TextColor, window_width // 2, self._paused_sprite.rect.bottom + 30)

        self._controller: Controller|None = None
        self._state = PauseMenu.State.PausePress
        self._axis_was_centered = False

    def enable(self, game: 'Game', controller: Controller) -> None:
        self._controller = controller
        self._state = PauseMenu.State.PausePress

        game.menu_sprites.add(self._paused_sprite)
        self._options_menu.controller = controller
        self._options_menu.show(game)

    def update(self, game: 'Game') -> None:
        self._options_menu.update(game)

        if self._controller is not None:
            # check pause button
            pressed = self._controller.get_pause_button()
            match self._state:
                case PauseMenu.State.PausePress:
                    if not pressed:
                        self._state = PauseMenu.State.PauseRelease
                case PauseMenu.State.PauseRelease:
                    if pressed:
                        self._state = PauseMenu.State.UnpausePress
                case PauseMenu.State.UnpausePress:
                    if not pressed:
                        game.unpause()

            # check if an option is being accepted
            if self._controller.get_activate_button():
                match self._options_menu.option_index:
                    case 0:
                        game.unpause()
                    case 1:
                        game.end_mission(delay=False)

class Game:
    MAX_FPS = 60.0
    MAX_FRAME_TIME_MS = 1000 / MAX_FPS

    RESET_GAME_EVENT = pygame.event.custom_type()
    START_WAVE_EVENT = pygame.event.custom_type()

    @unique
    class State(Enum):
        Setup = 0
        Mission = 1
        PostMission = 2

    def __init__(self, debug: bool=False):
        self._debug = debug
        self._logger = logging.getLogger('Game')

        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        # hide the cursor
        pygame.mouse.set_visible(False)

        self._resource_loader = ResourceLoader()

        self._fps_clock = pygame.time.Clock()
        self._frame_time = 0.0

        self._stopwatch_num_frames = int(Game.MAX_FPS)
        self._work_stopwatch = Stopwatch(self._stopwatch_num_frames)
        self._update_stopwatch = Stopwatch(self._stopwatch_num_frames)
        self._draw_stopwatch = Stopwatch(self._stopwatch_num_frames)
        self._blit_stopwatch = Stopwatch(self._stopwatch_num_frames)
        self._display_update_stopwatch = Stopwatch(self._stopwatch_num_frames)

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        display_width, display_height = self._display_surf.get_size()

        self._logger.info(f'Python version: {sys.version}')
        self._logger.info(f'Pygame version: {pygame.version.ver}')
        self._logger.info(f'Display size: {display_width}, {display_height}')

        self._mode = GameMode.AsteroidField

        self._setup_menu = SetupMenu(self)
        self._pause_menu = PauseMenu()

        self._interior_view_surface = self._display_surf.subsurface((0, 0), (display_width//2, display_height))
        self._flight_view_surface = self._display_surf.subsurface((display_width//2, 0), (display_width//2, display_height))

        self._setup_background = self._create_star_background((display_width, display_height))

        space_background = self._create_star_background((display_width // 2, display_height))
        self._mission_background = pygame.surface.Surface(pygame.display.get_window_size())
        self._mission_background.blit(space_background, (0, 0))
        self._mission_background.blit(space_background, (display_width//2, 0))

        self._background = self._mission_background.copy()
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
        self._paused = False

        self._timing_debug = False
        self._joystick_debug = False
        self._debug_font = pygame.font.SysFont('Courier', 20)
        self._debug_rect = pygame.rect.Rect(0, 0, 0, 0)

        self._menu_sprites = pygame.sprite.RenderUpdates()
        self._interior_view_sprites = pygame.sprite.LayeredDirty()
        self._flight_view_sprites = pygame.sprite.RenderUpdates()
        self._interior_solid_sprites = pygame.sprite.Group()
        self._flight_collision_sprites = pygame.sprite.Group()
        self._info_overlay_sprites = pygame.sprite.LayeredDirty()
        self._people_sprites = pygame.sprite.Group()

        self._joysticks: list[pygame.joystick.JoystickType] = []
        self._controllers: list[Controller] = []

        self._state: Game.State = Game.State.Setup
        self._ship: Ship|None = None
        self._num_players = 0
        self._wave = 1
        self._asteroid_count = 0
        self._enemy_count = 0

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def mode(self) -> GameMode:
        return self._mode

    @property
    def resource_loader(self) -> ResourceLoader:
        return self._resource_loader

    @property
    def frame_time(self) -> float:
        return self._frame_time

    @property
    def menu_sprites(self) -> 'pygame.sprite.RenderUpdates[Sprite]':
        return self._menu_sprites

    @property
    def interior_view_sprites(self) -> 'pygame.sprite.LayeredDirty[Sprite]':
        return self._interior_view_sprites

    @property
    def flight_view_sprites(self) -> 'pygame.sprite.RenderUpdates[Sprite]':
        return self._flight_view_sprites

    @property
    def interior_solid_sprites(self) -> 'pygame.sprite.Group[Sprite]':
        return self._interior_solid_sprites

    @property
    def flight_collision_sprites(self) -> 'pygame.sprite.Group[FlightCollisionSprite]':
        return self._flight_collision_sprites

    @property
    def info_overlay_sprites(self) -> 'pygame.sprite.LayeredDirty[Sprite]':
        return self._info_overlay_sprites

    @property
    def people_sprites(self) -> 'pygame.sprite.Group[Sprite]':
        return self._people_sprites

    @property
    def controllers(self) -> list[Controller]:
        return self._controllers

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

    def pause(self, controller: Controller) -> None:
        self._paused = True
        self._pause_menu.enable(self, controller)

    def unpause(self) -> None:
        self._paused = False
        self._menu_sprites.empty()

    def update_asteroid_count(self, change: int) -> None:
        self._asteroid_count += change

        if self._asteroid_count == 0:
            self._end_wave()

    def update_enemy_count(self, change: int) -> None:
        self._enemy_count += change

        if self._enemy_count == 0:
            self._end_wave()

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
            text_strings.append(f'Frame times for past {self._stopwatch_num_frames} frames:')
            text_strings.append(self._build_timing_string('Total', 1, self._work_stopwatch.times))
            text_strings.append(self._build_timing_string('Update', 2, self._update_stopwatch.times))
            text_strings.append(self._build_timing_string('Draw', 2, self._draw_stopwatch.times))
            text_strings.append(self._build_timing_string('Blit', 3, self._blit_stopwatch.times))
            text_strings.append(self._build_timing_string('Display', 3, self._display_update_stopwatch.times))

        if self._joystick_debug:
            # Joystick info
            joystick_count = pygame.joystick.get_count()
            text_strings.append(f'Joystick info ({joystick_count}):')

            for joystick in self._joysticks:
                i = joystick.get_instance_id()
                name = joystick.get_name()
                guid = joystick.get_guid()
                text_strings.append(f' {i}: {guid}, {name}')

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

        # if the debug text overlaps any sprites, they will need to be redrawn
        for sprite in self._interior_view_sprites:
            if self._debug_rect.colliderect(sprite.rect):
                sprite.dirty = 1

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
            self.resource_loader.load_image(f'galaxy{i+1}.png')
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
            self.resource_loader.load_image(f'nebula_part{i+1}.png')
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
        self._menu_sprites.empty()
        self._interior_view_sprites.empty()
        self._flight_view_sprites.empty()
        self._interior_solid_sprites.empty()
        self._flight_collision_sprites.empty()
        self._info_overlay_sprites.empty()

        self._paused = False
        self._ship = None

        self.start_setup()

    def _new_asteroid_wave(self) -> None:
        flight_view_size = self._flight_view_surface.get_size()
        flight_view_width, flight_view_height = flight_view_size

        self._asteroid_count = self._wave * self._num_players
        for _ in range(self._asteroid_count):
            x = random.randint(0, flight_view_width - 1)
            y = random.randint(0, flight_view_height // 10)
            Asteroid(self, Asteroid.Size.Big, (x, y))

    def _new_enemy_ship_wave(self) -> None:
        flight_view_size = self._flight_view_surface.get_size()
        flight_view_width, _ = flight_view_size

        wave_mod = (self._wave - 1) % 5

        hold_position_delay = 5.0 - wave_mod

        if self._wave == 1:
            initial_fire_delay = 6.0
        else:
            initial_fire_delay = 3.0

        laser_delay = 3.0 - wave_mod * 0.5

        if wave_mod == 0:
            max_aiming_iterations = 0
        elif wave_mod <= 2:
            max_aiming_iterations = 1
        else:
            max_aiming_iterations = 5

        config = EnemyShipConfig(
            hold_position_delay=hold_position_delay,
            initial_fire_delay=initial_fire_delay,
            laser_delay=laser_delay,
            max_aiming_iterations=max_aiming_iterations,
        )

        self._enemy_count = (self._wave - 1) // 5 + 1

        x = flight_view_width//2 - self._enemy_count//2 * 40
        y = 30
        for i in range(self._enemy_count):
            EnemyShip(self, x, y, config)
            x += 40
            y = 30 + 40 * (i // 10)

    def start_setup(self) -> None:
        self._state = Game.State.Setup

        self._setup_menu.start(self)

        # reset background
        self._background.blit(self._setup_background, (0, 0))
        self._display_surf.blit(self._background, (0, 0))
        self._update_rects.append(self._display_surf.get_rect())

    def start_mission(self, num_players: int, game_mode: GameMode) -> None:
        interior_view_width, interior_view_height = self._interior_view_surface.get_size()
        interior_view_center = (interior_view_width // 2, interior_view_height // 2)

        self._state = Game.State.Mission
        self._mode = game_mode

        # reset background
        self._background.blit(self._mission_background, (0, 0))
        self._display_surf.blit(self._background, (0, 0))
        self._update_rects.append(self._display_surf.get_rect())

        # create ship
        self._ship = Ship(self, interior_view_center)

        self._ship.blit_interior_view(self._interior_view_background)
        self._display_surf.blit(self._interior_view_background, (0, 0))
        self._update_rects.append(self._interior_view_surface.get_rect())

        self._num_players = num_players
        self._wave = 1

        # create people
        for i in range(num_players):
            if i % 2 == 0:
                x = interior_view_center[0] - 20
            else:
                x = interior_view_center[0] + 20
            y = interior_view_center[1] - 130 + (i // 2 * 15)

            controller = self._controllers[i]
            person = Person(self, (x, y), controller)
            self._people_sprites.add(person)

        self._start_wave()

    def end_mission(self, delay: bool) -> None:
        self._state = Game.State.PostMission
        if delay:
            pygame.time.set_timer(Game.RESET_GAME_EVENT, 3_000, 1)
        else:
            self._reset_game()

    def _start_wave(self) -> None:
        match self._mode:
            case GameMode.AsteroidField:
                self._new_asteroid_wave()
            case GameMode.Combat:
                self._new_enemy_ship_wave()
            case _:
                assert False, f'Unknown game mode: {self._mode}'

    def _end_wave(self) -> None:
        self._wave += 1

        pygame.time.set_timer(Game.START_WAVE_EVENT, 3_000, 1)

    def _process_events(self) -> bool:
        quit_game = False
        for event in pygame.event.get():
            match event.type:
                case pygame.locals.QUIT:
                    quit_game = True

                case pygame.locals.KEYDOWN:
                    if event.key == pygame.K_F1 and pygame.K_F1 not in self._pressed_keys:
                        self._timing_debug = not self._timing_debug
                    elif event.key == pygame.K_F2 and pygame.K_F2 not in self._pressed_keys:
                        self._joystick_debug = not self._joystick_debug
                    self._pressed_keys.add(event.key)

                case pygame.locals.KEYUP:
                    self._pressed_keys.remove(event.key)

                case pygame.locals.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    self._joysticks.append(joystick)
                    self._controllers.append(Controller(joystick))
                    joystick_id = joystick.get_instance_id()
                    guid = joystick.get_guid()
                    name = joystick.get_name()
                    self._logger.info(f'Joystick added: {joystick_id}, {guid}, {name}')

                case pygame.locals.JOYDEVICEREMOVED:
                    idx = event.instance_id
                    for joystick in self._joysticks:
                        if joystick.get_id() == idx:
                            self._joysticks.pop(idx)
                            self._controllers.pop(idx)
                            joystick_id = joystick.get_instance_id()
                            guid = joystick.get_guid()
                            name = joystick.get_name()
                            self._logger.info(f'Joystick removed: {joystick_id}, {guid}, {name}')
                            break

                case Game.RESET_GAME_EVENT:
                    self._reset_game()

                case Game.START_WAVE_EVENT:
                    if self._state == Game.State.Mission:
                        self._start_wave()

        return quit_game

    def _update_sprites(self) -> None:
        self._update_stopwatch.start()

        match self._state:
            case Game.State.Setup:
                self._setup_menu.update(self)
            case Game.State.Mission:
                if self._paused:
                    self._pause_menu.update(self)
                else:
                    for sprite in self.interior_view_sprites:
                        sprite.update(self)
                    for sprite in self.flight_view_sprites:
                        sprite.update(self)

                    for controller in self.controllers:
                        if controller.get_pause_button():
                            self.pause(controller)
                            break
            case Game.State.PostMission:
                for sprite in self.flight_view_sprites:
                    sprite.update(self)

        self._update_stopwatch.stop()

    def _draw_sprites(self) -> None:
        self._draw_stopwatch.start()
        self._blit_stopwatch.start()

        if self._debug_rect.width > 0 and self._debug_rect.height > 0:
            rect = self._display_surf.blit(self._background, (0, 0), self._debug_rect)
            self._update_rects.append(rect)

        self._interior_view_sprites.clear(self._interior_view_surface, self._interior_view_background)
        self._flight_view_sprites.clear(self._flight_view_surface, self._flight_view_background)
        self._info_overlay_sprites.clear(self._display_surf, self._background)
        self._menu_sprites.clear(self._display_surf, self._background)

        rects = self._interior_view_sprites.draw(self._interior_view_surface)
        self._update_rects += rects

        rects = self._flight_view_sprites.draw(self._flight_view_surface)
        offset = self._display_surf.get_rect().width // 2
        for rect in rects:
            adjusted_rect = rect.copy()
            adjusted_rect.x += offset
            self._update_rects.append(adjusted_rect)

        if self._state != Game.State.Setup:
            self._display_surf.blit(self._divider.image, self._divider.rect)
            self._update_rects.append(self._divider.rect)

        rects = self._info_overlay_sprites.draw(self._display_surf)
        self._update_rects += rects

        rects = self._menu_sprites.draw(self._display_surf)
        self._update_rects += rects

        if self._timing_debug or self._joystick_debug:
            self._display_debug()
        else:
            self._debug_rect.size = (0, 0)

        self._blit_stopwatch.stop()

        update_rects_str = ', '.join(f'({r.x}, {r.y})' for r in self._update_rects)
        self._logger.debug(f'Update rects: {update_rects_str}')

        self._display_update_stopwatch.start()

        pygame.display.update(self._update_rects)
        self._update_rects.clear()

        self._display_update_stopwatch.stop()
        self._draw_stopwatch.stop()

    def mainloop(self) -> None:
        self.start_setup()

        self._work_stopwatch.start()
        while True:
            self._logger.debug(f'Ticks: {pygame.time.get_ticks()}')

            quit_game = self._process_events()
            if quit_game:
                break

            self._update_sprites()
            self._draw_sprites()

            self._work_stopwatch.stop()

            frame_time_ms = self._fps_clock.tick(Game.MAX_FPS)
            self._frame_time = frame_time_ms / 1000

            self._work_stopwatch.start()

        pygame.quit()
