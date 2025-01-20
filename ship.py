import os
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from person import Person

class Ship:
    MAX_ACCELERATION = 5.0
    FLOOR_COLOR = (180, 180, 180)
    WALL_COLOR = (80, 80, 80)

    def __init__(self, game: 'Game', interior_view_center: tuple[int, int]):

        flight_view_center = (game.flight_view_size[0] // 2, game.flight_view_size[1] // 2)
        self._x = float(flight_view_center[0])
        self._y = float(flight_view_center[1])
        self._dx = 0.0
        self._dy = 0.0

        background_image = pygame.image.load(os.path.join('images', 'ship1.png'))
        background_sprite = pygame.sprite.Sprite()
        background_sprite.image = background_image
        background_sprite.rect = background_image.get_rect()
        background_sprite.rect.center = interior_view_center
        game.interior_view_sprites.add(background_sprite)

        wall_width = 10
        self._floor: list[pygame.sprite.Sprite] = []
        self._walls: list[pygame.sprite.Sprite] = []

        surface = pygame.surface.Surface((100, 100))
        surface.fill(Ship.FLOOR_COLOR)
        floor1 = pygame.sprite.Sprite()
        floor1.image = surface
        floor1.rect = floor1.image.get_rect()
        floor1.rect.center = (interior_view_center[0], interior_view_center[1] - 50)
        self._floor.append(floor1)

        surface = pygame.surface.Surface((100, 100))
        surface.fill(Ship.FLOOR_COLOR)
        floor2 = pygame.sprite.Sprite()
        floor2.image = surface
        floor2.rect = floor2.image.get_rect()
        floor2.rect.topleft = (floor1.rect.left, floor1.rect.bottom)
        self._floor.append(floor2)

        # top wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.bottomleft = (floor1.rect.left - wall_width, floor1.rect.top)
        self._walls.append(wall)

        # bottom wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topleft = (floor2.rect.left - wall_width, floor2.rect.bottom)
        self._walls.append(wall)

        # left wall
        surface = pygame.surface.Surface((wall_width, 200))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topright = (floor1.rect.left, floor1.rect.top)
        self._walls.append(wall)

        # right wall
        surface = pygame.surface.Surface((wall_width, 200))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topleft = (floor1.rect.right, floor1.rect.top)
        self._walls.append(wall)

        surface = pygame.surface.Surface((38, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topleft = (floor1.rect.left, floor1.rect.bottom - wall_width//2)
        self._walls.append(wall)

        surface = pygame.surface.Surface((38, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topright = (floor1.rect.right, floor1.rect.bottom - wall_width//2)
        self._walls.append(wall)

        for floor in self._floor:
            game.interior_view_sprites.add(floor)

        for wall in self._walls:
            game.interior_view_sprites.add(wall)
            game.interior_solid_sprites.add(wall)

        self._pilot_console = pygame.sprite.Sprite()
        self._pilot_console.image = pygame.image.load(os.path.join('images', 'pilot_console.png'))
        self._pilot_console.rect = self._pilot_console.image.get_rect()
        self._pilot_console.rect.centerx = floor1.rect.centerx
        self._pilot_console.rect.top = floor1.rect.top
        game.interior_view_sprites.add(self._pilot_console)
        game.interior_solid_sprites.add(self._pilot_console)

        self._pilot_console_person: Person|None = None

        # flight view image
        ship_image_size = background_image.get_size()
        new_size = (ship_image_size[0] // 10, ship_image_size[1] // 10)
        flight_view_image = pygame.transform.scale(background_image, new_size)
        self._flight_sprite = pygame.sprite.Sprite()
        self._flight_sprite.image = flight_view_image
        self._flight_sprite.rect = flight_view_image.get_rect()
        self._flight_sprite.rect.center = flight_view_center
        game.flight_view_sprites.add(self._flight_sprite)

        self._joystick: pygame.joystick.JoystickType|None = None

    def try_activate_console(self, person: 'Person') -> bool:
        console_rect: pygame.rect.Rect = self._pilot_console.rect.inflate(4, 20)
        if self._pilot_console_person is not None or not console_rect.colliderect(person.rect):
            return False

        self._pilot_console_person = person
        self._joystick = person.joystick

        self._pilot_console_person.rect.centerx = self._pilot_console.rect.centerx
        self._pilot_console_person.rect.top = self._pilot_console.rect.bottom + 4

        return True

    def deactivate_console(self, person: 'Person') -> None:
        self._pilot_console_person = None
        self._joystick = None

    def update(self, game: 'Game') -> None:
        if self._joystick is not None:
            a0 = self._joystick.get_axis(0)
            if a0 < -0.2 or a0 > 0.2:
                self._dx += a0 * Ship.MAX_ACCELERATION

            a1 = self._joystick.get_axis(1)
            if a1 < -0.2 or a1 > 0.2:
                self._dy += a1 * Ship.MAX_ACCELERATION

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

        for sprite in pygame.sprite.spritecollide(self._flight_sprite, game.flight_collision_sprites, False):
            sprite.collide(game)
