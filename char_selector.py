from typing import List
from MockLCD import CharLCD


class CharacterSelector:
    VISIBLE_WIDTH = 40

    def __init__(
        self,
        display: CharLCD,
        characters: str,
        header: str = "",
        x: int = 0,
        y: int = 0
    ):
        if not characters:
            raise ValueError("Character list cannot be empty")

        self.display = display
        self.characters: List[str] = list(characters)

        self.header = header

        self.origin_x = x
        self.origin_y = y

        self.selected_index = 0
        self.scroll_offset = 0

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Draw header, characters and cursor.
        """
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

    def update_header(self, text: str) -> None:
        """
        Update header text.
        """
        self.header = text
        self.draw()

    # ---------- INTERNAL ----------

    def _get_visible_chars(self) -> List[str]:
        end = self.scroll_offset + self.VISIBLE_WIDTH
        return self.characters[self.scroll_offset:end]

if __name__ == "__main__":
    import time

    display = CharLCD()
    display.clear()

    selector = CharacterSelector(
        display,
        characters="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:',.<>/?`~ ",
        header="Select a character:",
        x=0,
        y=0
    )

    selector.draw()

    time.sleep(1)
    for _ in range(50):
        selector.next()
        time.sleep(0.2)

    time.sleep(1)
    for _ in range(15):
        selector.prev()
        time.sleep(0.2)

    time.sleep(1)
    display.cursor_pos = (0, 5)
    display.write_string(f"Selected: '{selector.get_selected()}'")