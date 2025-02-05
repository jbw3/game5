import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Animation(Sprite):
    def __init__(self, images: list[pygame.surface.Surface], period: int = -1, loop: bool = False):
        super().__init__(images[0])
        self.set_images(images, period, loop)

    def set_images(self, images: list[pygame.surface.Surface], period: int = -1, loop: bool = False) -> None:
        self._images = images
        self._index = 0
        self._period = period
        self._loop = loop
        if self._period >= 0:
            self._next_change = pygame.time.get_ticks() + self._period

        self.image = self._images[self._index]

    @override
    def update(self, game: 'Game') -> None:
        if self._period >= 0:
            current_time = pygame.time.get_ticks()
            if current_time >= self._next_change:
                self._index += 1
                if self._index >= len(self._images):
                    if not self._loop:
                        self.kill()
                        return
                    self._index = 0

                old_center = self.rect.center
                self.image = self._images[self._index]
                self.rect.center = old_center
                self.dirty = 1
                self._next_change += self._period
