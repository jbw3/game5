import pygame

class Stopwatch:
    def __init__(self, queue_size: int):
        self._times = [0] * queue_size
        self._start = 0

    @property
    def times(self) -> list[int]:
        return self._times

    def start(self) -> None:
        self._start = pygame.time.get_ticks()

    def stop(self) -> None:
        time = pygame.time.get_ticks() - self._start
        self._times.append(time)
        self._times.pop(0)
