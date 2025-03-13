import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Animation(Sprite):
    def __init__(self, images: list[pygame.surface.Surface], period: int = -1, loop: bool = False):
        super().__init__(images[0])
        self._images: list[pygame.surface.Surface] = []
        self._angle = 0.0
        self.set_images(images, period, loop)

    def _rotate_images(self) -> None:
        self._images.clear()
        for image in self._orig_images:
            rotated_image = pygame.transform.rotate(image, self._angle)
            self._images.append(rotated_image)

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_angle: float) -> None:
        self._angle = new_angle % 360.0
        self._rotate_images()

    def set_images(self, images: list[pygame.surface.Surface], period: int = -1, loop: bool = False) -> None:
        self._orig_images = images[:]
        self._rotate_images()
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

class ShipExplosionAnimation(Animation):
    def __init__(self, game: 'Game', center: tuple[int, int]):
        explosion_images = [
            game.resource_loader.load_image(f'explosion{i+1}.png')
            for i in range(8)
        ]
        super().__init__(explosion_images, 62)
        self.rect.center = center

        game.flight_view_sprites.add(self)
