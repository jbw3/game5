import math
import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Laser(Sprite):
    RED_IMAGE_NAME = 'laser_red.png'

    SPEED = 1000

    def __init__(self, game: 'Game', center: tuple[int, int], angle: float, parent: Sprite):
        super().__init__(pygame.transform.rotate(game.resource_loader.load_image(Laser.RED_IMAGE_NAME), angle))
        self.rect.center = center
        self.mask = pygame.mask.from_surface(self.image)
        self._parent = parent

        game.flight_view_sprites.add(self)

        self.x = float(center[0])
        self.y = float(center[1])

        self.dx = Laser.SPEED * math.cos(math.radians(angle))
        self.dy = Laser.SPEED * math.sin(math.radians(-angle))

        sound = game.resource_loader.load_sound('laser.wav')
        sound.play()

    @override
    def update(self, game: 'Game') -> None:
        self.x += self.dx * game.frame_time
        self.y += self.dy * game.frame_time

        self.rect.center = (int(self.x), int(self.y))

        # remove laser when it goes beyond the bounds of the view
        view_width, view_height = game.flight_view_size
        if self.x < 0.0 or self.x >= view_width or self.y < 0.0 or self.y >= view_height:
            game.flight_view_sprites.remove(self)

        collide_sprites = pygame.sprite.spritecollide(self, game.flight_collision_sprites, False, pygame.sprite.collide_mask)
        for sprite in collide_sprites:
            if sprite is not self._parent:
                sprite.damage(game, 1)
                self.kill()
                break
