import pygame
from pygame.locals import JOYDEVICEADDED, JOYDEVICEREMOVED, KEYDOWN, KEYUP, QUIT

DEBUG_TEXT_COLOR = (180, 0, 150)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        self._fps_clock = pygame.time.Clock()
        self._tick_delta = 0.0

        self._display_surf = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self._display_surf.fill((0, 0, 0))

        self._debug = False
        self._can_change_debug = True
        self._debug_font = pygame.font.SysFont('Courier', 20)

        self._joysticks: list[pygame.joystick.JoystickType] = []

    def _display_debug(self) -> None:
        y = 0

        fps = self._fps_clock.get_fps()
        text_surface = self._debug_font.render(f'FPS: {fps:.1f}', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        tick_delta_ms = self._tick_delta * 1000
        text_surface = self._debug_font.render(f'Tick delta: {tick_delta_ms:.1f} ms', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        joystick_count = pygame.joystick.get_count()
        text_surface = self._debug_font.render(f'Joystick info ({joystick_count}):', False, DEBUG_TEXT_COLOR)
        self._display_surf.blit(text_surface, (0, y))
        y += text_surface.get_rect().bottom

        for i in range(joystick_count):
            # joystick_count = pygame.joystick.get_count()\
            joystick = pygame.joystick.Joystick(i)
            name = joystick.get_name()
            text_surface = self._debug_font.render(f' {i}: {name}', False, DEBUG_TEXT_COLOR)
            self._display_surf.blit(text_surface, (0, y))
            y += text_surface.get_rect().bottom

    def mainloop(self) -> None:
        quit_game = False
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit_game = True
                elif event.type == KEYDOWN:
                    if event.key == pygame.K_F1 and self._can_change_debug:
                        self._debug = not self._debug
                        self._can_change_debug = False
                elif event.type == KEYUP:
                    if event.key == pygame.K_F1:
                        self._can_change_debug = True
                elif event.type == JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    self._joysticks.append(joystick)
                elif event.type == JOYDEVICEREMOVED:
                    idx = event.instance_id
                    for joystick in self._joysticks:
                        if joystick.get_id() == idx:
                            self._joysticks.pop(idx)
                            break

            if quit_game:
                break

            self._display_surf.fill((0, 0, 0))

            if self._debug:
                self._display_debug()

            pygame.display.update()
            tick_delta_ms = self._fps_clock.tick(60.0)
            self._tick_delta = tick_delta_ms / 1000
