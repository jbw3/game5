import pygame
from game import Game

class Sprite(pygame.sprite.DirtySprite, pygame.sprite._SpriteSupportsGroup, pygame.sprite._DirtySpriteSupportsGroup):
    image: pygame.surface.Surface
    rect: pygame.rect.Rect
    def __init__(self, image: pygame.surface.Surface) -> None: ...

class FlightCollisionSprite(Sprite):
    x: float
    y: float
    dx: float
    dy: float
    def __init__(self, image: pygame.surface.Surface, x: float, y: float, dx: float, dy: float) -> None: ...
    def collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None: ...
    def damage(self, game: 'Game') -> None: ...
