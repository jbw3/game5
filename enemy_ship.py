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
        game.flight_collision_sprites.add(self)

        self._hull = 3

    @override
    def update(self, game: 'Game') -> None:
        pass

    @override
    def collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        self._dx = new_dx
        self._dy = new_dy

        hit_points = int(force / 10_000)
        self._hull -= min(self._hull, hit_points)
        if self._hull <= 0:
            self.destroy()

    @override
    def damage(self, game: 'Game') -> None:
        self._hull -= 1
        if self._hull <= 0:
            self.destroy()

    def destroy(self) -> None:
        # remove from all sprite groups
        self.kill()
