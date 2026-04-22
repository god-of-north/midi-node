from core.align_text import AlignText
from .device_state import DeviceState
from .settings_menu_state import SettingsMenuState
from core.device_event import EventType

class HomeState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        if self.context.get_settings_menu_locked():
            bottom = "Setup (locked)"
        else:
            bottom = "[Select] to Setup"
        self.context.ui.write_ui(f"LIVE MODE\r\n\r\n\r\n{bottom}", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            if self.context.get_settings_menu_locked():
                self.context.show_info("Setup locked", line=3, clear_screen=False)
            else:
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

