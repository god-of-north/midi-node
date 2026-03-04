from typing import List
from .device_state import DeviceState
from core.device_event import EventType

class ListItemReplaceState(DeviceState):
    MAX_LINES = 4

    def __init__(self, context, items:List[str]=None, current_index:int=0, element_name:str="Item", callback=None, return_to_previous_depth:int=1):
        super().__init__(context)

        self.callback = callback
        self.items = items or ["Back"]
        self.origin_x = 0
        self.origin_y = 0

        self.selected_index = current_index
        self.scroll_offset = 0
        self.element_name = element_name
        self.return_to_previous_depth = return_to_previous_depth


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            if self.callback:
                index = self._get_index()
                self.callback(index)
            self.return_to_previous(self.return_to_previous_depth)

    def _refresh_display(self) -> None:
        """
        Draw menu with selector.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line

            cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.context.ui.write_ui(" " * 20, cursor_pos[0], cursor_pos[1], True)
                continue

            is_selected = item_index == self.selected_index
            item_name = self.element_name if is_selected else self.items[item_index]
            line_text = f"{item_index:3d}: {item_name}"
            prefix = ">" if is_selected else " "
            text = f"{prefix} {line_text}"

            # Clear line leftovers
            self.context.ui.write_ui(text.ljust(20), cursor_pos[0], cursor_pos[1], True)

    def _down(self) -> None:
        """
        Move cursor down. Scroll if needed.
        """
        if self.selected_index >= len(self.items) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset += 1

        self._refresh_display()

    def _up(self) -> None:
        """
        Move cursor up. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected element.
        """
        return self.items[self.selected_index]
    
    def _get_index(self) -> int:
        """
        Return currently selected index.
        """
        return self.selected_index
