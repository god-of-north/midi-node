from typing import List
from MockLCD import CharLCD


class StringCreator:
    VISIBLE_WIDTH = 20

    def __init__(
        self,
        display: CharLCD,
        characters: str,
        header: str = "",
        x: int = 0,
        y: int = 0,
        centered: bool = True,
    ):
        self.display = display
        self.origin_x = x
        self.origin_y = y
        self.centered = centered
        self.characters: List[str] = list(characters)
        self.selected_index = 0
        self.scroll_offset = 0
        self.header = header

        self.chars: List[str] = []

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        # Header
        self.display.cursor_pos = (self.origin_x, self.origin_y)
        self.display.write_string(self.header.ljust(self.VISIBLE_WIDTH))

        # Characters line
        self.display.cursor_pos = (self.origin_x, self.origin_y + 1)
        visible_chars = self._get_visible_chars()
        self.display.write_string("".join(visible_chars).ljust(self.VISIBLE_WIDTH))

        # Cursor line
        self.display.cursor_pos = (self.origin_x, self.origin_y + 2)
        cursor_x = self.selected_index - self.scroll_offset
        cursor_line = " " * cursor_x + "^"
        self.display.write_string(cursor_line.ljust(self.VISIBLE_WIDTH))

        # Draw the current string.
        self.display.cursor_pos = (self.origin_x, self.origin_y+3)
        current_string = "".join(self.chars)

        if self.centered:
            self.display.write_string(current_string.center(self.VISIBLE_WIDTH))
        else:
            self.display.write_string(current_string.ljust(self.VISIBLE_WIDTH))

    def add_char(self) -> None:
        """
        Add currently selected character to the string.
        """
        selected_char = self.get_selected()
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
    
    def next(self) -> None:
        """
        Move cursor right. Scroll if needed.
        """
        if self.selected_index >= len(self.characters) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.VISIBLE_WIDTH:
            self.scroll_offset += 1

        self.draw()

    def prev(self) -> None:
        """
        Move cursor left. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self.draw()

    def get_selected(self) -> str:
        """
        Return currently selected character.
        """
        return self.characters[self.selected_index]

    def _get_visible_chars(self) -> List[str]:
        end = self.scroll_offset + self.VISIBLE_WIDTH
        return self.characters[self.scroll_offset:end]


if __name__ == "__main__":
    display = CharLCD()
    display.clear()

    string_creator = StringCreator(
        display=display,
        characters="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
        header="Build your string:",
    )

    string_creator.draw()

    import time
    time.sleep(1)

    for _ in range(5):
        for _ in range(5):
            string_creator.next()
            time.sleep(0.2)

        for _ in range(1):
            string_creator.prev()
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
            string_creator.next()
            time.sleep(0.2)

        for _ in range(1):
            string_creator.prev()
            time.sleep(0.2)

        string_creator.add_char()
        time.sleep(0.2)

    display.cursor_pos = (0, 5)
    display.write_string(f"Selected: '{string_creator.get_selected()}'")
    display.cursor_pos = (0, 6)
    display.write_string(f"Created String: '{string_creator.get_string()}'")
