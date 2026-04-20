import time

from core.device_event import EventType
from ui.states.menu_selector_state import MenuSelectorState
from ui.states.menu_state import MenuState
from ui.states.wifi_password_state import WifiPasswordState


def _clip(s: str, max_len: int = 19) -> str:
    s = s.replace("\r", " ").replace("\n", " ")
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


class WifiSettingsState(MenuState):
    def __init__(self, context):
        super().__init__(context)
        self._pending_ssid: str | None = None
        self._status_key = ""

    def _status_menu_label(self) -> str:
        wifi = self.context.wifi
        if wifi.is_connected():
            ac = wifi.active_connection()
            ssid = (ac.ssid if ac else None) or "?"
            ip = wifi.get_ip_address() or "--"
            return _clip(f"OK:{ssid} {ip}")
        return _clip("Not connected")

    def on_enter(self):
        if self._pending_ssid is not None:
            ssid = self._pending_ssid
            self._pending_ssid = None
            self.transition_to(WifiPasswordState, ssid=ssid)
            return

        self._status_key = self._status_menu_label()
        self.items = [
            self._status_key,
            "Refresh",
            "Connect",
            "Disconnect",
            "Reconnect",
            "Back",
        ]
        self.selected_index = 0
        self.scroll_offset = 0
        super().on_enter()

    def _ssid_selected(self, selected: str) -> None:
        self._pending_ssid = selected

    def _start_connect(self) -> None:
        ssids = self.context.wifi.list_ssid()
        if not ssids:
            self.context.show_info("No networks found", line=1)
            return
        self.transition_to(
            MenuSelectorState,
            param=ssids[0],
            items=ssids,
            callback=self._ssid_selected,
        )

    def _show_cmd_result(self, msg: str) -> None:
        line = _clip(msg or "OK", 40)
        self.context.show_info(line, line=2, clear_screen=False)
        time.sleep(0.8)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            if selected == self._status_key or selected == "Refresh":
                self.on_enter()
                return
            if selected == "Connect":
                self._start_connect()
                return
            if selected == "Disconnect":
                self._show_cmd_result(self.context.wifi.disconnect())
                self.on_enter()
                return
            if selected == "Reconnect":
                self._show_cmd_result(self.context.wifi.reconnect())
                self.on_enter()
                return
            if selected == "Back":
                self.return_to_previous()
                return
        super().handle_event(event)
