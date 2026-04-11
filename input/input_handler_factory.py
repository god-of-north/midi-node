from enum import Enum, auto

from input.input_handler import InputHandler


class InputHandlerType(Enum):
    GPIO = auto()
    KEYBOARD = auto()
    ADS1115 = auto()

class InputHandlerFactory:
    @staticmethod
    def create_input_handler(handler_type: InputHandlerType, config) -> InputHandler:
        if handler_type == InputHandlerType.KEYBOARD:
            from input.keyboard_input_handler import KeyboardInputHandler
            return KeyboardInputHandler(config)
        elif handler_type == InputHandlerType.GPIO:
            from input.gpio_input_handler import GPIOInputHandler
            return GPIOInputHandler(config)
        elif handler_type == InputHandlerType.ADS1115:
            from input.ads1115_input_handler import ADS1115InputHandler
            return ADS1115InputHandler(config)