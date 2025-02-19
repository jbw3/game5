from dataclasses import dataclass
from enum import Enum, unique
import logging
import math
import pygame
from pygame.math import Vector2
import random
from typing import TYPE_CHECKING, override

from aim_sprite import AimSprite
from animation import ShipExplosionAnimation
from laser import Laser
from sprite import FlightCollisionSprite

if TYPE_CHECKING:
    from game import Game

@dataclass
class EnemyShipConfig:
    initial_fire_delay: float # seconds
    laser_delay: float # seconds
    max_aiming_iterations: int

class EnemyShip(FlightCollisionSprite):
    MAX_ACCELERATION = 5.0
    AIM_ANGLE_RATE = 120.0 # degrees

    @unique
    class MoveState(Enum):
        MovingToTarget = 0
        HoldingAtTarget = 1

    def __init__(self, game: 'Game', x: float, y: float, config: EnemyShipConfig):
        self._logger = logging.getLogger('EnemyShip')
        image = game.resource_loader.load_image('enemy_ship1.png')
        super().__init__(image, x, y, 0.0, 0.0)
        self._x = float(x)
        self._y = float(y)
        self.rect.center = (int(x), int(y))
        self.mask = pygame.mask.from_surface(self.image)

        game.flight_view_sprites.add(self)
        game.flight_collision_sprites.add(self)

        self._aim_sprite = AimSprite((240, 0, 0), self.rect.center)
        if game.debug:
            game.flight_view_sprites.add(self._aim_sprite)

        self._hull = 3

        self._move_state = EnemyShip.MoveState.MovingToTarget
        self._move_target = Vector2(self._x, self._y)
        self._update_move_target(game)

        self._aim_angle = 90.0
        self._target_angle = self._aim_angle
        self._max_aiming_iterations = config.max_aiming_iterations
        self._initial_fire_timer = config.initial_fire_delay
        self._laser_fire_timer = 0.0
        self._laser_delay = config.laser_delay

    @override
    def update(self, game: 'Game') -> None:
        self._update_engine(game)
        self._update_weapon(game)

    def _update_move_target(self, game: 'Game') -> None:
        view_width, view_height = game.flight_view_size

        old_move_target = self._move_target.copy()

        # pick a new move target that is not too close to the current one
        while self._move_target.distance_to(old_move_target) <= 100.0:
            x = random.randint(-20, 20)
            y = random.randint(-30, 30)

            match random.randint(0, 3):
                case 0:
                    x += view_width // 6
                    y += view_height // 6
                case 1:
                    x += view_width * 5 // 6
                    y += view_height // 6
                case 2:
                    x += view_width // 6
                    y += view_height * 5 // 6
                case 3:
                    x += view_width * 5 // 6
                    y += view_height * 5 // 6

            self._move_target.x = x
            self._move_target.y = y

    def _update_engine(self, game: 'Game') -> None:
        self_pos = Vector2(self.x, self.y)
        self_vel = Vector2(self.dx, self.dy)
        target_distance = self_pos.distance_to(self._move_target)
        self._logger.debug(f'move target distance: {target_distance}')

        match self._move_state:
            case EnemyShip.MoveState.MovingToTarget:
                if target_distance < 10.0 and self_vel.magnitude() < 0.5:
                    self._move_state = EnemyShip.MoveState.HoldingAtTarget
                else:
                    max_target_vel = 300.0
                    target_vel_unit = (self._move_target - self_pos).normalize()
                    target_vel: Vector2
                    if target_distance < 10.0:
                        target_vel = Vector2(0.0, 0.0)
                    elif target_distance < 150.0:
                        target_vel = (target_distance / 150.0) * max_target_vel * target_vel_unit
                    else:
                        target_vel = max_target_vel * target_vel_unit

                    accel = target_vel - self_vel
                    if accel.magnitude() > EnemyShip.MAX_ACCELERATION:
                        accel = accel.normalize() * EnemyShip.MAX_ACCELERATION

                    self._dx += accel.x
                    self._dy += accel.y

            case EnemyShip.MoveState.HoldingAtTarget:
                if target_distance >= 10.0:
                    self._move_state = EnemyShip.MoveState.MovingToTarget
                else:
                    self._update_move_target(game)
                    self._move_state = EnemyShip.MoveState.MovingToTarget

            case _:
                assert False, f'Unknown move state: {self._move_state}'

        self._x += self._dx * game.frame_time
        self._y += self._dy * game.frame_time
        self.rect.center = (int(self._x), int(self._y))
        self._aim_sprite.origin = self.rect.center

    def _update_weapon(self, game: 'Game') -> None:
        self._initial_fire_timer = max(0.0, self._initial_fire_timer - game.frame_time)
        if game.ship is None or self._initial_fire_timer > 0.0:
            return

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
        while i < self._max_aiming_iterations and target_pos.distance_to(old_target_pos) > 10.0:
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

        # create explosion graphic
        ShipExplosionAnimation(game, self.rect.center)

        game.update_enemy_count(-1)
