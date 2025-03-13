import pygame
from pygame.color import Color
from pygame.rect import Rect

from sprite import Sprite

class StatusBar(Sprite):
    BACKGROUND_COLOR = Color(180, 180, 180)
    BORDER_COLOR = Color(120, 120, 180)
    BORDER_WIDTH = 2

    def __init__(self, width: int, height: int, color: Color):
        surface = pygame.surface.Surface((width, height))
        surface.fill(StatusBar.BACKGROUND_COLOR)
        border_rect = Rect((0, 0), (width, height))
        pygame.draw.rect(surface, StatusBar.BORDER_COLOR, border_rect, StatusBar.BORDER_WIDTH)

        super().__init__(surface)

        self._color = color
        self._status = 1.0
        self._draw_status()

    def _draw_status(self) -> None:
        offset = StatusBar.BORDER_WIDTH
        interior_width = self.image.get_width() - offset*2
        interior_height = self.image.get_height() - offset*2

        clear_rect = Rect((offset, offset), (interior_width, interior_height))
        pygame.draw.rect(self.image, StatusBar.BACKGROUND_COLOR, clear_rect)

        status_width = int(interior_width * self._status)
        status_rect = Rect((offset, offset), (status_width, interior_height))
        pygame.draw.rect(self.image, self._color, status_rect)

        self.dirty = 1

    def set_status(self, status: float) -> None:
        if status < 0.0:
            self._status = 0.0
        elif status > 1.0:
            self._status = 1.0
        else:
            self._status = status

        self._draw_status()
