import math
import os
import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Laser(Sprite):
    RED_IMAGE = pygame.image.load(os.path.join('images', 'laser_red.png'))

    SPEED = 1000

    def __init__(self, game: 'Game', center: tuple[int, int], angle: float):
        super().__init__(pygame.transform.rotate(Laser.RED_IMAGE, angle))
        self.rect.center = center

        game.flight_view_sprites.add(self)

        self._x = float(center[0])
        self._y = float(center[1])

        self._dx = Laser.SPEED * math.cos(math.radians(angle))
        self._dy = Laser.SPEED * math.sin(math.radians(-angle))

    @override
    def update(self, game: 'Game') -> None:
        self._x += self._dx * game.frame_time
        self._y += self._dy * game.frame_time

        self.rect.center = (int(self._x), int(self._y))

        # remove laser when it goes beyond the bounds of the view
        view_width, view_height = game.flight_view_size
        if self._x < 0.0 or self._x >= view_width or self._y < 0.0 or self._y >= view_height:
            game.flight_view_sprites.remove(self)

        collide_sprites = pygame.sprite.spritecollide(self, game.flight_collision_sprites, False)
        if len(collide_sprites) > 0:
            collide_sprites[0].collide(game)
            game.flight_view_sprites.remove(self)
