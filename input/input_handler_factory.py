from enum import Enum, auto

from input.input_handler import InputHandler


class InputHandlerType(Enum):
    GPIO = auto()
    KEYBOARD = auto()

class InputHandlerFactory:
    @staticmethod
    def create_input_handler(handler_type: InputHandlerType, config) -> InputHandler:
        if handler_type == InputHandlerType.KEYBOARD:
            from input.keyboard_input_handler import KeyboardInputHandler
            return KeyboardInputHandler(config)
        else:
            from input.gpio_input_handler import GPIOInputHandler
            return GPIOInputHandler(config)