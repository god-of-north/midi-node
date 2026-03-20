from .display_provider import DisplayProvider
from RPLCD.i2c import CharLCD


class LCD2004(DisplayProvider):
    def __init__(self):
        self.lcd = CharLCD(
            i2c_expander='PCF8574',
            address=0x27,
            port=1,
            cols=20,
            rows=4
        )

    def clear(self):
        self.lcd.clear()

    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        if set_pos:
            self.lcd.cursor_pos = (y, x)
        self.lcd.write_string(text)
