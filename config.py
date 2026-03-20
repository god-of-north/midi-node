import os
from storage.app_config import AppMode


APP_MODE: AppMode = AppMode.SIMULATION
if os.getenv("MIDI_NODE_MODE") == "LIVE":
    APP_MODE = AppMode.LIVE


