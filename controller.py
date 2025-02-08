import pygame

class Controller:
    GAMEPAD_F310_GUID         = '0300bd846d0400001dc2000000007200'
    LOGITECH_DUAL_ACTION_GUID = '0300040e6d04000016c2000000000000'
    NINTENDO_SWITCH_PRO_GUID  = '030056fb7e0500000920000000006803'

    def __init__(self, joystick: pygame.joystick.JoystickType):
        self._joystick = joystick

        guid = self._joystick.get_guid()

        self._axis_threshold = 0.2
        if guid == Controller.NINTENDO_SWITCH_PRO_GUID:
            self._trigger_button_num = 10
            self._pause_buttons = [4, 6]
        elif guid == Controller.GAMEPAD_F310_GUID:
            self._trigger_button_num = 5
            self._pause_buttons = [6, 7]
        else:
            self._trigger_button_num = 5
            self._pause_buttons = [8, 9]

    def _get_adjusted_axis(self, value: float) -> float:
        abs_value = abs(value)
        if abs_value > self._axis_threshold:
            adjusted_value = (abs_value - self._axis_threshold) / (1.0 - self._axis_threshold)
            if value < 0.0:
                adjusted_value = -adjusted_value
        else:
            adjusted_value = 0.0

        return adjusted_value

    def get_move_x_axis(self) -> float:
        return self._get_adjusted_axis(self._joystick.get_axis(0))

    def get_move_y_axis(self) -> float:
        return self._get_adjusted_axis(self._joystick.get_axis(1))

    def get_activate_button(self) -> bool:
        return self._joystick.get_button(0)

    def get_deactivate_button(self) -> bool:
        return self._joystick.get_button(1)

    def get_trigger_button(self) -> bool:
        return self._joystick.get_button(self._trigger_button_num)

    def get_pause_button(self) -> bool:
        for button in self._pause_buttons:
            if self._joystick.get_button(button):
                return True
        return False
