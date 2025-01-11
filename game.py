import pygame
from pygame.locals import QUIT

DEBUG_TEXT_COLOR = (180, 0, 150)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self._fps_clock = pygame.time.Clock()
        self._tick_delta = 0.0

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self._display_surf.fill((0, 0, 0))

        self._debug_font = pygame.font.SysFont('Courier', 20)

    def _display_debug(self) -> None:
        fps = self._fps_clock.get_fps()
        fps_surface = self._debug_font.render(f'FPS: {fps:.1f}', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(fps_surface, (0, 0))

        tick_delta_ms = self._tick_delta * 1000
        tick_delta_surface = self._debug_font.render(f'Tick delta: {tick_delta_ms:.1f} ms', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(tick_delta_surface, (0, fps_surface.get_rect().bottom))

    def mainloop(self) -> None:
        quit_game = False
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
            if quit_game:
                break

            self._display_surf.fill((0, 0, 0))
            self._display_debug()

            pygame.display.update()
            tick_delta_ms = self._fps_clock.tick(60.0)
            self._tick_delta = tick_delta_ms / 1000
