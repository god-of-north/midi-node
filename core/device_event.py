from enum import Enum, auto

class EventType(Enum):
    SYSTEM_SHUTDOWN = auto()
    LCD_TEXT = auto()
    LCD_CLEAR = auto()
    ENCODER_CW = auto()
    ENCODER_CCW = auto()
    ENCODER_SELECT = auto()
    INFO_MESSAGE = auto()

class DeviceEvent:
    def __init__(self, event_type: EventType, data=None):
        self.type = event_type
        self.data = data
