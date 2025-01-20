import os
import pygame
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from game import Game

class Laser(pygame.sprite.Sprite):
    RED_IMAGE = pygame.image.load(os.path.join('images', 'laser_red.png'))

    SPEED = 1000

    def __init__(self, game: 'Game', center: tuple[int, int], angle: float):
        super().__init__()

        self.image = Laser.RED_IMAGE
        self.rect = self.image.get_rect()
        self.rect.center = center

        game.flight_view_sprites.add(self)

        self._x = float(center[0])
        self._y = float(center[1])

    @override
    def update(self, game: 'Game') -> None:
        self._y += Laser.SPEED * game.frame_time

        self.rect.center = (int(self._x), int(self._y))

        view_width, view_height = game.flight_view_size
        if self._x < 0.0 or self._x >= view_width or self._y < 0.0 or self._y >= view_height:
            game.flight_view_sprites.remove(self)
