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

    def __init__(self, game: 'Game', orientation: Orientation, gap_len: int, thickness: int):
        self._orientation = orientation
        self._gap_len = gap_len
        self._current_len = self._gap_len // 2
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

        self._last_update = pygame.time.get_ticks()

    @override
    def update(self, game: 'Game') -> None:
        if pygame.time.get_ticks() >= self._last_update + 10:
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
                    self._current_len -= 1
                    needs_update = True
            else:
                if self._current_len < self._gap_len // 2:
                    self._current_len += 1
                    needs_update = True

            if needs_update:
                if self._orientation == Door.Orientation.Horizontal:
                    rect1 = pygame.rect.Rect(0, 0, self._current_len, self._thickness)
                    rect2 = pygame.rect.Rect(self._gap_len - self._current_len, 0, self._current_len, self._thickness)
                else:
                    rect1 = pygame.rect.Rect(0, 0, self._thickness, self._current_len)
                    rect2 = pygame.rect.Rect(0, self._gap_len - self._current_len, self._thickness, self._current_len)
                self.image.fill(Door.COLORKEY)
                pygame.draw.rect(self.image, Door.COLOR, rect1)
                pygame.draw.rect(self.image, Door.COLOR, rect2)

            self._last_update = pygame.time.get_ticks()
