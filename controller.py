import pygame

class Controller:
    GAMEPAD_F310_GUID         = '0300bd846d0400001dc2000000007200'
    LOGITECH_DUAL_ACTION_GUID = '0300040e6d04000016c2000000000000'
    NINTENDO_SWITCH_PRO_GUID  = '030056fb7e0500000920000000006803'

    def __init__(self, joystick: pygame.joystick.JoystickType):
        self._joystick = joystick

        guid = self._joystick.get_guid()

        if guid == Controller.NINTENDO_SWITCH_PRO_GUID:
            self._trigger_button_num = 10
        else:
            self._trigger_button_num = 5

    def get_move_x_axis(self) -> float:
        return self._joystick.get_axis(0)

    def get_move_y_axis(self) -> float:
        return self._joystick.get_axis(1)

    def get_activate_button(self) -> bool:
        return self._joystick.get_button(0)

    def get_deactivate_button(self) -> bool:
        return self._joystick.get_button(1)

    def get_trigger_button(self) -> bool:
        return self._joystick.get_button(self._trigger_button_num)
