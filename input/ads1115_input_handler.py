import logging
import time
# Removed from threading import Event, Thread as they are no longer needed for internal threading
from collections import deque

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from .input_handler import InputHandler
from .pot_event import PotEvent
from storage.app_config import AppConfig

# Define constants for potentiometer events
POT_MIN_THRESHOLD = 500  # Raw value to consider as "min"
POT_MAX_THRESHOLD = 32000  # Raw value to consider as "max"
POT_STOP_CHANGING_TIMEOUT = 0.1  # Seconds after last change to fire STOP_CHANGING

class Potentiometer:
    def __init__(self, name: str, analog_in_channel: AnalogIn, actions: dict):
        self.name = name
        self.channel = analog_in_channel
        self.actions = actions
        self.last_value = self.channel.value if analog_in_channel else 0 # Initialize with current value or 0
        self.last_direction = 0  # 1 for increasing, -1 for decreasing, 0 for no change
        self.last_change_time = time.time()
        self.is_min = False
        self.is_max = False

    def process_value(self, current_value: int, threshold: int):
        # Check for significant change to avoid noise
        if abs(current_value - self.last_value) > threshold:
            self._fire_event(PotEvent.CHANGE_VALUE, current_value)
            
            # Detect direction change
            current_direction = 0
            if current_value > self.last_value:
                current_direction = 1
            elif current_value < self.last_value:
                current_direction = -1

            if current_direction != 0 and current_direction != self.last_direction:
                self._fire_event(PotEvent.CHANGE_DIRECTION, current_value)
                self.last_direction = current_direction
            
            self.last_value = current_value
            self.last_change_time = time.time()
            self.is_min = False
            self.is_max = False

        # Check for min/max thresholds
        if current_value < POT_MIN_THRESHOLD and not self.is_min:
            self._fire_event(PotEvent.ON_MIN, current_value)
            self.is_min = True
        elif current_value >= POT_MIN_THRESHOLD and self.is_min:
            self._fire_event(PotEvent.LEAVE_MIN, current_value)
            self.is_min = False
        
        if current_value > POT_MAX_THRESHOLD and not self.is_max:
            self._fire_event(PotEvent.ON_MAX, current_value)
            self.is_max = True
        elif current_value <= POT_MAX_THRESHOLD and self.is_max:
            self._fire_event(PotEvent.LEAVE_MAX, current_value)
            self.is_max = False

    def check_stop_changing(self):
        if (time.time() - self.last_change_time) > POT_STOP_CHANGING_TIMEOUT and self.last_direction != 0:
            self._fire_event(PotEvent.STOP_CHANGING, self.last_value)
            self.last_direction = 0 # Reset direction after stop changing event

    def _fire_event(self, event_type: PotEvent, value: int):
        action = self.actions.get(event_type)
        if action:
            logging.debug(f"Firing PotEvent {event_type} for {self.name} with value {value}")
            action.execute(value=value) # Assuming actions can take a 'value' parameter
        else:
            logging.debug(f"No action defined for PotEvent {event_type} on {self.name}")

class ADS1115InputHandler(InputHandler):
    def __init__(self, config: AppConfig):
        self.config = config
        self.potentiometers: list[Potentiometer] = []
        self.i2c = None
        self.ads = None
        
        if self.config.ads1115_enabled:
            self._initialize_ads1115()
        else:
            logging.info("ADS1115 input handler is disabled in config.")

    def _initialize_ads1115(self):
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(self.i2c, address=self.config.ads1115_address)
            self.ads.gain = self.config.ads1115_gain
            logging.info(f"Initialized ADS1115 at address 0x{self.config.ads1115_address:X} with gain {self.config.ads1115_gain}")
        except ValueError as e:
            logging.error(f"Failed to initialize ADS1115: {e}.")
            self.ads = None
        except Exception as e:
            logging.error(f"An unexpected error occurred during ADS1115 initialization: {e}")
            self.ads = None

    def add_potentiometer(self, name: str, analog_pin: int, actions: dict):
        # We allow adding pots even if ads is None, but they won't function
        if self.ads is None:
            logging.warning(f"ADS1115 not initialized, potentiometer {name} will not function.")
            chan = None # Assign None to channel if ADS is not initialized
        else:
            # Mapping analog_pin (0-3) to ADS.P0, ADS.P1, etc.
            ads_pin = getattr(ADS, f"P{analog_pin}")
            chan = AnalogIn(self.ads, ads_pin)
        
        pot = Potentiometer(name, chan, actions)
        self.potentiometers.append(pot)
        logging.info(f"Added potentiometer {name} on AIN{analog_pin} (functional: {chan is not None})")

    # Not applicable for ADS1115, but required by InputHandler ABC
    def add_button(self, key_name, actions, tap_time=0.25, long_press=0.6):
        logging.warning("ADS1115InputHandler does not support buttons.")
        pass

    # Not applicable for ADS1115, but required by InputHandler ABC
    def add_encoder(self, left_key, right_key, callback):
        logging.warning("ADS1115InputHandler does not support encoders.")
        pass

    def tick(self):
        if not self.config.ads1115_enabled or self.ads is None:
            return # Skip if disabled or not initialized

        for pot in self.potentiometers:
            if pot.channel is not None: # Only process if the channel was successfully initialized
                try:
                    current_value = pot.channel.value
                    pot.process_value(current_value, self.config.ads1115_pot_threshold)
                    pot.check_stop_changing()
                except Exception as e:
                    logging.error(f"Error reading potentiometer {pot.name}: {e}")
            # No sleep here; InputManager will handle the polling interval

    def stop(self):
        logging.info("ADS1115InputHandler stopping.")
        # I2C resources are typically managed by the OS or the busio library
        # when the object goes out of scope. No explicit release needed here.
        if self.i2c:
            try:
                # Some I2C implementations might benefit from explicit closing
                if hasattr(self.i2c, 'deinit'): # For CircuitPython busio
                    self.i2c.deinit()
                elif hasattr(self.i2c, 'close'): # For some Linux smbus/i2c-dev wrappers
                    self.i2c.close()
            except Exception as e:
                logging.error(f"Error closing I2C bus for ADS1115: {e}")
        self.i2c = None
        self.ads = None
