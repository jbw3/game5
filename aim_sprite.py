import pygame

from sprite import Sprite

class AimSprite(Sprite):
    LENGTH = 80

    def __init__(self, color: tuple[int, int, int], origin: tuple[int, int]):
        self._orig_image = pygame.surface.Surface((AimSprite.LENGTH, 3))
        self._orig_image.fill((0, 0, 0))
        self._orig_image.set_colorkey((0, 0, 0))
        pygame.draw.line(self._orig_image, color, (0, 1), (AimSprite.LENGTH - 1, 1))
        super().__init__(self._orig_image)

        self._origin = origin
        self.angle = 90.0

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_angle: float) -> None:
        self._angle = new_angle % 360.0

        self.image = pygame.transform.rotate(self._orig_image, new_angle)
        self.rect = self.image.get_rect()
        self._update_position()

    @property
    def origin(self) -> tuple[int, int]:
        return self._origin

    @origin.setter
    def origin(self, new_origin: tuple[int, int]) -> None:
        self._origin = new_origin
        self._update_position()

    def _update_position(self) -> None:
        if 0.0 <= self._angle < 90.0:
            self.rect.left = self._origin[0]
            self.rect.bottom = self._origin[1]
        elif 90.0 <= self._angle < 180.0:
            self.rect.right = self._origin[0]
            self.rect.bottom = self._origin[1]
        elif 180.0 <= self._angle < 270.0:
            self.rect.right = self._origin[0]
            self.rect.top = self._origin[1]
        else:
            self.rect.left = self._origin[0]
            self.rect.top = self._origin[1]
