from typing import TYPE_CHECKING

from animation import Animation

if TYPE_CHECKING:
    from game import Game

class Fire(Animation):
    def __init__(self, game: 'Game', topleft: tuple[int, int]):
        images = [
            game.resource_loader.load_image('fire1.png'),
            game.resource_loader.load_image('fire2.png'),
            game.resource_loader.load_image('fire3.png'),
            game.resource_loader.load_image('fire2.png'),
        ]

        super().__init__(images, period=200, loop=True)
        self.rect.topleft = topleft
