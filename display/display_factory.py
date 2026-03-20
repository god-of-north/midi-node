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
            from RPLCD.i2c import CharLCD
            return CharLCD(
                i2c_expander='PCF8574',
                address=0x27,
                port=1,
                cols=20,
                rows=4
            )
        else:
            raise ValueError(f"Unknown display type: {display_type}")