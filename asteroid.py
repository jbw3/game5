import os
import pygame
import random
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from game import Game

class Asteroid(pygame.sprite.Sprite):
    BIG_IMAGE = pygame.image.load(os.path.join('images', 'asteroid_big1.png'))
    MIN_SPEED = 1
    MAX_SPEED = 120

    def __init__(self, game: 'Game', center: tuple[int, int]):
        super().__init__()

        self.image = Asteroid.BIG_IMAGE
        self.rect = self.image.get_rect()
        self.rect.center = center

        game.flight_view_sprites.add(self)

        self._x = float(center[0])
        self._y = float(center[1])

        self._dx = 0.0
        self._dy = 0.0
        while self._dx == 0.0 and self._dy == 0.0:
            self._dx = float(random.randint(-Asteroid.MAX_SPEED, Asteroid.MAX_SPEED))
            self._dy = float(random.randint(-Asteroid.MAX_SPEED, Asteroid.MAX_SPEED))

    @override
    def update(self, game: 'Game') -> None:
        self._x += self._dx * game.frame_time
        self._y += self._dy * game.frame_time

        self.rect.center = (int(self._x), int(self._y))

        flight_view_size = game.flight_view_size

        # wrap around if the asteroid goes past the top or bottom of the screen
        if self.rect.top >= flight_view_size[1]:
            self.rect.bottom = 0
            self._y = float(self.rect.centery)
        elif self.rect.bottom <= 0:
            self.rect.top = flight_view_size[1]
            self._y = float(self.rect.centery)

        # wrap around if the asteroid goes past the left or right of the screen
        if self.rect.left >= flight_view_size[0]:
            self.rect.right = 0
            self._x = float(self.rect.centerx)
        elif self.rect.right <= 0:
            self.rect.left = flight_view_size[0]
            self._x = float(self.rect.centerx)
