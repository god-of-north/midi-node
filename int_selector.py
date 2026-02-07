from MockLCD import CharLCD


class IntNumberSelector:
    LINE_WIDTH = 40

    def __init__(
        self,
        display: CharLCD,
        min_value: int,
        max_value: int,
        header: str = "",
        x: int = 0,
        y: int = 0
    ):
        if min_value > max_value:
            raise ValueError("min_value must be <= max_value")

        self.display = display
        self.min_value = min_value
        self.max_value = max_value
        self.header = header

        self.origin_x = x
        self.origin_y = y

        self.value = min_value

        # Pre-calc width for zero-padded numbers (optional but nice)
        self._num_width = len(str(max(abs(min_value), abs(max_value))))

    # ---------- PUBLIC API ----------

    def draw(self) -> None:
        """
        Draw header and current integer value.
        """
        # Header
        self.display.cursor_pos = (self.origin_x, self.origin_y)
        self.display.write_string(self.header.ljust(self.LINE_WIDTH))

        # Value line
        formatted = self._format_value(self.value)
        value_line = f"< {formatted} >".center(self.LINE_WIDTH)

        self.display.cursor_pos = (self.origin_x, self.origin_y + 1)
        self.display.write_string(value_line[:self.LINE_WIDTH])

        # Clear remaining lines
        for i in range(2, 4):
            self.display.cursor_pos = (self.origin_x, self.origin_y + i)
            self.display.write_string(" " * self.LINE_WIDTH)

    def next(self) -> None:
        """
        Increment value by 1 (cyclic).
        """
        if self.value >= self.max_value:
            self.value = self.min_value
        else:
            self.value += 1

        self.draw()

    def prev(self) -> None:
        """
        Decrement value by 1 (cyclic).
        """
        if self.value <= self.min_value:
            self.value = self.max_value
        else:
            self.value -= 1

        self.draw()

    def get_value(self) -> int:
        """
        Return current integer value.
        """
        return self.value

    # ---------- INTERNAL ----------

    def _format_value(self, value: int) -> str:
        """
        Format value for display (zero-padded).
        """
        sign = "-" if value < 0 else ""
        return f"{sign}{abs(value):0{self._num_width}d}"


if __name__ == "__main__":
    dispaly = CharLCD()
    selector = IntNumberSelector(dispaly, -50, 50, header="Select a Number", x=0, y=0)
    selector.draw()
    import time
    time.sleep(1)
    for _ in range(55):
        selector.next()
        time.sleep(0.1)

    time.sleep(1)

    for _ in range(60):
        selector.prev()
        time.sleep(0.1)

