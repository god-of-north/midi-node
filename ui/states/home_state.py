from .device_state import DeviceState
from .settings_menu_state import SettingsMenuState
from core.device_event import EventType

class HomeState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("LIVE MODE\r\n\r\n\r\nPress [Select] to Setup", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.transition_to(SettingsMenuState)
        elif event.type == EventType.INFO_MESSAGE:
            info = event.data.get("info", "")
            self.context.ui.write_ui(f"[{info}]".center(20), 0, 1, True)

