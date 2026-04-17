import threading
import time

from .device_state import DeviceState


class ShutdownState(DeviceState):
    """Shows shutdown message, then requests immediate system power-off."""

    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("Device shut down".ljust(20), 0, 0, True)
        self.context.ui.write_ui(" ".ljust(20), 0, 1, True)
        self.context.ui.write_ui(" ".ljust(20), 0, 2, True)
        self.context.ui.write_ui(" ".ljust(20), 0, 3, True)

        def _run_shutdown():
            time.sleep(0.4)
            self.context.shutdown_device()

        threading.Thread(target=_run_shutdown, daemon=True).start()

    def handle_event(self, event):
        pass
