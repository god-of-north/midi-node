from enum import Enum, auto

class ButtonEvent(Enum):
    PRESS = auto()
    RELEASE = auto()
    TAP = auto()
    DOUBLE_TAP = auto()
    TRIPLE_TAP = auto()
    LONG_PRESS = auto()
    LONG_PRESS_RELEASE = auto()
