from enum import Enum, unique
import math
import pygame
from pygame.color import Color
from typing import TYPE_CHECKING, override

from animation import Animation
from controller import Controller
from sprite import Sprite
from status_bar import StatusBar

if TYPE_CHECKING:
    from game import Game

class Person(Animation):
    @unique
    class State(Enum):
        Moving = 0
        Console = 1

    IMAGE_NAME = 'person.png'
    COLORS = [
        Color(179, 0, 28), # red
        Color(0, 50, 205), # blue
        Color(0, 150, 20), # green
        Color(179, 103, 29), # orange
        Color(160, 50, 160), # purple
        Color(199, 68, 171), # pink
    ]
    MAX_SPEED = 70.0
    MAX_HEALTH = 5

    _image_cache: dict[tuple[str, int], pygame.surface.Surface] = {}

    @staticmethod
    def _color_image(image: pygame.surface.Surface, color: Color) -> pygame.surface.Surface:
        replace_color = Color(63, 72, 204)
        for x in range(image.get_width()):
            for y in range(image.get_height()):
                if image.get_at((x, y)) == replace_color:
                    image.set_at((x, y), color)

        return image

    @staticmethod
    def load_image(game: 'Game', name: str, color: Color) -> pygame.surface.Surface:
        color_key = (color.r << 16) | (color.g << 8) | color.b
        image = Person._image_cache.get((name, color_key))
        if image is None:
            base_image = game.resource_loader.load_image(name)
            image = Person._color_image(base_image.copy(), color)
            Person._image_cache[(name, color_key)] = image

        return image

    def __init__(self, game: 'Game', index: int, center: tuple[int, int], controller: Controller):
        color = Person.COLORS[index % len(Person.COLORS)]
        basic_image = Person.load_image(game, Person.IMAGE_NAME, color)
        self._basic_images = [basic_image]
        self._control_images = [
            Person.load_image(game, f'person_control{i+1}.png', color)
            for i in range(5)
        ]

        super().__init__(self._basic_images)
        self.rect.center = center
        self.dirty = 1

        self.x = float(center[0])
        self.y = float(center[1])

        game.interior_view_sprites.add(self)
        game.interior_solid_sprites.add(self)

        self._controller = controller
        self._state: Person.State = Person.State.Moving
        self._health = Person.MAX_HEALTH

        info_sprite = Sprite(basic_image)
        info_sprite.rect.topleft = (10, index * 30 + 10)
        game.info_overlay_sprites.add(info_sprite)

        self._health_bar = StatusBar(100, 20, color)
        self._health_bar.rect.left = info_sprite.rect.right + 10
        self._health_bar.rect.centery = info_sprite.rect.centery
        game.info_overlay_sprites.add(self._health_bar)

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

    def damage(self, game: 'Game', hit_points: int) -> None:
        self._health = max(0, self._health - hit_points)
        self._health_bar.set_status(self._health / Person.MAX_HEALTH)

        if self._health <= 0:
            self.die(game)

    def die(self, game: 'Game') -> None:
        # remove graphics
        self.kill()

        if self._state == Person.State.Console:
            game.ship.deactivate_console(self)

        game.on_player_death()

    def _state_moving(self, game: 'Game') -> None:
        last_rect = self.rect.copy()

        x_axis = self._controller.get_move_x_axis()
        y_axis = self._controller.get_move_y_axis()

        angle = math.atan2(y_axis, x_axis)
        magnitude = min(1.0, math.sqrt(x_axis**2 + y_axis**2))
        speed = Person.MAX_SPEED * magnitude * game.frame_time

        self.x += speed * math.cos(angle)
        self.y += speed * math.sin(angle)

        self.rect.center = (int(self.x), int(self.y))

        for sprite in pygame.sprite.spritecollide(self, game.interior_solid_sprites, False):
            if last_rect.top >= sprite.rect.bottom:
                self.rect.top = sprite.rect.bottom
                self.y = float(self.rect.centery)
            elif last_rect.bottom <= sprite.rect.top:
                self.rect.bottom = sprite.rect.top
                self.y = float(self.rect.centery)

            if last_rect.left >= sprite.rect.right:
                self.rect.left = sprite.rect.right
                self.x = float(self.rect.centerx)
            elif last_rect.right <= sprite.rect.left:
                self.rect.right = sprite.rect.left
                self.x = float(self.rect.centerx)

        if self._controller.get_activate_button():
            if game.ship.try_activate_console(self):
                self._state = Person.State.Console
                old_bottom = self.rect.bottom
                self.set_images(self._control_images, period=300, loop=True)
                self.rect.bottom = old_bottom
                self.x = float(self.rect.centerx)
                self.y = float(self.rect.centery)

        if last_rect.x != self.rect.x or last_rect.y != self.rect.y:
            self.dirty = 1

    def _state_console(self, game: 'Game') -> None:
        if self._controller.get_deactivate_button():
            game.ship.deactivate_console(self)
            self._state = Person.State.Moving
            old_bottom = self.rect.bottom
            self.set_images(self._basic_images)
            self.rect.bottom = old_bottom
