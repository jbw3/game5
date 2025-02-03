import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Animation(Sprite):
    def __init__(self, images: list[pygame.surface.Surface], period: int):
        self._images = images
        self._index = 0
        super().__init__(self._images[self._index])

        self._period = period
        self._next_change = pygame.time.get_ticks() + self._period

    @override
    def update(self, game: 'Game') -> None:
        current_time = pygame.time.get_ticks()
        if current_time >= self._next_change:
            self._index += 1
            if self._index >= len(self._images):
                self.kill()
            else:
                old_center = self.rect.center
                self.image = self._images[self._index]
                self.rect.center = old_center
                self.dirty = 1
                self._next_change += self._period
