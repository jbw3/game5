import pygame
from typing import TYPE_CHECKING, override

from sprite import FlightCollisionSprite

if TYPE_CHECKING:
    from game import Game

class EnemyShip(FlightCollisionSprite):
    def __init__(self, game: 'Game', x: float, y: float):
        image = game.resource_loader.load_image('enemy_ship1.png')
        super().__init__(image, x, y, 0.0, 0.0)
        self.rect.center = (int(x), int(y))
        self.mask = pygame.mask.from_surface(self.image)

        game.flight_view_sprites.add(self)

    @override
    def update(self, game: 'Game') -> None:
        pass
