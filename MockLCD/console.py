import sys
from typing import Tuple


class Console:
    def __init__(self):
        self._cursor_pos = (0, 0)

    # ---------- PUBLIC API ----------

    def write_string(self, text: str) -> None:
        """
        Write string at current cursor position.
        """
        self._apply_cursor()
        sys.stdout.write(text)
        sys.stdout.flush()
        
        ## move cursor position. \r - return to start of line, \n - move to next line
        lines = text.splitlines(keepends=True)
        for line in lines:
            if line.endswith("\n"):
                self._cursor_pos = (0, self._cursor_pos[1] + 1)
            else:
                self._cursor_pos = (self._cursor_pos[0] + len(line), self._cursor_pos[1])

    def clear(self) -> None:
        """
        Clear entire screen and move cursor to (0, 0).
        """
        sys.stdout.write("\033[2J")      # Clear screen
        sys.stdout.write("\033[H")       # Move cursor home
        sys.stdout.flush()
        self._cursor_pos = (0, 0)

    @property
    def cursor_pos(self) -> Tuple[int, int]:
        """
        Get cursor position as (x, y)
        """
        return self._cursor_pos

    @cursor_pos.setter
    def cursor_pos(self, pos: Tuple[int, int]) -> None:
        """
        Set cursor position as (x, y)
        """
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise ValueError("cursor_pos must be a tuple (x, y)")

        x, y = pos
        if x < 0 or y < 0:
            raise ValueError("cursor coordinates must be >= 0")

        self._cursor_pos = (x, y)
        self._apply_cursor()

    # ---------- INTERNAL ----------

    def _apply_cursor(self) -> None:
        """
        Move cursor to stored position.
        ANSI is 1-based: (row, col)
        """
        x, y = self._cursor_pos
        sys.stdout.write(f"\033[{y + 1};{x + 1}H")
