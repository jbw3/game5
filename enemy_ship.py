import logging
import math
import pygame
from pygame.math import Vector2
from typing import TYPE_CHECKING, override

from aim_sprite import AimSprite
from laser import Laser
from sprite import FlightCollisionSprite

if TYPE_CHECKING:
    from game import Game

class EnemyShip(FlightCollisionSprite):
    AIM_ANGLE_RATE = 120.0 # degrees

    def __init__(self, game: 'Game', x: float, y: float):
        self._logger = logging.getLogger('EnemyShip')
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

        self._laser_fire_timer = 0.0
        self._laser_delay = 2.0 # seconds

    @override
    def update(self, game: 'Game') -> None:
        if game.ship is not None:
            # calculate aim angle

            self._target_angle = self._calc_target_angle(game.ship)

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

            # fire

            self._laser_fire_timer = max(0.0, self._laser_fire_timer - game.frame_time)
            angle_diff = (self._target_angle - self._aim_angle) % 360.0
            if angle_diff < 0.5:
                self.fire_laser(game)

    def _calc_target_angle(self, target: FlightCollisionSprite) -> float:
        self_pos = Vector2(self.x, self.y)
        target_pos = Vector2(target.x, target.y)
        old_target_pos = Vector2(1_000_000.0, 1_000_000.0)

        i = 0
        while i < 10 and target_pos.distance_to(old_target_pos) > 10.0:
            old_target_pos = target_pos.copy()
            distance = self_pos.distance_to(target_pos)
            laser_travel_time = distance / Laser.SPEED
            target_pos.x = target.x + target.dx * laser_travel_time
            target_pos.y = target.y + target.dy * laser_travel_time
            i += 1

        x_diff = target_pos.x - self.x
        y_diff = target_pos.y - self.y
        target_angle = math.degrees(math.atan2(-y_diff, x_diff)) % 360.0

        self._logger.debug(f'Calculated target angle {target_angle:.1f} in {i} iterations')

        return target_angle

    def fire_laser(self, game: 'Game') -> None:
        if self._laser_fire_timer <= 0.0:
            Laser(game, self.rect.center, self._aim_angle, self)
            self._laser_fire_timer = self._laser_delay

    @override
    def collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        self._dx = new_dx
        self._dy = new_dy

        hit_points = int(force / 20_000)
        self._hull -= min(self._hull, hit_points)
        if self._hull <= 0:
            self.destroy(game)

    @override
    def damage(self, game: 'Game', hit_points: int) -> None:
        self._hull -= hit_points
        if self._hull <= 0:
            self.destroy(game)

    def destroy(self, game: 'Game') -> None:
        # remove from all sprite groups
        self.kill()
        self._aim_sprite.kill()

        game.update_enemy_count(-1)
