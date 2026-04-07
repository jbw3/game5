import pygame
from typing import TYPE_CHECKING, override

from animation import Animation

if TYPE_CHECKING:
    from game import Game

class FireExtinguisherSpray(Animation):
    def __init__(self, game: 'Game') -> None:
        images = [
            game.resource_loader.load_image(f'fire_extinguisher_spray{i+1}.png')
            for i in range(5)
        ]

        super().__init__(images, 150, loop=True)

        self._mask = pygame.surface.Surface((25, 15))
        self._mask.fill((0, 0, 0))
        self._mask.set_colorkey((0, 0, 0))

        if game.debug:
            self._mask.set_alpha(100)
        else:
            self._mask.set_alpha(0)

        points = [
            (0, 6),
            (24, 0),
            (24, 14),
            (0, 8),
        ]
        pygame.draw.polygon(self._mask, (100, 100, 100), points)
