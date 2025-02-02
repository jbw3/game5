from enum import Enum, unique
import math
import pygame
from typing import TYPE_CHECKING, override

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game

class Person(Sprite):
    @unique
    class State(Enum):
        Moving = 0
        Console = 1

    IMAGE_NAME = 'person.png'
    MAX_SPEED = 70.0

    def __init__(self, game: 'Game', center: tuple[int, int], joystick: pygame.joystick.JoystickType):
        super().__init__(game.image_loader.load(Person.IMAGE_NAME))
        self.rect.center = center
        self.dirty = 1

        self._x = float(center[0])
        self._y = float(center[1])

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
        if abs(a0) > 0.2:
            x_axis = a0
        else:
            x_axis = 0.0

        a1 = self._joystick.get_axis(1)
        if abs(a1) > 0.2:
            y_axis = a1
        else:
            y_axis = 0.0

        angle = math.atan2(y_axis, x_axis)
        magnitude = min(1.0, math.sqrt(x_axis**2 + y_axis**2))
        speed = Person.MAX_SPEED * magnitude * game.frame_time

        self._x += speed * math.cos(angle)
        self._y += speed * math.sin(angle)

        self.rect.center = (int(self._x), int(self._y))

        for sprite in pygame.sprite.spritecollide(self, game.interior_solid_sprites, False):
            if last_rect.top >= sprite.rect.bottom:
                self.rect.top = sprite.rect.bottom
                self._y = float(self.rect.centery)
            elif last_rect.bottom <= sprite.rect.top:
                self.rect.bottom = sprite.rect.top
                self._y = float(self.rect.centery)

            if last_rect.left >= sprite.rect.right:
                self.rect.left = sprite.rect.right
                self._x = float(self.rect.centerx)
            elif last_rect.right <= sprite.rect.left:
                self.rect.right = sprite.rect.left
                self._x = float(self.rect.centerx)

        if self._joystick.get_button(0):
            if game.ship.try_activate_console(self):
                self._state = Person.State.Console
                self._x = float(self.rect.centerx)
                self._y = float(self.rect.centery)

        if last_rect.x != self.rect.x or last_rect.y != self.rect.y:
            self.dirty = 1

    def _state_console(self, game: 'Game') -> None:
        if self._joystick.get_button(1):
            game.ship.deactivate_console(self)
            self._state = Person.State.Moving
