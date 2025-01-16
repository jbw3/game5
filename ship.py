import os
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game

class Ship:
    FLOOR_COLOR = (180, 180, 180)
    WALL_COLOR = (80, 80, 80)

    def __init__(self, game: 'Game', center: tuple[int, int]):
        background_image = pygame.image.load(os.path.join('images', 'ship1.png'))
        background_sprite = pygame.sprite.Sprite()
        background_sprite.image = background_image
        background_sprite.rect = background_image.get_rect()
        background_sprite.rect.center = center
        game.interior_view_sprites.add(background_sprite)

        wall_width = 10
        self._floor: list[pygame.sprite.Sprite] = []
        self._walls: list[pygame.sprite.Sprite] = []

        surface = pygame.surface.Surface((100, 100))
        surface.fill(Ship.FLOOR_COLOR)
        floor1 = pygame.sprite.Sprite()
        floor1.image = surface
        floor1.rect = floor1.image.get_rect()
        floor1.rect.center = (center[0], center[1] - 50)
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
            game.solid_sprites.add(wall)

        self._pilot_console = pygame.sprite.Sprite()
        self._pilot_console.image = pygame.image.load(os.path.join('images', 'pilot_console.png'))
        self._pilot_console.rect = self._pilot_console.image.get_rect()
        self._pilot_console.rect.centerx = floor1.rect.centerx
        self._pilot_console.rect.top = floor1.rect.top
        game.interior_view_sprites.add(self._pilot_console)
        game.solid_sprites.add(self._pilot_console)

        # flight view image
        ship_image_size = background_image.get_size()
        new_size = (ship_image_size[0] // 10, ship_image_size[1] // 10)
        flight_view_image = pygame.transform.scale(background_image, new_size)
        self._flight_sprite = pygame.sprite.Sprite()
        self._flight_sprite.image = flight_view_image
        self._flight_sprite.rect = flight_view_image.get_rect()
        self._flight_sprite.rect.center = center
        game.flight_view_sprites.add(self._flight_sprite)

    def update(self, game: 'Game') -> None:
        pass
