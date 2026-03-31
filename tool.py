from enum import Enum, unique
from typing import TYPE_CHECKING

from sprite import Sprite

if TYPE_CHECKING:
    from game import Game
    from person import Person

@unique
class ToolType(Enum):
    FireExtinguisher = 0

class Tool(Sprite):
    def __init__(
        self,
        game: 'Game',
        tool_type: ToolType,
        left: int|None=None,
        right: int|None=None,
        top: int|None=None,
        bottom: int|None=None,
    ) -> None:
        self._tool_type = tool_type

        match self._tool_type:
            case ToolType.FireExtinguisher:
                image_name = 'fire_extinguisher.png'
            case _:
                raise ValueError(f'Unknown tool type {self._tool_type}')

        image = game.resource_loader.load_image(image_name)
        super().__init__(image)

        if left is not None:
            self.rect.left = left
        elif right is not None:
            self.rect.right = right

        if top is not None:
            self.rect.top = top
        elif bottom is not None:
            self.rect.bottom = bottom

        self._person: Person|None = None

    @property
    def tool_type(self) -> ToolType:
        return self._tool_type

    @property
    def person(self) -> Person|None:
        return self._person

    def pick_up(self, game: 'Game', person: 'Person') -> None:
        game.interior_view_sprites.remove(self)
        game.interior_solid_sprites.remove(self)
        self._person = person

    def put_down(self, game: 'Game', left: int, bottom: int) -> None:
        self.rect.left = left
        self.rect.bottom = bottom
        game.interior_view_sprites.add(self)
        game.interior_solid_sprites.add(self)
        self._person = None
