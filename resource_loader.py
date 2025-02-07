import os
import pygame

class ResourceLoader:
    def __init__(self):
        self._cache: dict[str, pygame.surface.Surface] = {}

    def load_image(self, name: str) -> pygame.surface.Surface:
        image = self._cache.get(name)
        if image is None:
            filename = os.path.join('images', name)
            image = pygame.image.load(filename).convert_alpha()
            self._cache[name] = image

        return image
