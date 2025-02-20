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
    collided_this_update: list[FlightCollisionSprite]
    def __init__(self, image: pygame.surface.Surface, x: float=0.0, y: float=0.0, dx: float=0.0, dy: float=0.0) -> None: ...
    def check_collision(self, game: 'Game') -> None: ...
    def on_collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None: ...
    def damage(self, game: 'Game', hit_points: int) -> None: ...
