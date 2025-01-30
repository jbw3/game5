from enum import Enum, unique
import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Door(Sprite):
    @unique
    class Orientation(Enum):
        Horizontal = 0
        Vertical = 1

    COLORKEY = (0, 0, 0)
    COLOR = (110, 120, 150)
    MOVE_RATE = 60.0

    def __init__(self, game: 'Game', orientation: Orientation, gap_len: int, thickness: int):
        self._orientation = orientation
        self._gap_len = gap_len
        self._current_len = self._gap_len / 2
        self._thickness = thickness

        if self._orientation == Door.Orientation.Horizontal:
            width = self._gap_len
            height = self._thickness
        else:
            width = self._thickness
            height = self._gap_len

        surface = pygame.surface.Surface((width, height))
        surface.set_colorkey(Door.COLORKEY)
        surface.fill(Door.COLOR)

        super().__init__(surface)
        game.interior_view_sprites.add(self)

    @override
    def update(self, game: 'Game') -> None:
        if self._orientation == Door.Orientation.Horizontal:
            proximity_rect = self.rect.inflate(8, 10)
        else:
            proximity_rect = self.rect.inflate(10, 8)

        opening = False
        for person in game.people_sprites:
            if proximity_rect.colliderect(person.rect):
                opening = True
                break

        needs_update = False
        if opening:
            if self._current_len > 1:
                self._current_len -= game.frame_time * Door.MOVE_RATE
                self._current_len = max(1.0, self._current_len)
                needs_update = True
        else:
            if self._current_len < self._gap_len / 2:
                self._current_len += game.frame_time * Door.MOVE_RATE
                self._current_len = min(self._gap_len / 2, self._current_len)
                needs_update = True

        if needs_update:
            current_len_int = int(self._current_len)
            if self._orientation == Door.Orientation.Horizontal:
                rect1 = pygame.rect.Rect(0, 0, current_len_int, self._thickness)
                rect2 = pygame.rect.Rect(self._gap_len - current_len_int, 0, current_len_int, self._thickness)
            else:
                rect1 = pygame.rect.Rect(0, 0, self._thickness, current_len_int)
                rect2 = pygame.rect.Rect(0, self._gap_len - current_len_int, self._thickness, current_len_int)
            self.image.fill(Door.COLORKEY)
            pygame.draw.rect(self.image, Door.COLOR, rect1)
            pygame.draw.rect(self.image, Door.COLOR, rect2)
