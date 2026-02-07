from typing import List
from char_selector import CharacterSelector
from MockLCD import CharLCD


class StringCreator:
    def __init__(
        self,
        display: CharLCD,
        character_selector: CharacterSelector,
        x: int = 0,
        y: int = 3,
        width: int = 40,
        centered: bool = True
    ):
        self.display = display
        self.char_selector = character_selector
        self.origin_x = x
        self.origin_y = y
        self.width = width
        self.centered = centered

        self.chars: List[str] = []

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Draw the current string.
        """
        self.console.cursor_pos = (self.origin_x, self.origin_y)
        current_string = "".join(self.chars)

        if self.centered:
            self.console.write_string(current_string.center(self.width))
        else:
            self.console.write_string(current_string.ljust(self.width))

    def add_char(self) -> None:
        """
        Add currently selected character to the string.
        """
        selected_char = self.char_selector.get_selected()
        self.chars.append(selected_char)
        self.draw()

    def backspace(self) -> None:
        """
        Remove last character from the string.
        """
        if not self.chars:
            return

        self.chars.pop()
        self.draw()

    def get_string(self) -> str:
        """
        Return the current string.
        """
        return "".join(self.chars)

if __name__ == "__main__":
    display = CharLCD()
    display.clear()

    char_selector = CharacterSelector(
        display=display,
        characters="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
        header="Select characters to build your string:",
        x=0,
        y=0
    )

    string_creator = StringCreator(
        display=display,
        character_selector=char_selector
    )

    char_selector.draw()
    string_creator.draw()

    import time
    time.sleep(1)

    for _ in range(5):
        for _ in range(5):
            char_selector.next()
            time.sleep(0.2)

        for _ in range(1):
            char_selector.prev()
            time.sleep(0.2)

        string_creator.add_char()
        time.sleep(0.2)

    time.sleep(1)
    string_creator.backspace()
    time.sleep(1)
    string_creator.backspace()
    time.sleep(1)

    for _ in range(5):
        for _ in range(5):
            char_selector.next()
            time.sleep(0.2)

        for _ in range(1):
            char_selector.prev()
            time.sleep(0.2)

        string_creator.add_char()
        time.sleep(0.2)

    display.cursor_pos = (0, 5)
    display.write_string(f"Selected: '{char_selector.get_selected()}'")
    display.cursor_pos = (0, 6)
    display.write_string(f"Created String: '{string_creator.get_string()}'")
