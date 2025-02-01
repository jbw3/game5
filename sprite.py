import pygame

class Sprite(pygame.sprite.DirtySprite):
    def __init__(self, image: pygame.surface.Surface):
        super().__init__()
        self.image = image

    @property
    def image(self) -> pygame.surface.Surface:
        return self._image

    @image.setter
    def image(self, value: pygame.surface.Surface) -> None:
        self._image = value
        self.rect = self._image.get_rect()
