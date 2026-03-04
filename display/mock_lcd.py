from .display_provider import DisplayProvider
from .MockLCD import CharLCD

class MockLCD(DisplayProvider):
    def __init__(self):
        self.lcd = CharLCD()

    def clear(self):
        self.lcd.clear()

    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        if set_pos:
            self.lcd.cursor_pos = (x, y)
        self.lcd.write_string(text)
