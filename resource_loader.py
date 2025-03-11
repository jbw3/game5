import os
import pygame

class ResourceLoader:
    def __init__(self):
        self._image_cache: dict[str, pygame.surface.Surface] = {}
        self._sound_cache: dict[str, pygame.mixer.Sound] = {}

    def load_image(self, name: str) -> pygame.surface.Surface:
        image = self._image_cache.get(name)
        if image is None:
            filename = os.path.join('images', name)
            image = pygame.image.load(filename).convert_alpha()
            self._image_cache[name] = image

        return image

    def load_sound(self, name: str) -> pygame.mixer.Sound:
        sound = self._sound_cache.get(name)
        if sound is None:
            filename = os.path.join('audio', name)
            sound = pygame.mixer.Sound(filename)
            self._sound_cache[name] = sound

        return sound
