from enum import Enum, auto


class DisplayType(Enum):
    CONSOLE = auto()
    LCD2004 = auto()

class DisplayFactory:
    @staticmethod
    def create_display(display_type: DisplayType):
        if display_type == DisplayType.CONSOLE:
            from .mock_lcd import MockLCD
            return MockLCD()
        elif display_type == DisplayType.LCD2004:
            from .lcd2004 import LCD2004
            return LCD2004()
        else:
            raise ValueError(f"Unknown display type: {display_type}")