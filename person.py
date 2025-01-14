import os
import pygame
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from game import Game

class Person(pygame.sprite.Sprite):
    def __init__(self, game: 'Game', center: tuple[int, int], joystick: pygame.joystick.JoystickType):
        super().__init__()

        self.image = pygame.image.load(os.path.join('images', 'person.png'))
        self.rect = self.image.get_rect()
        self.rect.center = center

        game.sprites.add(self)

        self._joystick = joystick

    @override
    def update(self, game: 'Game') -> None:
        last_rect = self.rect.copy()

        a0 = self._joystick.get_axis(0)
        if a0 < -0.2:
            self.rect.move_ip(-1.0, 0.0)
        elif a0 > 0.2:
            self.rect.move_ip(1.0, 0.0)

        a1 = self._joystick.get_axis(1)
        if a1 < -0.2:
            self.rect.move_ip(0.0, -1.0)
        elif a1 > 0.2:
            self.rect.move_ip(0.0, 1.0)

        for sprite in pygame.sprite.spritecollide(self, game.solid, False):
            if last_rect.top >= sprite.rect.bottom:
                self.rect.top = sprite.rect.bottom
            elif last_rect.bottom <= sprite.rect.top:
                self.rect.bottom = sprite.rect.top

            if last_rect.left >= sprite.rect.right:
                self.rect.left = sprite.rect.right
            elif last_rect.right <= sprite.rect.left:
                self.rect.right = sprite.rect.left
