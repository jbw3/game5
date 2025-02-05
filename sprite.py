import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game

class Sprite(pygame.sprite.DirtySprite):
    def __init__(self, image: pygame.surface.Surface):
        super().__init__()
        self._image = image
        self.rect = self._image.get_rect()

    @property
    def image(self) -> pygame.surface.Surface:
        return self._image

    @image.setter
    def image(self, value: pygame.surface.Surface) -> None:
        old_topleft = self.rect.topleft
        self._image = value
        self.rect = self._image.get_rect()
        self.rect.topleft = old_topleft

class FlightCollisionSprite(Sprite):
    def __init__(self, image: pygame.surface.Surface, x: float, y: float, dx: float, dy: float):
        super().__init__(image)
        self._x = x
        self._y = y
        self._dx = dx
        self._dy = dy

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def dx(self) -> float:
        return self._dx

    @property
    def dy(self) -> float:
        return self._dy

    def collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        pass

    def damage(self, game: 'Game') -> None:
        pass
