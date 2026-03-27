import logging
import pygame
import random
from typing import TYPE_CHECKING, override

from animation import Animation

if TYPE_CHECKING:
    from game import Game
    from sprite import Sprite

class Fire(Animation):
    @staticmethod
    def get_propagate_threshold() -> float:
        return 5.0 + (random.random() - 0.5) * 2.0

    def __init__(self, game: 'Game', topleft: tuple[int, int], floor: 'Sprite'):
        self._logger = logging.getLogger('Fire')

        images = [
            game.resource_loader.load_image('fire1.png'),
            game.resource_loader.load_image('fire2.png'),
            game.resource_loader.load_image('fire3.png'),
            game.resource_loader.load_image('fire2.png'),
        ]

        super().__init__(images, period=200, loop=True)
        self.rect.topleft = topleft

        self._floor = floor
        self._propagate_timer = Fire.get_propagate_threshold()

    @override
    def update(self, game: 'Game') -> None:
        super().update(game)

        for person in pygame.sprite.spritecollide(self, game.people_sprites, False):
            person.fire_damage(game, game.frame_time)

        self._propagate_timer -= game.frame_time
        while self._propagate_timer <= 0.0:
            self.propagate(game)
            self._propagate_timer += Fire.get_propagate_threshold()

    def propagate(self, game: 'Game') -> bool:
        length = self.rect.width

        surrounding_positions: list[tuple[int, int]] = [
            (self.rect.left + length * x, self.rect.top + length * y)
            for x in [-1, 0, 1]
            for y in [-1, 0, 1]
            if x != 0 or y != 0
        ]

        valid_fires: list[Fire] = []
        for pos in surrounding_positions:
            fire = Fire(game, pos, self._floor)
            if self._floor.rect.contains(fire.rect) and pygame.sprite.spritecollideany(fire, game.fires) is None:
                valid_fires.append(fire)

        if len(valid_fires) == 0:
            return False

        new_fire = random.choice(valid_fires)
        game.fires.add(new_fire)
        game.interior_view_sprites.add(new_fire)

        return True
