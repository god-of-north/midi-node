from enum import Enum, auto

class Control(Enum):
    BUTTON_1 = auto()
    BUTTON_2 = auto()
    BUTTON_3 = auto()
    BUTTON_4 = auto()
    EXP_PEDAL_1 = auto()
    EXP_PEDAL_2 = auto()

class ControlType(Enum):
    BUTTON = auto()
    POTENTIOMETER = auto()
