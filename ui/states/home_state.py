from core.align_text import AlignText
from .device_state import DeviceState
from .settings_menu_state import SettingsMenuState
from core.device_event import EventType

class HomeState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("LIVE MODE\r\n\r\n\r\n[Select] to Setup", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.transition_to(SettingsMenuState)
        elif event.type == EventType.INFO_MESSAGE:
            info = event.data.get("info", "")
            line = event.data.get("line", 2)-1
            clear_screen = event.data.get("clear_screen", False)
            align:AlignText = event.data.get("align", AlignText.CENTER)
            if clear_screen:
                self.context.ui.clear_ui()
            text = f"{info}".center(20) if align == AlignText.CENTER else info.ljust(20) if align == AlignText.LEFT else info.rjust(20)
            self.context.ui.write_ui(text, 0, line, True)

