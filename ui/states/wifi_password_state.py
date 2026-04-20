import time

from ui.states.string_creator_state import StringCreatorState


class WifiPasswordState(StringCreatorState):
    """Enter Wi‑Fi password and run nmcli connect for the chosen SSID."""

    _CHARS = (
        "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz "
        "_0123456789 _!@#$%^&*()-_=+"
    )

    def __init__(self, context, ssid: str):
        super().__init__(
            context,
            value="",
            characters=self._CHARS,
            header=f"PW:{ssid[:12]}",
            centered=False,
        )
        self.ssid = ssid

    def return_to_previous(self, deep: int = 1) -> None:
        password = self._get_string().strip()
        msg = self.context.wifi.connect(self.ssid, password)
        line = (msg or "OK").replace("\r", " ").replace("\n", " ")[:40]
        self.context.show_info(line, line=2, clear_screen=False)
        time.sleep(1.0)
        super().return_to_previous(deep)
