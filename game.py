import pygame
from pygame.locals import QUIT

class Game:
    def __init__(self):
        pygame.init()
        self._fps_clock = pygame.time.Clock()

        self._display_surf = pygame.display.set_mode((500, 400))
        self._display_surf.fill((0, 0, 0))

    def mainloop(self) -> None:
        quit_game = False
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
            if quit_game:
                break

            pygame.display.update()
            self._fps_clock.tick(60.0)
