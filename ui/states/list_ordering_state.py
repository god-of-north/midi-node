from typing import Any, Callable, List, Optional
from .device_state import DeviceState
from core.device_event import EventType


class ListOrderingState(DeviceState):
    """
    Reorder a mutable sequence: navigate with >, SELECT to grab (#), encoder
    moves the grabbed item, SELECT to place (> again), SELECT on [Apply] to exit.
    """

    MAX_LINES = 4
    LINE_WIDTH = 20
    APPLY_LABEL = "[Apply]"

    def __init__(
        self,
        context,
        items: Optional[List[str]] = None,
        *,
        sequence: Optional[List[Any]] = None,
        format_line: Optional[Callable[[int, Any], str]] = None,
        current_index: int = 0,
    ):
        super().__init__(context)

        if sequence is not None:
            self._sequence = sequence
        else:
            self._sequence = items or ["Back"]
        self._format_line = format_line or (lambda i, x: str(x))

        self.origin_x = 0
        self.origin_y = 0

        n = len(self._sequence)
        max_cursor = n
        self._cursor_index = max(0, min(current_index, max_cursor))
        self._grabbed_at: Optional[int] = None
        self.scroll_offset = 0
        self._sync_scroll()

    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if self._grabbed_at is not None:
            if event.type == EventType.ENCODER_CW:
                self._move_grabbed_down()
            elif event.type == EventType.ENCODER_CCW:
                self._move_grabbed_up()
            elif event.type == EventType.ENCODER_SELECT:
                self._cursor_index = self._grabbed_at
                self._grabbed_at = None
                self._sync_scroll()
                self._refresh_display()
        else:
            if event.type == EventType.ENCODER_CW:
                self._cursor_down()
            elif event.type == EventType.ENCODER_CCW:
                self._cursor_up()
            elif event.type == EventType.ENCODER_SELECT:
                if self._cursor_index == len(self._sequence):
                    self.return_to_previous()
                else:
                    self._grabbed_at = self._cursor_index
                    self._sync_scroll()
                    self._refresh_display()

    def _total_rows(self) -> int:
        return len(self._sequence) + 1

    def _focus_row(self) -> int:
        if self._grabbed_at is not None:
            return self._grabbed_at
        return self._cursor_index

    def _sync_scroll(self) -> None:
        focus = self._focus_row()
        total = self._total_rows()
        if focus < self.scroll_offset:
            self.scroll_offset = focus
        if focus >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset = focus - self.MAX_LINES + 1
        max_off = max(0, total - self.MAX_LINES)
        self.scroll_offset = max(0, min(self.scroll_offset, max_off))

    def _cursor_down(self) -> None:
        if self._cursor_index >= self._total_rows() - 1:
            return
        self._cursor_index += 1
        self._sync_scroll()
        self._refresh_display()

    def _cursor_up(self) -> None:
        if self._cursor_index <= 0:
            return
        self._cursor_index -= 1
        self._sync_scroll()
        self._refresh_display()

    def _move_grabbed_down(self) -> None:
        g = self._grabbed_at
        if g is None or g >= len(self._sequence) - 1:
            return
        seq = self._sequence
        seq[g], seq[g + 1] = seq[g + 1], seq[g]
        self._grabbed_at = g + 1
        self._sync_scroll()
        self._refresh_display()

    def _move_grabbed_up(self) -> None:
        g = self._grabbed_at
        if g is None or g <= 0:
            return
        seq = self._sequence
        seq[g], seq[g - 1] = seq[g - 1], seq[g]
        self._grabbed_at = g - 1
        self._sync_scroll()
        self._refresh_display()

    def _refresh_display(self) -> None:
        total = self._total_rows()
        for row in range(self.MAX_LINES):
            row_index = self.scroll_offset + row
            cursor_pos = (self.origin_x, self.origin_y + row)

            if row_index >= total:
                self.context.ui.write_ui(
                    " " * self.LINE_WIDTH, cursor_pos[0], cursor_pos[1], True
                )
                continue

            if row_index < len(self._sequence):
                row_text = self._format_line(row_index, self._sequence[row_index])
            else:
                row_text = self.APPLY_LABEL

            if self._grabbed_at is not None:
                prefix = "# " if row_index == self._grabbed_at else "  "
            else:
                prefix = "> " if row_index == self._cursor_index else "  "

            text = (prefix + row_text)[: self.LINE_WIDTH].ljust(self.LINE_WIDTH)
            self.context.ui.write_ui(text, cursor_pos[0], cursor_pos[1], True)

    def get_list(self) -> List[Any]:
        """
        Return reordered sequence (same order as on screen).
        """
        return list(self._sequence)
