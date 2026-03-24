import pygame
from typing import TYPE_CHECKING, override

from animation import Animation

if TYPE_CHECKING:
    from game import Game
    from sprite import Sprite

class Fire(Animation):
    PERSON_DAMAGE_THRESHOLD = 1.2

    def __init__(self, game: 'Game', topleft: tuple[int, int]):
        images = [
            game.resource_loader.load_image('fire1.png'),
            game.resource_loader.load_image('fire2.png'),
            game.resource_loader.load_image('fire3.png'),
            game.resource_loader.load_image('fire2.png'),
        ]

        super().__init__(images, period=200, loop=True)
        self.rect.topleft = topleft

        self._damage_timers: dict['Sprite', float] = {}

    @override
    def update(self, game: 'Game') -> None:
        super().update(game)

        for sprite in pygame.sprite.spritecollide(self, game.people_sprites, False):
            damage_timer = self._damage_timers.get(sprite, 0.0)
            damage_timer += game.frame_time
            damage = int(damage_timer / Fire.PERSON_DAMAGE_THRESHOLD)
            if damage > 0:
                sprite.damage(game, damage)

            self._damage_timers[sprite] = damage_timer % Fire.PERSON_DAMAGE_THRESHOLD
