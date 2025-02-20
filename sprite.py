import math
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game

class Sprite(pygame.sprite.DirtySprite):
    def __init__(self, image: pygame.surface.Surface):
        super().__init__()
        self._image = image
        self.rect = self._image.get_rect()

    @property
    def image(self) -> pygame.surface.Surface:
        return self._image

    @image.setter
    def image(self, value: pygame.surface.Surface) -> None:
        old_topleft = self.rect.topleft
        self._image = value
        self.rect = self._image.get_rect()
        self.rect.topleft = old_topleft

class FlightCollisionSprite(Sprite):
    def __init__(self, image: pygame.surface.Surface, x: float=0.0, y: float=0.0, dx: float=0.0, dy: float=0.0):
        super().__init__(image)
        self._x = x
        self._y = y
        self._dx = dx
        self._dy = dy
        self.collided_this_update: list[FlightCollisionSprite] = []

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def dx(self) -> float:
        return self._dx

    @property
    def dy(self) -> float:
        return self._dy

    def check_collision(self, game: 'Game') -> None:
        for sprite in pygame.sprite.spritecollide(self, game.flight_collision_sprites, False): # type: ignore
            # don't collide with ourselves
            if sprite is self:
                continue

            # don't collide with sprites that have collided with us this update
            if any(sprite is s for s in self.collided_this_update):
                continue

            # elastic collision equations

            # use sprite area as "mass"
            my_mass = self.rect.width * self.rect.height
            other_mass = sprite.rect.width * sprite.rect.height
            mass_sum = my_mass + other_mass

            # rotate velocities so collision can be calculated for x component
            angle = math.atan2(sprite.y - self._y, sprite.x - self._x)
            sin_angle = math.sin(angle)
            cos_angle = math.cos(angle)
            my_vx = self._dx * cos_angle - self._dy * sin_angle
            my_vy = self._dx * sin_angle + self._dy * cos_angle
            other_vx = sprite.dx * cos_angle - sprite.dy * sin_angle
            other_vy = sprite.dx * sin_angle + sprite.dy * cos_angle

            # calculate new x components
            my_new_vx = (my_mass - other_mass) / mass_sum * my_vx + 2 * other_mass / mass_sum * other_vx
            other_new_vx = 2 * my_mass / mass_sum * my_vx + (other_mass - my_mass) / mass_sum * other_vx

            # rotate the velocity components back
            sin_negative_angle = math.sin(-angle)
            cos_negative_angle = math.cos(-angle)
            self._dx = my_new_vx * cos_negative_angle - my_vy * sin_negative_angle
            self._dy = my_new_vx * sin_negative_angle + my_vy * cos_negative_angle
            other_dx = other_new_vx * cos_negative_angle - other_vy * sin_negative_angle
            other_dy = other_new_vx * sin_negative_angle + other_vy * cos_negative_angle

            force = my_mass * abs(my_new_vx - my_vx)

            sprite.on_collide(game, other_dx, other_dy, force)
            self.on_collide(game, self._dx, self._dy, force)
            sprite.collided_this_update.append(self) # type: ignore

            my_x = self.rect.x
            my_y = self.rect.y
            other_x = sprite.rect.x
            other_y = sprite.rect.y
            if abs(other_x - my_x) < abs(other_y - my_y):
                if my_y < other_y:
                    self.rect.bottom = sprite.rect.top
                else:
                    self.rect.top = sprite.rect.bottom
                self._y = float(self.rect.centery)
            else:
                if my_x < other_x:
                    self.rect.right = sprite.rect.left
                else:
                    self.rect.left = sprite.rect.right
                self._x = float(self.rect.centerx)

        self.collided_this_update.clear()

    def on_collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        pass

    def damage(self, game: 'Game', hit_points: int) -> None:
        pass
