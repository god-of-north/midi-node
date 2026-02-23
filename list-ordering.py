from typing import List
from MockLCD import CharLCD


class ListOrdering:
    MAX_LINES = 4
    LINE_WIDTH = 40

    def __init__(
        self,
        console: CharLCD,
        items: List[str],
        x: int = 0,
        y: int = 0
    ):
        if not items:
            raise ValueError("Items list cannot be empty")

        self.console = console
        self.items = items

        self.origin_x = x
        self.origin_y = y

        self.current_index = 0
        self.scroll_offset = 0

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Redraw visible part of the list.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line
            self.console.cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.console.write_string(" " * self.LINE_WIDTH)
                continue

            prefix = "> " if item_index == self.current_index else "  "
            text = prefix + self.items[item_index]
            self.console.write_string(text[:self.LINE_WIDTH].ljust(self.LINE_WIDTH))

    def set_current(self, index: int) -> None:
        """
        Select element by index and ensure it's visible.
        """
        if index < 0 or index >= len(self.items):
            raise IndexError("Index out of range")

        self.current_index = index

        if self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index
        elif self.current_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset = self.current_index - self.MAX_LINES + 1

        self.draw()

    def down(self) -> None:
        """
        Move selected element down in list.
        """
        if self.current_index >= len(self.items) - 1:
            return

        # Swap elements
        self.items[self.current_index], self.items[self.current_index + 1] = (
            self.items[self.current_index + 1],
            self.items[self.current_index],
        )

        self.current_index += 1

        # Scroll if needed (same rule as Menu)
        if self.current_index >= self.scroll_offset + self.MAX_LINES - 1:
            self.scroll_offset += 1

        self.draw()

    def up(self) -> None:
        """
        Move selected element up in list.
        """
        if self.current_index <= 0:
            return

        # Swap elements
        self.items[self.current_index], self.items[self.current_index - 1] = (
            self.items[self.current_index - 1],
            self.items[self.current_index],
        )

        self.current_index -= 1

        if self.current_index < self.scroll_offset:
            self.scroll_offset -= 1

        self.draw()

    def get_selected(self) -> List[str]:
        """
        Return reordered list.
        """
        return self.items


if __name__ == "__main__":
    import time

    c = CharLCD()
    c.clear()

    items = ["Kick", "Snare", "HiHat", "Bass", "Lead", "Pad"]

    ordering = ListOrdering(c, items, x=0, y=0)
    ordering.draw()

    time.sleep(0.5)
    ordering.down()
    time.sleep(0.5)
    ordering.down()
    time.sleep(0.5)
    ordering.up()

    print("\nResult:", ordering.get_selected())
