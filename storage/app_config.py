from enum import Enum, auto

from controls.control import Control
from midi.midi_output_type import MidiOutputType


class AppMode(Enum):
    SIMULATION = auto()
    LIVE = auto()

class PotCalibration:
    def __init__(self):
        self.min_value = 500
        self.max_value = 32000
        self.min_threshold = 500
        self.max_threshold = 32000
        self.stop_changing_timeout = 0.1  # seconds after last change to fire STOP_CHANGING event
        self.ema_filter_alpha_min = 0.1 # EMA filter smoothing factor: Alpha used when the knob is still (max stability).
        self.ema_filter_alpha_max = 0.6 # EMA filter smoothing factor: Alpha used during fast movements (max responsiveness).
        self.ema_filter_sensitivity = 0.1 # How quickly the filter 'wakes up' to movement.

    def to_dict(self):
        return {
            "min_value": self.min_value,
            "max_value": self.max_value,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
            "stop_changing_timeout": self.stop_changing_timeout,
            "ema_filter_alpha_min": self.ema_filter_alpha_min,
            "ema_filter_alpha_max": self.ema_filter_alpha_max,
            "ema_filter_sensitivity": self.ema_filter_sensitivity,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        instance.min_value = data.get("min_value", 500)
        instance.max_value = data.get("max_value", 32000)
        instance.min_threshold = data.get("min_threshold", 600)
        instance.max_threshold = data.get("max_threshold", 30000)
        instance.stop_changing_timeout = data.get("stop_changing_timeout", 0.1)
        instance.ema_filter_alpha_min = data.get("ema_filter_alpha_min", 0.1)
        instance.ema_filter_alpha_max = data.get("ema_filter_alpha_max", 0.6)
        instance.ema_filter_sensitivity = data.get("ema_filter_sensitivity", 0.1)
        return instance

class AppConfig:
    def __init__(self):
        self.buttons_tap_time = 0.25
        self.buttons_long_press_time = 0.6
        # GPIO: True = switch to GND (idle high, pull-up); False = switch to VCC (idle low, pull-down).
        self.buttons_active_low = True
        self.ads1115_address = 0x48
        self.ads1115_gain = 1
        self.ads1115_pot_threshold = 200 # raw value change
        self.ads1115_enabled = True # New: Enable/disable ADS1115InputHandler
        self.input_poll_interval = 0.01  # seconds
        self.mouse_input_enabled = True # New: Enable/disable MouseInputHandler
        self.mouse_pot_sensitivity = 500 # New: How much mouse movement (pixels) changes pot value
        self.mouse_pot_threshold = 100 # New: Threshold for significant change in mouse pot value
        self.pot_calibration: dict[Control, PotCalibration] = {
            Control.EXP_PEDAL_1: PotCalibration(),
            Control.EXP_PEDAL_2: PotCalibration(),
        } # New: Calibration settings for each potentiometer

    def to_dict(self):
        return {
            "buttons_tap_time": self.buttons_tap_time,
            "buttons_long_press_time": self.buttons_long_press_time,
            "buttons_active_low": self.buttons_active_low,
            "ads1115_address": self.ads1115_address,
            "ads1115_gain": self.ads1115_gain,
            "ads1115_pot_threshold": self.ads1115_pot_threshold,
            "ads1115_enabled": self.ads1115_enabled, 
            "input_poll_interval": self.input_poll_interval,
            "mouse_input_enabled": self.mouse_input_enabled,
            "mouse_pot_sensitivity": self.mouse_pot_sensitivity,
            "mouse_pot_threshold": self.mouse_pot_threshold,
            "pot_calibration": {
                control.name: cal.to_dict() for control, cal in self.pot_calibration.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        instance.buttons_tap_time = data.get("buttons_tap_time", 0.25)
        instance.buttons_long_press_time = data.get("buttons_long_press_time", 0.6)
        instance.buttons_active_low = data.get("buttons_active_low", True)
        instance.ads1115_address = data.get("ads1115_address", 0x48)
        instance.ads1115_gain = data.get("ads1115_gain", 1)
        instance.ads1115_pot_threshold = data.get("ads1115_pot_threshold", 200)
        instance.ads1115_enabled = data.get("ads1115_enabled", True) # New
        instance.input_poll_interval = data.get("input_poll_interval", 0.01)
        instance.mouse_input_enabled = data.get("mouse_input_enabled", True) # New
        instance.mouse_pot_sensitivity = data.get("mouse_pot_sensitivity", 500) # New
        instance.mouse_pot_threshold = data.get("mouse_pot_threshold", 100) # New
        return instance
