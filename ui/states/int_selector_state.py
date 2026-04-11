from .device_state import DeviceState
from core.device_event import EventType


class IntNumberSelectorState(DeviceState):
    LINE_WIDTH = 20

    def __init__(
        self,
        context,
        min_value: int = 0,
        max_value: int = 100,
        value: int = 0,
        header: str = "Integer Selector"
    ):
        super().__init__(context)

        self.min_value = min_value
        self.max_value = max_value
        self.header = header

        self.origin_x = 0
        self.origin_y = 0

        self.value = value

        # Pre-calc width for zero-padded numbers (optional but nice)
        self._num_width = len(str(max(abs(min_value), abs(max_value))))


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Draw header and current integer value.
        """
        # Header
        self.context.ui.write_ui(self.header.ljust(self.LINE_WIDTH), self.origin_x, self.origin_y, True)

        # Value line
        formatted = self._format_value(self.value)
        value_line = f"< {formatted} >".center(self.LINE_WIDTH)

        self.context.ui.write_ui(value_line[:self.LINE_WIDTH], self.origin_x, self.origin_y + 1, True)

        # Clear remaining lines
        for i in range(2, 4):
            self.context.ui.write_ui(" " * self.LINE_WIDTH, self.origin_x, self.origin_y + i, True)

    def _next(self) -> None:
        """
        Increment value by 1 (cyclic).
        """
        if self.value >= self.max_value:
            self.value = self.min_value
        else:
            self.value += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Decrement value by 1 (cyclic).
        """
        if self.value <= self.min_value:
            self.value = self.max_value
        else:
            self.value -= 1

        self._refresh_display()

    def get_value(self) -> int:
        """
        Return current integer value.
        """
        return self.value

    def _format_value(self, value: int) -> str:
        """
        Format value for display (zero-padded).
        """
        sign = "-" if value < 0 else ""
        return f"{sign}{abs(value):0{self._num_width}d}"

class IntSelectorState(IntNumberSelectorState):
    def __init__(self, context, value: int = 0, callback=None, header="Set Value:", min_value=0, max_value=100):
        super().__init__(
            context,
            min_value=min_value,
            max_value=max_value,
            value=value,
            header=header
        )
        self.callback = callback


    def return_to_previous(self, deep: int = 1):
        self.callback(self.get_value())
        super().return_to_previous()