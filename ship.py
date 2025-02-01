import pygame
import random
from typing import TYPE_CHECKING, override

from door import Door
from laser import Laser
from person import Person
from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Console(Sprite):
    PILOT_CONSOLE_IMAGE_NAME = 'pilot_console.png'
    WEAPON_CONSOLE_IMAGE_NAME = 'weapon_console.png'

    def __init__(self, game: 'Game', image: pygame.surface.Surface):
        super().__init__(image)
        self.dirty = 1
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
        super().__init__(game, game.image_loader.load(Console.PILOT_CONSOLE_IMAGE_NAME))

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
        super().__init__(game, game.image_loader.load(Console.WEAPON_CONSOLE_IMAGE_NAME))
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
    WALL_WIDTH = 10

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
        self._hull = 3

        background_image = game.image_loader.load('ship1.png')
        self._background_sprite = Sprite(background_image)
        self._background_sprite.rect.center = interior_view_center

        self._floor: list[Sprite] = []
        self._walls: list[Sprite] = []
        self._consoles: list[Console] = []

        self._create_interior(interior_view_center)

        # hull integrity info
        self._status_font = pygame.font.SysFont('Arial', 40)
        self._hull_text = Sprite(pygame.surface.Surface((0, 0)))
        self._update_hull_info()
        game.info_overlay_sprites.add(self._hull_text)

        # flight view image
        ship_image_size = background_image.get_size()
        new_size = (ship_image_size[0] // 15, ship_image_size[1] // 15)
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
        pilot_console = PilotConsole(self.game)
        pilot_console.rect.centerx = floor1.rect.centerx
        pilot_console.rect.top = floor1.rect.top
        self._consoles.append(pilot_console)

        # weapon consoles
        top = floor1.rect.top + 25
        for i in range(2):
            weapon_console = WeaponConsole(self.game, i)
            weapon_console.rect.left = floor1.rect.left
            weapon_console.rect.top = top
            self._consoles.append(weapon_console)
            top += 35

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

        last_rect = self._flight_sprite.rect.copy()
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

            if last_rect.top >= sprite.rect.bottom:
                self._flight_sprite.rect.top = sprite.rect.bottom
                self._y = float(self._flight_sprite.rect.centery)
            elif last_rect.bottom <= sprite.rect.top:
                self._flight_sprite.rect.bottom = sprite.rect.top
                self._y = float(self._flight_sprite.rect.centery)

            if last_rect.left >= sprite.rect.right:
                self._flight_sprite.rect.left = sprite.rect.right
                self._x = float(self._flight_sprite.rect.centerx)
            elif last_rect.right <= sprite.rect.left:
                self._flight_sprite.rect.right = sprite.rect.left
                self._x = float(self._flight_sprite.rect.centerx)

        if collision:
            # TODO: use elastic collision equations
            self._dx = -self._dx
            self._dy = -self._dy

            self._hull -= 1
            self._update_hull_info()
            if self._hull <= 0:
                game.flight_view_sprites.remove(self._flight_sprite)
                game.end_mission()
