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
        game.sprites.add(background_sprite)

        image = pygame.surface.Surface((100, 100))
        image.fill(Ship.FLOOR_COLOR)
        self._sprite = pygame.sprite.Sprite()
        self._sprite.image = image
        self._sprite.rect = self._sprite.image.get_rect()
        self._sprite.rect.center = center
        game.sprites.add(self._sprite)

        wall_width = 10
        self._walls: list[pygame.sprite.Sprite] = []

        # top wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.bottomleft = (self._sprite.rect.left - wall_width, self._sprite.rect.top)
        self._walls.append(wall)

        # bottom wall
        surface = pygame.surface.Surface((100 + wall_width*2, wall_width))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topleft = (self._sprite.rect.left - wall_width, self._sprite.rect.bottom)
        self._walls.append(wall)

        # left wall
        surface = pygame.surface.Surface((wall_width, 100))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topright = (self._sprite.rect.left, self._sprite.rect.top)
        self._walls.append(wall)

        # right wall
        surface = pygame.surface.Surface((wall_width, 100))
        surface.fill(Ship.WALL_COLOR)
        wall = pygame.sprite.Sprite()
        wall.image = surface
        wall.rect = surface.get_rect()
        wall.rect.topleft = self._sprite.rect.right, self._sprite.rect.top
        self._walls.append(wall)

        for wall in self._walls:
            game.sprites.add(wall)
            game.solid.add(wall)

    def update(self, game: 'Game') -> None:
        pass
