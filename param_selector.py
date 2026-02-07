from typing import List
from MockLCD import CharLCD


class ParameterSelector:
    LINE_WIDTH = 40

    def __init__(
        self,
        display: CharLCD,
        values: List[str],
        header: str = "",
        x: int = 0,
        y: int = 0
    ):
        if not values:
            raise ValueError("Parameter values list cannot be empty")

        self.display = display
        self.values = values
        self.header = header

        self.origin_x = x
        self.origin_y = y

        self.selected_index = 0

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Draw header and current parameter value.
        """
        # Header
        self.display.cursor_pos = (self.origin_x, self.origin_y)
        self.display.write_string(self.header.ljust(self.LINE_WIDTH))

        # Value (centered for readability)
        value = self.values[self.selected_index]
        value_line = f"< {value} >"
        value_line = value_line.center(self.LINE_WIDTH)

        self.display.cursor_pos = (self.origin_x, self.origin_y + 1)
        self.display.write_string(value_line[:self.LINE_WIDTH])

        # Clear remaining lines
        for i in range(2, 4):
            self.display.cursor_pos = (self.origin_x, self.origin_y + i)
            self.display.write_string(" " * self.LINE_WIDTH)

    def next(self) -> None:
        """
        Select next parameter value (cyclic).
        """
        self.selected_index = (self.selected_index + 1) % len(self.values)
        self.draw()

    def prev(self) -> None:
        """
        Select previous parameter value (cyclic).
        """
        self.selected_index = (self.selected_index - 1) % len(self.values)
        self.draw()

    def get_value(self) -> str:
        """
        Return currently selected parameter value.
        """
        return self.values[self.selected_index]


if __name__ == "__main__":
    # Example usage
    import time

    display = CharLCD()
    display.clear()

    params = ["Param A", "Param B", "Param C", "Param D", "Param E", "Param F"]
    selector = ParameterSelector(display, params, header="Select Parameter:", x=0, y=0)
    selector.draw()

    time.sleep(1)
    selector.next()
    time.sleep(1)
    selector.next()
    time.sleep(1)
    selector.prev()
    time.sleep(1)
    selected_value = selector.get_value()
    display.cursor_pos = (0, 6)
    display.write_string(f"Selected: {selected_value}")
    time.sleep(2)