from typing import List
from MockLCD import CharLCD


class MenuPlacer:
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
        self.cursor_name = "menu_cursor"

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

            is_selected = item_index == self.selected_index
            item_name = self.cursor_name if is_selected else self.items[item_index]
            line_text = f"{item_index + 1:2d}. {item_name}"
            prefix = ">" if is_selected else " "
            text = f"{prefix} {line_text}"

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
    
    def get_selected_index(self) -> int:
        """
        Return index of currently selected element.
        """
        return self.selected_index


if __name__ == "__main__":
    display = CharLCD()
    menu_items = [f"Item {i}" for i in range(1, 11)]
    menu = MenuPlacer(display, menu_items, x=0, y=0)

    menu.draw()
    import time
    time.sleep(1)

    for _ in range(5):
        menu.down()
        time.sleep(1.5)

    for _ in range(4):
        menu.up()
        time.sleep(1.5)

    selected = menu.get_selected()
    display.cursor_pos = (0, 6)
    display.write_string(f"Selected: {selected}")