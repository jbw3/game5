from enum import Enum, unique
import math
import pygame
from typing import TYPE_CHECKING, override

from animation import Animation
from controller import Controller

if TYPE_CHECKING:
    from game import Game

class Person(Animation):
    @unique
    class State(Enum):
        Moving = 0
        Console = 1

    IMAGE_NAME = 'person.png'
    MAX_SPEED = 70.0

    def __init__(self, game: 'Game', center: tuple[int, int], controller: Controller):
        self._basic_images = [game.resource_loader.load_image(Person.IMAGE_NAME)]
        self._control_images = [
            game.resource_loader.load_image(f'person_control{i+1}.png')
            for i in range(5)
        ]

        super().__init__(self._basic_images)
        self.rect.center = center
        self.dirty = 1

        self._x = float(center[0])
        self._y = float(center[1])

        game.interior_view_sprites.add(self)

        self._controller = controller
        self._state: Person.State = Person.State.Moving

    @property
    def controller(self) -> Controller:
        return self._controller

    @override
    def update(self, game: 'Game') -> None:
        super().update(game)

        match self._state:
            case Person.State.Moving:
                self._state_moving(game)
            case Person.State.Console:
                self._state_console(game)
            case _:
                assert False, f'Unknown state: {self._state}'

    def _state_moving(self, game: 'Game') -> None:
        last_rect = self.rect.copy()

        x_axis = self._controller.get_move_x_axis()
        y_axis = self._controller.get_move_y_axis()

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

        if self._controller.get_activate_button():
            if game.ship.try_activate_console(self):
                self._state = Person.State.Console
                old_bottom = self.rect.bottom
                self.set_images(self._control_images, period=300, loop=True)
                self.rect.bottom = old_bottom
                self._x = float(self.rect.centerx)
                self._y = float(self.rect.centery)

        if last_rect.x != self.rect.x or last_rect.y != self.rect.y:
            self.dirty = 1

    def _state_console(self, game: 'Game') -> None:
        if self._controller.get_deactivate_button():
            game.ship.deactivate_console(self)
            self._state = Person.State.Moving
            old_bottom = self.rect.bottom
            self.set_images(self._basic_images)
            self.rect.bottom = old_bottom
