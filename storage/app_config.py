from enum import Enum, auto

from midi.midi_output_type import MidiOutputType


class AppMode(Enum):
    SIMULATION = auto()
    LIVE = auto()

class AppConfig:
    def __init__(self):
        self.buttons_tap_time = 0.25
        self.buttons_long_press_time = 0.6

    def to_dict(self):
        return {
            "buttons_tap_time": self.buttons_tap_time,
            "buttons_long_press_time": self.buttons_long_press_time
        }

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        instance.buttons_tap_time = data.get("buttons_tap_time", 0.25)
        instance.buttons_long_press_time = data.get("buttons_long_press_time", 0.6)
        return instance
