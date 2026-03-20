from typing import List
from .device_state import DeviceState
from core.device_event import EventType

class ListOrderingState(DeviceState):
    MAX_LINES = 4
    LINE_WIDTH = 20

    def __init__(self, context, items:List[str]=None, current_index:int=0):
        super().__init__(context)

        self.items = items or ["Back"]

        self.origin_x = 0
        self.origin_y = 0

        self.current_index = 0
        self.scroll_offset = 0

        self._set_current(current_index)


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
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

    def _set_current(self, index: int) -> None:
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

        self._refresh_display()

    def _down(self) -> None:
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

        self._refresh_display()

    def _up(self) -> None:
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

        self._refresh_display()

    def get_list(self) -> List[str]:
        """
        Return reordered list.
        """
        return self.items
