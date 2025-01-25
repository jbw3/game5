import os
import pygame
import random
from typing import TYPE_CHECKING, override

from laser import Laser
from person import Person
from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Console(Sprite):
    PILOT_CONSOLE_IMAGE = pygame.image.load(os.path.join('images', 'pilot_console.png'))
    WEAPON_CONSOLE_IMAGE = pygame.image.load(os.path.join('images', 'weapon_console.png'))

    def __init__(self, game: 'Game', image: pygame.surface.Surface):
        super().__init__(image)

        game.interior_view_sprites.add(self)
        game.interior_solid_sprites.add(self)

        self._person: Person|None = None

    @property
    def person(self) -> Person|None:
        return self._person

    def activate(self, ship: 'Ship', person: Person) -> None:
        self._person = person

        self._person.rect.centerx = self.rect.centerx
        self._person.rect.top = self.rect.bottom + 4

    def deactivate(self, ship: 'Ship') -> None:
        self._person = None

    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        pass

class PilotConsole(Console):
    def __init__(self, game: 'Game'):
        super().__init__(game, Console.PILOT_CONSOLE_IMAGE)

    @override
    def update_ship(self, game: 'Game', ship: 'Ship') -> None:
        if self._person is not None:
            joystick = self._person.joystick

            a0 = joystick.get_axis(0)
            if a0 < -0.2 or a0 > 0.2:
                x_accel = a0 * Ship.MAX_ACCELERATION
            else:
                x_accel = 0.0

            a1 = joystick.get_axis(1)
            if a1 < -0.2 or a1 > 0.2:
                y_accel = a1 * Ship.MAX_ACCELERATION
            else:
                y_accel = 0.0

            ship.accelerate(x_accel, y_accel)

class WeaponConsole(Console):
    def __init__(self, game: 'Game', weapon_index: int):
        super().__init__(game, Console.WEAPON_CONSOLE_IMAGE)
        self._weapon_index = weapon_index

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
            joystick = self._person.joystick

            a0 = joystick.get_axis(0)
            if a0 < -0.2:
                ship.rotate_aim_counterclockwise(self._weapon_index)
            elif a0 > 0.2:
                ship.rotate_aim_clockwise(self._weapon_index)

            if joystick.get_button(5):
                ship.fire_laser(self._weapon_index)

class AimSprite(Sprite):
    LENGTH = 80

    def __init__(self, color: tuple[int, int, int], origin: tuple[int, int]):
        self._orig_image = pygame.surface.Surface((AimSprite.LENGTH, 3))
        self._orig_image.fill((0, 0, 0))
        self._orig_image.set_colorkey((0, 0, 0))
        pygame.draw.line(self._orig_image, color, (0, 1), (AimSprite.LENGTH - 1, 1))
        super().__init__(self._orig_image)

        self._origin = origin
        self.angle = 90.0

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_angle: float) -> None:
        self._angle = new_angle % 360.0

        self.image = pygame.transform.rotate(self._orig_image, new_angle)
        self.rect = self.image.get_rect()
        self._update_position()

    @property
    def origin(self) -> tuple[int, int]:
        return self._origin

    @origin.setter
    def origin(self, new_origin: tuple[int, int]) -> None:
        self._origin = new_origin
        self._update_position()

    def _update_position(self) -> None:
        if 0.0 <= self._angle < 90.0:
            self.rect.left = self._origin[0]
            self.rect.bottom = self._origin[1]
        elif 90.0 <= self._angle < 180.0:
            self.rect.right = self._origin[0]
            self.rect.bottom = self._origin[1]
        elif 180.0 <= self._angle < 270.0:
            self.rect.right = self._origin[0]
            self.rect.top = self._origin[1]
        else:
            self.rect.left = self._origin[0]
            self.rect.top = self._origin[1]

class Ship:
    MAX_ACCELERATION = 5.0
    LASER_DELAY = 600 # ms
    AIM_ANGLE_RATE = 120.0 # degrees
    FLOOR_COLOR = (180, 180, 180)
    WALL_COLOR = (80, 80, 80)

    def __init__(self, game: 'Game', interior_view_center: tuple[int, int]):
        self.game = game
        flight_view_center = (game.flight_view_size[0] // 2, game.flight_view_size[1] // 2)
        self._x = float(flight_view_center[0])
        self._y = float(flight_view_center[1])
        self._dx = 0.0
        self._dy = 0.0

        # start ship with a small, random velocity
        while abs(self._dx) < 1.0 and abs(self._dy) < 1.0:
            self._dx = random.random() * 10 - 5
            self._dy = random.random() * 10 - 5

        self._next_available_laser_fire = [0, 0]

        background_image = pygame.image.load(os.path.join('images', 'ship1.png'))
        background_sprite = Sprite(background_image)
        background_sprite.rect.center = interior_view_center
        game.interior_view_sprites.add(background_sprite)

        wall_width = 10
        self._floor: list[pygame.sprite.Sprite] = []
        self._walls: list[pygame.sprite.Sprite] = []

        surface = pygame.surface.Surface((100, 100))
        surface.fill(Ship.FLOOR_COLOR)
        floor1 = Sprite(surface)
        floor1.rect.center = (interior_view_center[0], interior_view_center[1] - 50)
        self._floor.append(floor1)

        surface = pygame.surface.Surface((100, 100))
        surface.fill(Ship.FLOOR_COLOR)
        floor2 = Sprite(surface)
        floor2.rect.topleft = (floor1.rect.left, floor1.rect.bottom)
        self._floor.append(floor2)

        # top wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.bottomleft = (floor1.rect.left - wall_width, floor1.rect.top)
        self._walls.append(wall)

        # bottom wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.topleft = (floor2.rect.left - wall_width, floor2.rect.bottom)
        self._walls.append(wall)

        # left wall
        surface = pygame.surface.Surface((wall_width, 200))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.topright = (floor1.rect.left, floor1.rect.top)
        self._walls.append(wall)

        # right wall
        surface = pygame.surface.Surface((wall_width, 200))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.topleft = (floor1.rect.right, floor1.rect.top)
        self._walls.append(wall)

        surface = pygame.surface.Surface((38, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.topleft = (floor1.rect.left, floor1.rect.bottom - wall_width//2)
        self._walls.append(wall)

        surface = pygame.surface.Surface((38, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = Sprite(surface)
        wall.rect.topright = (floor1.rect.right, floor1.rect.bottom - wall_width//2)
        self._walls.append(wall)

        for floor in self._floor:
            game.interior_view_sprites.add(floor)

        for wall in self._walls:
            game.interior_view_sprites.add(wall)
            game.interior_solid_sprites.add(wall)

        self._consoles: list[Console] = []

        # pilot console
        pilot_console = PilotConsole(game)
        pilot_console.rect.centerx = floor1.rect.centerx
        pilot_console.rect.top = floor1.rect.top
        self._consoles.append(pilot_console)

        # weapon consoles
        top = floor1.rect.top + 25
        for i in range(2):
            weapon_console = WeaponConsole(game, i)
            weapon_console.rect.left = floor1.rect.left
            weapon_console.rect.top = top
            self._consoles.append(weapon_console)
            top += 35

        # flight view image
        ship_image_size = background_image.get_size()
        new_size = (ship_image_size[0] // 10, ship_image_size[1] // 10)
        flight_view_image = pygame.transform.scale(background_image, new_size)
        self._flight_sprite = Sprite(flight_view_image)
        self._flight_sprite.rect.center = flight_view_center
        game.flight_view_sprites.add(self._flight_sprite)

        # weapon aiming
        self._aiming: list[AimSprite] = []
        colors = [
            (255, 0, 0),
            (0, 240, 0),
        ]
        for i in range(2):
            aim_sprite = AimSprite(colors[i], self._flight_sprite.rect.center)
            self._aiming.append(aim_sprite)

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
        self._dx += x_accel
        self._dy += y_accel

    def enable_aiming(self, weapon_index: int) -> None:
        self.game.flight_view_sprites.add(self._aiming[weapon_index])

    def disable_aiming(self, weapon_index: int) -> None:
        self.game.flight_view_sprites.remove(self._aiming[weapon_index])

    def rotate_aim_clockwise(self, weapon_index: int) -> None:
        self._aiming[weapon_index].angle -= Ship.AIM_ANGLE_RATE * self.game.frame_time

    def rotate_aim_counterclockwise(self, weapon_index: int) -> None:
        self._aiming[weapon_index].angle += Ship.AIM_ANGLE_RATE * self.game.frame_time

    def fire_laser(self, weapon_index: int) -> None:
        ticks = pygame.time.get_ticks()
        if ticks >= self._next_available_laser_fire[weapon_index]:
            angle = self._aiming[weapon_index].angle
            Laser(self.game, self._flight_sprite.rect.center, angle)
            self._next_available_laser_fire[weapon_index] = ticks + Ship.LASER_DELAY

    def update(self, game: 'Game') -> None:
        for console in self._consoles:
            console.update_ship(game, self)

        self._x += self._dx * game.frame_time
        self._y += self._dy * game.frame_time

        self._flight_sprite.rect.center = (int(self._x), int(self._y))

        # wrap around if the ship goes past the top or bottom of the screen
        if self._flight_sprite.rect.top >= game.flight_view_size[1]:
            self._flight_sprite.rect.bottom = 0
            self._y = float(self._flight_sprite.rect.centery)
        elif self._flight_sprite.rect.bottom <= 0:
            self._flight_sprite.rect.top = game.flight_view_size[1]
            self._y = float(self._flight_sprite.rect.centery)

        # wrap around if the ship goes past the left or right of the screen
        if self._flight_sprite.rect.left >= game.flight_view_size[0]:
            self._flight_sprite.rect.right = 0
            self._x = float(self._flight_sprite.rect.centerx)
        elif self._flight_sprite.rect.right <= 0:
            self._flight_sprite.rect.left = game.flight_view_size[0]
            self._x = float(self._flight_sprite.rect.centerx)

        for aiming in self._aiming:
            aiming.origin = self._flight_sprite.rect.center

        collision = False
        for sprite in pygame.sprite.spritecollide(self._flight_sprite, game.flight_collision_sprites, False):
            sprite.collide(game)
            collision = True

        if collision:
            game.flight_view_sprites.remove(self._flight_sprite)
            game.end_mission()
