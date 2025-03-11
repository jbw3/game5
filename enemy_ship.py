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
from sprite import FlightCollisionSprite, Sprite

if TYPE_CHECKING:
    from game import Game

class MoveDetectionSprite(Sprite):
    MAX_LENGTH = 300

    def __init__(self, origin: tuple[int, int]):
        self._length = 0
        self._update_orig_image(MoveDetectionSprite.MAX_LENGTH // 2, 70)
        super().__init__(self._orig_image)

        self._origin = origin
        self.angle = 90.0

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_angle: float) -> None:
        self._angle = new_angle % 360.0
        self._rotate()

    @property
    def origin(self) -> tuple[int, int]:
        return self._origin

    @origin.setter
    def origin(self, new_origin: tuple[int, int]) -> None:
        self._origin = new_origin
        self._update_position()

    def _rotate(self) -> None:
        self.image = pygame.transform.rotate(self._orig_image, self.angle)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self._update_position()

    def _update_orig_image(self, length: int, height2: int) -> None:
        height1 = 40
        image = pygame.surface.Surface((length, height2))
        image.fill((0, 0, 0))
        image.set_colorkey((0, 0, 0))
        image.set_alpha(130)
        y1 = (height2 - height1) // 2
        points = [
            (0, y1),
            (length - 1, 0),
            (length - 1, height2 - 1),
            (0, y1 + height1),
        ]
        pygame.draw.polygon(image, (0, 50, 255), points)

        self._orig_image = image
        self._length = length

    def _update_position(self) -> None:
        offset = self._length / 2
        x = self.origin[0] + offset * math.cos(math.radians(self.angle))
        y = self.origin[1] + offset * -math.sin(math.radians(self.angle))
        self.rect.center = (int(x), int(y))

    def update_vel_proportion(self, proportion: float) -> None:
        if proportion < 0.5:
            length = MoveDetectionSprite.MAX_LENGTH // 2
            height2 = 70
        else:
            length = MoveDetectionSprite.MAX_LENGTH
            height2 = 100

        if self._length != length:
            self._update_orig_image(length, height2)
            self._rotate()

@dataclass
class EnemyShipConfig:
    hold_position_delay: float # seconds
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
        AvoidingCollision = 2

    def __init__(self, game: 'Game', x: float, y: float, config: EnemyShipConfig):
        self._logger = logging.getLogger('EnemyShip')
        image = game.resource_loader.load_image('enemy_ship1.png')
        super().__init__(image, x, y, 0.0, 0.0)
        self.rect.center = (int(x), int(y))
        self.mask = pygame.mask.from_surface(self.image)

        game.flight_view_sprites.add(self)
        game.flight_collision_sprites.add(self)

        self._move_detection_sprite = MoveDetectionSprite(self.rect.center)
        self._aim_sprite = AimSprite((240, 0, 0), self.rect.center)
        if game.debug:
            game.flight_view_sprites.add(self._move_detection_sprite)
            game.flight_view_sprites.add(self._aim_sprite)

        self._hull = 3
        self._target_vel = Vector2(0.0, 0.0)

        self._hold_position_timer = 0.0
        self._hold_position_delay = config.hold_position_delay
        self._move_state = EnemyShip.MoveState.MovingToTarget
        self._move_target = Vector2(self.x, self.y)
        self._update_move_target(game)

        self._aim_angle = 90.0
        self._target_angle = self._aim_angle
        self._max_aiming_iterations = config.max_aiming_iterations
        self._initial_fire_timer = config.initial_fire_delay
        self._laser_fire_timer = 0.0
        self._laser_delay = config.laser_delay

    @override
    def update(self, game: 'Game') -> None:
        self._hold_position_timer = max(0.0, self._hold_position_timer - game.frame_time)
        self._initial_fire_timer = max(0.0, self._initial_fire_timer - game.frame_time)
        self._laser_fire_timer = max(0.0, self._laser_fire_timer - game.frame_time)

        self._update_engine(game)
        self._update_weapon(game)

        self.check_collision(game)

    def _update_move_target(self, game: 'Game') -> None:
        view_width, view_height = game.flight_view_size

        old_move_target = self._move_target.copy()

        # pick a new move target that is not too close to the current one
        while self._move_target.distance_to(old_move_target) <= 150.0:
            x = random.randint(-40, 40)
            y = random.randint(-50, 50)

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
        self_vel_mag = self_vel.magnitude()
        target_distance = self_pos.distance_to(self._move_target)
        self._logger.debug(f'move target distance: {target_distance}')
        max_target_vel = 300.0

        if self_vel_mag > 0.1:
            self._move_detection_sprite.angle = math.degrees(math.atan2(-self.dy, self.dx))

        move_collision = False
        collide_sprites = pygame.sprite.spritecollide(self._move_detection_sprite, game.flight_collision_sprites, False, pygame.sprite.collide_mask)
        for sprite in collide_sprites:
            if sprite is not self:
                move_collision = True
                break

        match self._move_state:
            case EnemyShip.MoveState.MovingToTarget:
                if target_distance < 10.0 and self_vel_mag < 0.5:
                    self._hold_position_timer = self._hold_position_delay
                    self._move_state = EnemyShip.MoveState.HoldingAtTarget
                else:
                    target_vel_unit = (self._move_target - self_pos).normalize()

                    if move_collision and self_vel_mag > 0.1:
                        self._target_vel = Vector2(0.0, 0.0)
                        self._move_state = EnemyShip.MoveState.AvoidingCollision
                    elif target_distance < 10.0:
                        self._target_vel = Vector2(0.0, 0.0)
                    elif target_distance < 150.0:
                        self._target_vel = (target_distance / 150.0) * max_target_vel * target_vel_unit
                    else:
                        self._target_vel = max_target_vel * target_vel_unit

            case EnemyShip.MoveState.HoldingAtTarget:
                self._target_vel = Vector2(0.0, 0.0)
                if target_distance >= 10.0:
                    self._move_state = EnemyShip.MoveState.MovingToTarget
                elif self._hold_position_timer <= 0.0:
                    self._update_move_target(game)
                    self._move_state = EnemyShip.MoveState.MovingToTarget

            case EnemyShip.MoveState.AvoidingCollision:
                self._target_vel = Vector2(0.0, 0.0)
                if not move_collision:
                    self._move_state = EnemyShip.MoveState.MovingToTarget
                elif self_vel_mag < 0.1:
                    # pick a new move target
                    self._update_move_target(game)
                    self._move_state = EnemyShip.MoveState.MovingToTarget

            case _:
                assert False, f'Unknown move state: {self._move_state}'

        accel = self._target_vel - self_vel
        if accel.magnitude() > EnemyShip.MAX_ACCELERATION:
            accel = accel.normalize() * EnemyShip.MAX_ACCELERATION

        self.dx += accel.x
        self.dy += accel.y

        self.x += self.dx * game.frame_time
        self.y += self.dy * game.frame_time
        self.rect.center = (int(self.x), int(self.y))
        self._aim_sprite.origin = self.rect.center
        self._move_detection_sprite.origin = self.rect.center
        self._move_detection_sprite.update_vel_proportion(Vector2(self.dx, self.dy).magnitude() / max_target_vel)

    def _update_weapon(self, game: 'Game') -> None:
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
    def on_collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        self.dx = new_dx
        self.dy = new_dy

        hit_points = int(force / 20_000)
        self.damage(game, hit_points)

    @override
    def damage(self, game: 'Game', hit_points: int) -> None:
        self._hull = max(0, self._hull - hit_points)
        if self._hull <= 0:
            self.destroy(game)

    def destroy(self, game: 'Game') -> None:
        # remove from all sprite groups
        self.kill()
        self._aim_sprite.kill()
        self._move_detection_sprite.kill()

        # create explosion graphic
        ShipExplosionAnimation(game, self.rect.center)

        game.update_enemy_count(-1)
