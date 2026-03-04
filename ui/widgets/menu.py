from typing import List
from display.MockLCD import CharLCD


class Menu:
    MAX_LINES = 4

    def __init__(self, display: CharLCD, items: List[str], x: int = 0, y: int = 0):
        if not items:
            raise ValueError("Menu items list cannot be empty")

        self.display = display
        self.items = items

        self.origin_x = x
        self.origin_y = y

        self.selected_index = 0   # index in items
        self.scroll_offset = 0    # first visible item index

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Draw menu with selector.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line

            self.display.cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.display.write_string(" " * 20)
                continue

            prefix = ">" if item_index == self.selected_index else " "
            text = f"{prefix} {self.items[item_index]}"

            # Clear line leftovers
            self.display.write_string(text.ljust(20))

    def down(self) -> None:
        """
        Move cursor down. Scroll if needed.
        """
        if self.selected_index >= len(self.items) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset += 1

        self.draw()

    def up(self) -> None:
        """
        Move cursor up. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self.draw()

    def get_selected(self) -> str:
        """
        Return currently selected element.
        """
        return self.items[self.selected_index]
