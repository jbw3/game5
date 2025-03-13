import math
import logging
import pygame
import random
from typing import TYPE_CHECKING, override

from aim_sprite import AimSprite
from animation import ShipExplosionAnimation
from door import Door
from laser import Laser
from person import Person
from sprite import FlightCollisionSprite, Sprite

if TYPE_CHECKING:
    from game import Game

class Console(Sprite):
    def __init__(self, game: 'Game', image: pygame.surface.Surface):
        super().__init__(image)
        self.dirty = 1
        game.interior_view_sprites.add(self)
        game.interior_solid_sprites.add(self)

        self._person: Person|None = None

    @property
    def person(self) -> Person|None:
        return self._person

    def _move_person(self, person: Person) -> None:
        pass

    def activate(self, ship: 'Ship', person: Person) -> None:
        self._person = person
        self._move_person(self._person)

    def deactivate(self, ship: 'Ship') -> None:
        self._person = None

    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        pass

class PilotConsole(Console):
    IMAGE_NAME = 'pilot_console.png'
    ERROR_IMAGE_NAME = 'pilot_console_error.png'

    def __init__(self, game: 'Game'):
        super().__init__(game, game.resource_loader.load_image(PilotConsole.IMAGE_NAME))

    @override
    def _move_person(self, person: Person) -> None:
        person.rect.centerx = self.rect.centerx
        person.rect.top = self.rect.bottom + 1

    @override
    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        if self._person is not None:
            controller = self._person.controller

            x_accel = controller.get_move_x_axis() * Ship.MAX_ACCELERATION
            y_accel = controller.get_move_y_axis() * Ship.MAX_ACCELERATION

            ship.accelerate(x_accel, y_accel)

    def set_error(self, game: 'Game', is_error: bool) -> None:
        old_rect = self.rect.copy()

        if is_error:
            self.image = game.resource_loader.load_image(PilotConsole.ERROR_IMAGE_NAME)
        else:
            self.image = game.resource_loader.load_image(PilotConsole.IMAGE_NAME)

        self.rect = old_rect
        self.dirty = 1

class WeaponConsole(Console):
    IMAGE_NAME = 'weapon_console.png'
    ERROR_IMAGE_NAME = 'weapon_console_error.png'

    def __init__(self, game: 'Game', weapon_index: int):
        super().__init__(game, game.resource_loader.load_image(WeaponConsole.IMAGE_NAME))
        self._weapon_index = weapon_index

    @override
    def _move_person(self, person: Person) -> None:
        person.rect.centerx = self.rect.centerx
        person.rect.top = self.rect.bottom + 1

    @override
    def activate(self, ship: 'Ship', person: Person) -> None:
        super().activate(ship, person)
        ship.enable_aiming(self._weapon_index)

    @override
    def deactivate(self, ship: 'Ship') -> None:
        super().deactivate(ship)
        ship.disable_aiming(self._weapon_index)

    @override
    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        if self._person is not None:
            controller = self._person.controller

            x = controller.get_aim_x_axis()
            y = controller.get_aim_y_axis()
            if abs(x) > 0.0 or abs(y) > 0.0:
                angle = math.degrees(math.atan2(-y, x))
                ship.set_aim_angle(self._weapon_index, angle)

            if controller.get_trigger_button():
                ship.fire_laser(self._weapon_index)

    def set_error(self, game: 'Game', is_error: bool) -> None:
        old_rect = self.rect.copy()

        if is_error:
            self.image = game.resource_loader.load_image(WeaponConsole.ERROR_IMAGE_NAME)
        else:
            self.image = game.resource_loader.load_image(WeaponConsole.IMAGE_NAME)

        self.rect = old_rect
        self.dirty = 1

class EngineConsole(Console):
    IMAGE_NAME = 'engine_console.png'
    ERROR_IMAGE_NAME = 'engine_console_error.png'

    def __init__(self, game: 'Game'):
        super().__init__(game, game.resource_loader.load_image(EngineConsole.IMAGE_NAME))

    @override
    def _move_person(self, person: Person) -> None:
        person.rect.bottom = self.rect.top

    @override
    def activate(self, ship: 'Ship', person: Person) -> None:
        super().activate(ship, person)
        person.angle = 180.0

    @override
    def deactivate(self, ship: 'Ship') -> None:
        if self._person is not None:
            self._person.angle = 0.0
        super().deactivate(ship)

    @override
    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        if self._person is not None:
            if not ship.get_engine_enabled():
                ship.enable_engine()
                game.resource_loader.load_sound('fix.wav').play(loops=1)

    def set_error(self, game: 'Game', is_error: bool) -> None:
        old_rect = self.rect.copy()

        if is_error:
            self.image = game.resource_loader.load_image(EngineConsole.ERROR_IMAGE_NAME)
        else:
            self.image = game.resource_loader.load_image(EngineConsole.IMAGE_NAME)

        self.rect = old_rect
        self.dirty = 1

class WeaponSystemConsole(Console):
    IMAGE_NAME = 'weapon_system_console.png'
    ERROR_IMAGE_NAME = 'weapon_system_console_error.png'

    def __init__(self, game: 'Game', weapon_index: int):
        super().__init__(game, game.resource_loader.load_image(WeaponSystemConsole.IMAGE_NAME))
        self._weapon_index = weapon_index

    @override
    def _move_person(self, person: Person) -> None:
        person.rect.centerx = self.rect.centerx
        person.rect.top = self.rect.bottom + 1

    @override
    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        if self._person is not None:
            if not ship.get_weapon_enabled(self._weapon_index):
                ship.enable_weapon(self._weapon_index)
                game.resource_loader.load_sound('fix.wav').play(loops=1)

    def set_error(self, game: 'Game', is_error: bool) -> None:
        old_rect = self.rect.copy()

        if is_error:
            self.image = game.resource_loader.load_image(WeaponSystemConsole.ERROR_IMAGE_NAME)
        else:
            self.image = game.resource_loader.load_image(WeaponSystemConsole.IMAGE_NAME)

        self.rect = old_rect
        self.dirty = 1

class Ship(FlightCollisionSprite):
    MAX_ACCELERATION = 5.0
    LASER_DELAY = 0.5 # seconds
    FLOOR_COLOR = (180, 180, 180)
    WALL_COLOR = (80, 80, 80)
    WALL_WIDTH = 10

    def __init__(self, game: 'Game', interior_view_center: tuple[int, int]):
        self.game = game
        self._logger = logging.getLogger('Ship')
        flight_view_center = (game.flight_view_size[0] // 2, game.flight_view_size[1] // 2)

        background_image = game.resource_loader.load_image('ship1.png')
        self._background_sprite = Sprite(background_image)
        self._background_sprite.rect.center = interior_view_center

        # flight view image
        ship_image_size = background_image.get_size()
        new_size = (ship_image_size[0] // 15, ship_image_size[1] // 15)
        flight_view_image = pygame.transform.scale(background_image, new_size)
        super().__init__(
            flight_view_image,
            float(flight_view_center[0]),
            float(flight_view_center[1]),
            0.0,
            0.0,
        )
        self.rect.center = flight_view_center
        game.flight_view_sprites.add(self)
        game.flight_collision_sprites.add(self)

        # start ship with a small, random velocity
        while (self.dx**2 + self.dy**2)**0.5 < 1.0:
            self.dx = random.random() * 10 - 5
            self.dy = random.random() * 10 - 5

        self._num_weapons = 2
        self._laser_fire_timers = [0.0, 0.0]
        self._hull = 10

        self._floor: list[Sprite] = []
        self._walls: list[Sprite] = []
        self._consoles: list[Console] = []

        self._create_interior(interior_view_center)

        # hull integrity info
        self._status_font = pygame.font.SysFont('Arial', 40)
        self._hull_text = Sprite(pygame.surface.Surface((0, 0)))
        self._update_hull_info()
        game.info_overlay_sprites.add(self._hull_text)

        # weapon aiming
        self._aiming: list[AimSprite] = []
        self._weapon_enabled: list[bool] = []
        colors = [
            (255, 0, 0),
            (0, 240, 0),
        ]
        for i in range(self._num_weapons):
            aim_sprite = AimSprite(colors[i], self.rect.center)
            self._aiming.append(aim_sprite)
            self._weapon_enabled.append(True)

        self._engine_enabled = True

    @property
    def num_weapons(self) -> int:
        return self._num_weapons

    def _create_interior(self, interior_view_center: tuple[int, int]) -> None:
        min_floor_width = 100
        door_gap = 24
        door_thickness = Ship.WALL_WIDTH - 2

        floor_surface = pygame.surface.Surface((min_floor_width, min_floor_width)).convert()
        floor_surface.fill(Ship.FLOOR_COLOR)

        # bridge
        floor1 = Sprite(floor_surface)
        floor1.rect.center = (interior_view_center[0], interior_view_center[1] - 200)
        self._floor.append(floor1)

        floor2 = Sprite(floor_surface)
        floor2.rect.topleft = (floor1.rect.left, floor1.rect.bottom)
        self._floor.append(floor2)

        floor3 = Sprite(floor_surface)
        floor3.rect.topright = (floor2.rect.centerx, floor2.rect.bottom)
        self._floor.append(floor3)

        floor4 = Sprite(floor_surface)
        floor4.rect.topleft = (floor2.rect.centerx, floor2.rect.bottom)
        self._floor.append(floor4)

        floor5 = Sprite(floor_surface)
        floor5.rect.topleft = (floor3.rect.left, floor3.rect.bottom)
        self._floor.append(floor5)

        floor6 = Sprite(floor_surface)
        floor6.rect.topleft = (floor4.rect.left, floor4.rect.bottom)
        self._floor.append(floor6)

        floor_surface2 = pygame.surface.Surface((min_floor_width*2, min_floor_width)).convert()
        floor_surface2.fill(Ship.FLOOR_COLOR)

        floor7 = Sprite(floor_surface2)
        floor7.rect.topleft = (floor5.rect.left, floor5.rect.bottom)
        self._floor.append(floor7)

        wall = self._create_wall(min_floor_width + Ship.WALL_WIDTH*2, Ship.WALL_WIDTH)
        wall.rect.bottomleft = (floor1.rect.left - Ship.WALL_WIDTH, floor1.rect.top)

        wall = self._create_wall(min_floor_width - door_gap*2, Ship.WALL_WIDTH)
        wall.rect.centerx = floor2.rect.centerx
        wall.rect.bottom = floor2.rect.bottom

        wall = self._create_wall(Ship.WALL_WIDTH, min_floor_width*2)
        wall.rect.topright = (floor1.rect.left, floor1.rect.top)

        wall = self._create_wall(Ship.WALL_WIDTH, min_floor_width*2)
        wall.rect.topleft = (floor1.rect.right, floor1.rect.top)

        wall = self._create_wall((min_floor_width - door_gap)//2, Ship.WALL_WIDTH)
        wall.rect.topleft = (floor1.rect.left, floor1.rect.bottom - Ship.WALL_WIDTH//2)

        wall = self._create_wall((min_floor_width - door_gap)//2, Ship.WALL_WIDTH)
        wall.rect.topright = (floor1.rect.right, floor1.rect.bottom - Ship.WALL_WIDTH//2)

        wall = self._create_wall(min_floor_width//2 - Ship.WALL_WIDTH, Ship.WALL_WIDTH)
        wall.rect.bottomleft = floor3.rect.topleft

        wall = self._create_wall(min_floor_width//2 - Ship.WALL_WIDTH, Ship.WALL_WIDTH)
        wall.rect.bottomright = floor4.rect.topright

        wall = self._create_wall(Ship.WALL_WIDTH, min_floor_width*3 + Ship.WALL_WIDTH*2)
        wall.rect.topright = (floor3.rect.left, floor3.rect.top - Ship.WALL_WIDTH)

        wall = self._create_wall(Ship.WALL_WIDTH, min_floor_width*3 + Ship.WALL_WIDTH*2)
        wall.rect.topleft = (floor4.rect.right, floor4.rect.top - Ship.WALL_WIDTH)

        wall = self._create_wall(Ship.WALL_WIDTH, min_floor_width*2 - Ship.WALL_WIDTH//2 - door_gap)
        wall.rect.centerx = floor3.rect.right
        wall.rect.top = floor3.rect.top

        wall = self._create_wall(min_floor_width*2 - door_gap*2, Ship.WALL_WIDTH)
        wall.rect.center = floor3.rect.bottomright

        wall = self._create_wall(min_floor_width*2 - door_gap*2, Ship.WALL_WIDTH)
        wall.rect.center = floor5.rect.bottomright

        wall = self._create_wall(min_floor_width*2, Ship.WALL_WIDTH)
        wall.rect.topleft = floor7.rect.bottomleft

        for wall in self._walls:
            self.game.interior_solid_sprites.add(wall)

        door1 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door1.rect.center = (floor1.rect.centerx, floor1.rect.bottom)

        door2 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door2.rect.bottomleft = (floor2.rect.left, floor2.rect.bottom - 1)

        door3 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door3.rect.bottomright = (floor2.rect.right, floor2.rect.bottom - 1)

        door4 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door4.rect.midleft = (floor3.rect.left, floor3.rect.bottom)

        door5 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door5.rect.midright = (floor4.rect.right, floor4.rect.bottom)

        door6 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door6.rect.midleft = (floor5.rect.left, floor5.rect.bottom)

        door7 = Door(self.game, Door.Orientation.Horizontal, door_gap, door_thickness)
        door7.rect.midright = (floor6.rect.right, floor6.rect.bottom)

        door8 = Door(self.game, Door.Orientation.Vertical, door_gap, door_thickness)
        door8.rect.midbottom = (floor5.rect.right, floor5.rect.bottom - Ship.WALL_WIDTH//2)

        # pilot console
        self._pilot_console = PilotConsole(self.game)
        self._pilot_console.rect.centerx = floor1.rect.centerx
        self._pilot_console.rect.top = floor1.rect.top
        self._consoles.append(self._pilot_console)

        # weapon consoles
        self._weapon_consoles: list[WeaponConsole] = []
        top = floor1.rect.top + 25
        for i in range(self._num_weapons):
            weapon_console = WeaponConsole(self.game, i)
            weapon_console.rect.left = floor1.rect.left
            weapon_console.rect.top = top
            self._weapon_consoles.append(weapon_console)
            self._consoles.append(weapon_console)
            top += 35

        self._engine_console = EngineConsole(self.game)
        self._engine_console.rect.centerx = floor7.rect.centerx
        self._engine_console.rect.bottom = floor7.rect.bottom
        self._consoles.append(self._engine_console)

        self._weapon_system_consoles: list[WeaponSystemConsole] = []
        left = floor6.rect.left + Ship.WALL_WIDTH//2
        for i in range(self._num_weapons):
            weapon_system_console = WeaponSystemConsole(self.game, i)
            weapon_system_console.rect.left = left
            weapon_system_console.rect.top = floor6.rect.top + Ship.WALL_WIDTH//2
            self._weapon_system_consoles.append(weapon_system_console)
            self._consoles.append(weapon_system_console)
            left = weapon_system_console.rect.right

    def _create_wall(self, width: int, height: int) -> Sprite:
        surface = pygame.surface.Surface((width, height)).convert()
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        self._walls.append(wall)
        return wall

    def _update_hull_info(self):
        self._hull_text.image = self._status_font.render(f'Hull: {self._hull}', True, (252, 10, 30))
        self._hull_text.rect.bottomleft = (10, self.game.interior_view_size[1] - 10)
        self._hull_text.dirty = 1

    def get_engine_enabled(self) -> bool:
        return self._engine_enabled

    def get_weapon_enabled(self, weapon_index: int) -> bool:
        return self._weapon_enabled[weapon_index]

    def blit_interior_view(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self._background_sprite.image, self._background_sprite.rect)

        for floor in self._floor:
            surface.blit(floor.image, floor.rect)

        for wall in self._walls:
            surface.blit(wall.image, wall.rect)

    def try_activate_console(self, person: 'Person') -> bool:
        for console in self._consoles:
            console_rect: pygame.rect.Rect = console.rect.inflate(4, 20)
            if console.person is None and console_rect.colliderect(person.rect):
                console.activate(self, person)
                return True

        return False

    def deactivate_console(self, person: 'Person') -> None:
        for console in self._consoles:
            if console.person is person:
                console.deactivate(self)
                break

    def accelerate(self, x_accel: float, y_accel: float) -> None:
        if self._engine_enabled:
            self.dx += x_accel
            self.dy += y_accel

    def enable_engine(self) -> None:
        self._engine_enabled = True
        self._pilot_console.set_error(self.game, False)
        self._engine_console.set_error(self.game, False)

    def disable_engine(self) -> None:
        self._engine_enabled = False
        self._pilot_console.set_error(self.game, True)
        self._engine_console.set_error(self.game, True)

    def enable_weapon(self, weapon_index: int) -> None:
        self._weapon_enabled[weapon_index] = True
        self._weapon_consoles[weapon_index].set_error(self.game, False)
        self._weapon_system_consoles[weapon_index].set_error(self.game, False)
        if self._weapon_consoles[weapon_index].person is not None:
            self.enable_aiming(weapon_index)

    def disable_weapon(self, weapon_index: int) -> None:
        self._weapon_enabled[weapon_index] = False
        self._weapon_consoles[weapon_index].set_error(self.game, True)
        self._weapon_system_consoles[weapon_index].set_error(self.game, True)
        self.disable_aiming(weapon_index)

    def enable_aiming(self, weapon_index: int) -> None:
        if self._weapon_enabled[weapon_index]:
            self.game.flight_view_sprites.add(self._aiming[weapon_index])

    def disable_aiming(self, weapon_index: int) -> None:
        self.game.flight_view_sprites.remove(self._aiming[weapon_index])

    def set_aim_angle(self, weapon_index: int, angle: float) -> None:
        self._aiming[weapon_index].angle = angle

    def fire_laser(self, weapon_index: int) -> None:
        if self._weapon_enabled[weapon_index]:
            if self._laser_fire_timers[weapon_index] <= 0.0:
                angle = self._aiming[weapon_index].angle
                Laser(self.game, self.rect.center, angle, self)
                self._laser_fire_timers[weapon_index] = Ship.LASER_DELAY

    def update(self, game: 'Game') -> None:
        for i in range(len(self._laser_fire_timers)):
            self._laser_fire_timers[i] = max(0.0, self._laser_fire_timers[i] - game.frame_time)

        for console in self._consoles:
            console.update_ship(game, self)

        self.x += self.dx * game.frame_time
        self.y += self.dy * game.frame_time

        self.rect.center = (int(self.x), int(self.y))

        # wrap around if the ship goes past the top or bottom of the screen
        if self.rect.top >= game.flight_view_size[1]:
            self.rect.bottom = 0
            self.y = float(self.rect.centery)
        elif self.rect.bottom <= 0:
            self.rect.top = game.flight_view_size[1]
            self.y = float(self.rect.centery)

        # wrap around if the ship goes past the left or right of the screen
        if self.rect.left >= game.flight_view_size[0]:
            self.rect.right = 0
            self.x = float(self.rect.centerx)
        elif self.rect.right <= 0:
            self.rect.left = game.flight_view_size[0]
            self.x = float(self.rect.centerx)

        for aiming in self._aiming:
            aiming.origin = self.rect.center

        self.check_collision(game)

    @override
    def on_collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        self.dx = new_dx
        self.dy = new_dy

        hit_points = int(force / 20_000)
        self._logger.info(f'Collision: total force: {force:.1f}, hit points: {hit_points}')
        self.damage(game, hit_points)

    @override
    def damage(self, game: 'Game', hit_points: int) -> None:
        if self._engine_enabled and hit_points > 0 and random.randint(0, 1) == 0:
            self.disable_engine()
            hit_points -= 1

        for i in range(len(self._weapon_enabled)):
            if self._weapon_enabled[i] and hit_points > 0 and random.randint(0, 1) == 0:
                self.disable_weapon(i)
                hit_points -= 1

        if hit_points > 0:
            self._hull = max(0, self._hull - hit_points)
            self._update_hull_info()
            if self._hull <= 0:
                self.destroy()

    def destroy(self) -> None:
        # remove graphics
        for i in range(len(self._aiming)):
            self.disable_aiming(i)
        self.kill()

        # create explosion graphic
        ShipExplosionAnimation(self.game, self.rect.center)

        self.game.resource_loader.load_sound('defeat.wav').play()

        self.game.end_mission(delay=True)
