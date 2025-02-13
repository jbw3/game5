import math
import pygame
from typing import TYPE_CHECKING, override

from aim_sprite import AimSprite
from sprite import FlightCollisionSprite

if TYPE_CHECKING:
    from game import Game

class EnemyShip(FlightCollisionSprite):
    AIM_ANGLE_RATE = 120.0 # degrees

    def __init__(self, game: 'Game', x: float, y: float):
        image = game.resource_loader.load_image('enemy_ship1.png')
        super().__init__(image, x, y, 0.0, 0.0)
        self.rect.center = (int(x), int(y))
        self.mask = pygame.mask.from_surface(self.image)

        game.flight_view_sprites.add(self)
        game.flight_collision_sprites.add(self)

        self._aim_sprite = AimSprite((240, 0, 0), self.rect.center)
        if game.debug:
            game.flight_view_sprites.add(self._aim_sprite)

        self._hull = 3
        self._aim_angle = 90.0
        self._target_angle = self._aim_angle

    @override
    def update(self, game: 'Game') -> None:
        if game.ship is not None:
            x_diff = game.ship.x - self.x
            y_diff = game.ship.y - self.y
            self._target_angle = math.degrees(math.atan2(-y_diff, x_diff)) % 360.0

        max_angle_move = EnemyShip.AIM_ANGLE_RATE * game.frame_time
        angle_diff = (self._target_angle - self._aim_angle) % 360.0
        if angle_diff <= max_angle_move:
            self._aim_angle = self._target_angle
        elif angle_diff <= 180.0:
            self._aim_angle += max_angle_move
        else:
            self._aim_angle -= max_angle_move
        self._aim_angle %= 360.0

        if game.debug:
            self._aim_sprite.angle = self._aim_angle
            self._aim_sprite.origin = self.rect.center

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
        self._aim_sprite.kill()
