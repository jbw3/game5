from enum import Enum, unique
import os
import pygame
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from game import Game

class Person(pygame.sprite.Sprite):
    @unique
    class State(Enum):
        Moving = 0
        Console = 1

    def __init__(self, game: 'Game', center: tuple[int, int], joystick: pygame.joystick.JoystickType):
        super().__init__()

        self.image = pygame.image.load(os.path.join('images', 'person.png'))
        self.rect = self.image.get_rect()
        self.rect.center = center

        game.interior_view_sprites.add(self)

        self._joystick = joystick
        self._state: Person.State = Person.State.Moving

    @property
    def joystick(self) -> pygame.joystick.JoystickType:
        return self._joystick

    @override
    def update(self, game: 'Game') -> None:
        match self._state:
            case Person.State.Moving:
                self._state_moving(game)
            case Person.State.Console:
                self._state_console(game)
            case _:
                assert False, f'Unknown state: {self._state}'

    def _state_moving(self, game: 'Game') -> None:
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

        for sprite in pygame.sprite.spritecollide(self, game.solid_sprites, False):
            if last_rect.top >= sprite.rect.bottom:
                self.rect.top = sprite.rect.bottom
            elif last_rect.bottom <= sprite.rect.top:
                self.rect.bottom = sprite.rect.top

            if last_rect.left >= sprite.rect.right:
                self.rect.left = sprite.rect.right
            elif last_rect.right <= sprite.rect.left:
                self.rect.right = sprite.rect.left

        if self._joystick.get_button(0):
            if game.ship.try_activate_console(self):
                self._state = Person.State.Console

    def _state_console(self, game: 'Game') -> None:
        if self._joystick.get_button(1):
            game.ship.deactivate_console(self)
            self._state = Person.State.Moving
