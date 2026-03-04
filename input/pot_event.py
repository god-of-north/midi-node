from enum import Enum, auto


class PotEvent(Enum):
    CHANGE_VALUE = auto()
    CHANGE_DIRECTION = auto()
    ON_MIN = auto()
    LEAVE_MIN = auto()
    ON_MAX = auto()
    LEAVE_MAX = auto()
    STOP_CHANGING = auto()