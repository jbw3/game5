from animation import Animation
from enum import Enum, unique
import pygame
import random
from typing import TYPE_CHECKING, override

from sprite import FlightCollisionSprite

if TYPE_CHECKING:
    from game import Game

class Asteroid(FlightCollisionSprite):
    @unique
    class Size(Enum):
        Small = 0
        Medium = 1
        Big = 2

    MAX_SPEED = 120

    def __init__(self, game: 'Game', size: 'Asteroid.Size', center: tuple[int, int]):
        small_images = [
            game.resource_loader.load_image(f'asteroid_small{i+1}.png')
            for i in range(1)
        ]
        medium_images = [
            game.resource_loader.load_image(f'asteroid_medium{i+1}.png')
            for i in range(2)
        ]
        big_images = [
            game.resource_loader.load_image(f'asteroid_big{i+1}.png')
            for i in range(2)
        ]

        self._size = size
        match size:
            case Asteroid.Size.Small:
                images = small_images
            case Asteroid.Size.Medium:
                images = medium_images
            case Asteroid.Size.Big:
                images = big_images
            case _:
                assert False, f'Unknown asteroid size: {size}'

        dx = 0.0
        dy = 0.0
        while dx == 0.0 and dy == 0.0:
            dx = float(random.randint(-Asteroid.MAX_SPEED, Asteroid.MAX_SPEED))
            dy = float(random.randint(-Asteroid.MAX_SPEED, Asteroid.MAX_SPEED))

        super().__init__(random.choice(images), float(center[0]), float(center[1]), dx, dy)
        self.rect.center = center
        self.mask = pygame.mask.from_surface(self.image)

        game.flight_view_sprites.add(self)
        game.flight_collision_sprites.add(self)

    @override
    def update(self, game: 'Game') -> None:
        self.x += self.dx * game.frame_time
        self.y += self.dy * game.frame_time

        self.rect.center = (int(self.x), int(self.y))

        # wrap around if the asteroid goes past the bounds of the view
        self.wrap(game.flight_view_size)

        # we're not using this, but we should clear it each update so it won't keep filling up
        self.collided_this_update.clear()

    @override
    def on_collide(self, game: 'Game', new_dx: float, new_dy: float, force: float) -> None:
        self.dx = new_dx
        self.dy = new_dy

        if ((self._size == Asteroid.Size.Small and force >= 125_000) or
            (self._size == Asteroid.Size.Medium and force >= 250_000) or
            (self._size == Asteroid.Size.Big and force >= 500_000)
            ):
            self.damage(game, 1)

    @override
    def damage(self, game: 'Game', hit_points: int) -> None:
        game.flight_view_sprites.remove(self)
        game.flight_collision_sprites.remove(self)

        if self._size == Asteroid.Size.Small:
            animation_images = [
                game.resource_loader.load_image(f'asteroid_debris{i+1}.png')
                for i in range(5)
            ]
            animation = Animation(animation_images, 20)
            animation.rect.center = self.rect.center
            game.flight_view_sprites.add(animation)

            game.update_asteroid_count(-1)
        else:
            if self._size == Asteroid.Size.Big:
                new_size = Asteroid.Size.Medium
            else:
                new_size = Asteroid.Size.Small

            Asteroid(game, new_size, self.rect.center)
            Asteroid(game, new_size, self.rect.center)

            game.update_asteroid_count(1)
