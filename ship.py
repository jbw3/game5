import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game

class Ship:
    FLOOR_COLOR = (180, 180, 180)

    def __init__(self, game: 'Game'):
        image = pygame.surface.Surface((100, 100))
        image.fill(Ship.FLOOR_COLOR)
        self._sprite = pygame.sprite.Sprite()
        self._sprite.image = image
        self._sprite.rect = self._sprite.image.get_rect()
        self._sprite.rect.center = (200, 200)

        game.sprites.add(self._sprite)

    def update(self, game: 'Game') -> None:
        pass
