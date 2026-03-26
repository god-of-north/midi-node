from typing import List
from .device_state import DeviceState
from core.device_event import EventType

class StringCreatorState(DeviceState):
    VISIBLE_WIDTH = 20

    def __init__(
        self,
        context,
        value: str = "",
        characters: str = "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _",
        header: str = "Create String:",
        centered: bool = True,
    ):
        super().__init__(context)

        self.origin_x = 0
        self.origin_y = 0
        self.centered = centered
        self.characters: List[str] = list("√←" + characters)
        self.selected_index = 0
        self.scroll_offset = 0
        self.header = header

        self.chars: List[str] = list(value or "")

    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            if self._get_selected() == "√":
                self.return_to_previous()
            elif self._get_selected() == "←":
                self._backspace()
            else:
                self._add_char()

    def _refresh_display(self) -> None:
        # Header
        self.context.ui.write_ui(self.header.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y, True)

        # Characters line
        visible_chars = self._get_visible_chars()
        self.context.ui.write_ui("".join(visible_chars).ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 1, True)

        # Cursor line
        cursor_x = self.selected_index - self.scroll_offset
        cursor_line = " " * cursor_x + "^"
        self.context.ui.write_ui(cursor_line.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 2, True)

        # Draw the current string.
        current_string = "".join(self.chars)

        if self.centered:
            self.context.ui.write_ui(current_string.center(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)
        else:
            self.context.ui.write_ui(current_string.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)

    def _add_char(self) -> None:
        """
        Add currently selected character to the string.
        """
        selected_char = self._get_selected()
        self.chars.append(selected_char)
        self._refresh_display()

    def _backspace(self) -> None:
        """
        Remove last character from the string.
        """
        if not self.chars:
            return

        self.chars.pop()
        self._refresh_display()

    def _get_string(self) -> str:
        """
        Return the current string.
        """
        return "".join(self.chars)
    
    def _next(self) -> None:
        """
        Move cursor right. Scroll if needed.
        """
        if self.selected_index >= len(self.characters) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.VISIBLE_WIDTH:
            self.scroll_offset += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Move cursor left. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected character.
        """
        return self.characters[self.selected_index]

    def _get_visible_chars(self) -> List[str]:
        end = self.scroll_offset + self.VISIBLE_WIDTH
        return self.characters[self.scroll_offset:end]
