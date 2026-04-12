from enum import Enum, auto

from midi.midi_output_type import MidiOutputType


class AppMode(Enum):
    SIMULATION = auto()
    LIVE = auto()

class AppConfig:
    def __init__(self):
        self.buttons_tap_time = 0.25
        self.buttons_long_press_time = 0.6
        self.ads1115_address = 0x48
        self.ads1115_gain = 1
        self.ads1115_pot_threshold = 200 # raw value change
        self.ads1115_enabled = True # New: Enable/disable ADS1115InputHandler
        self.input_poll_interval = 0.01  # seconds
        self.mouse_input_enabled = True # New: Enable/disable MouseInputHandler
        self.mouse_pot_sensitivity = 500 # New: How much mouse movement (pixels) changes pot value
        self.mouse_pot_threshold = 100 # New: Threshold for significant change in mouse pot value

    def to_dict(self):
        return {
            "buttons_tap_time": self.buttons_tap_time,
            "buttons_long_press_time": self.buttons_long_press_time,
            "ads1115_address": self.ads1115_address,
            "ads1115_gain": self.ads1115_gain,
            "ads1115_pot_threshold": self.ads1115_pot_threshold,
            "ads1115_enabled": self.ads1115_enabled, # New
            "input_poll_interval": self.input_poll_interval,
            "mouse_input_enabled": self.mouse_input_enabled, # New
            "mouse_pot_sensitivity": self.mouse_pot_sensitivity, # New
            "mouse_pot_threshold": self.mouse_pot_threshold # New
        }

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        instance.buttons_tap_time = data.get("buttons_tap_time", 0.25)
        instance.buttons_long_press_time = data.get("buttons_long_press_time", 0.6)
        instance.ads1115_address = data.get("ads1115_address", 0x48)
        instance.ads1115_gain = data.get("ads1115_gain", 1)
        instance.ads1115_pot_threshold = data.get("ads1115_pot_threshold", 200)
        instance.ads1115_enabled = data.get("ads1115_enabled", True) # New
        instance.input_poll_interval = data.get("input_poll_interval", 0.01)
        instance.mouse_input_enabled = data.get("mouse_input_enabled", True) # New
        instance.mouse_pot_sensitivity = data.get("mouse_pot_sensitivity", 500) # New
        instance.mouse_pot_threshold = data.get("mouse_pot_threshold", 100) # New
        return instance
