from .device_state import DeviceState
from core.device_event import EventType

class DummyState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("DUMMY STATE\r\nNo Actions", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()
