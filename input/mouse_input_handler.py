import logging
import time
import keyboard # For 'shift' and 'ctrl' detection
from pynput import mouse # For mouse movement

from collections import deque

from .input_handler import InputHandler
from .pot_event import PotEvent
from storage.app_config import AppConfig

# Define constants for potentiometer events
# These can be tuned based on desired sensitivity and behavior
POT_MIN_THRESHOLD = 0    # Mouse value considered "min"
POT_MAX_THRESHOLD = 65535 # Mouse value considered "max" (emulating 16-bit ADC)
POT_STOP_CHANGING_TIMEOUT = 0.1 # Seconds after last change to fire STOP_CHANGING

# Global for mouse listener to prevent it from being garbage collected
_mouse_listener = None
_mouse_position = (0, 0)
_mouse_delta_x = 0

def on_move(x, y):
    global _mouse_position, _mouse_delta_x
    if _mouse_position != (0, 0): # Avoid large delta on first move
        _mouse_delta_x += (x - _mouse_position[0])
    _mouse_position = (x, y)

class MousePotentiometer:
    def __init__(self, name: str, analog_pin_id: int, actions: dict):
        self.name = name
        self.analog_pin_id = analog_pin_id
        self.actions = actions
        self.current_value = 0 # Will be updated by mouse movement
        self.last_value = 0
        self.last_direction = 0  # 1 for increasing, -1 for decreasing, 0 for no change
        self.last_change_time = time.time()
        self.is_min = False
        self.is_max = False
        logging.debug(f"MousePotentiometer {name} created for analog_pin {analog_pin_id}")

    def update_value(self, delta_x: int, sensitivity: float = 1.0):
        # Map mouse delta_x to potentiometer value change
        # The delta_x can be positive or negative.
        # We need to scale it and add it to current_value, clamping within [POT_MIN_THRESHOLD, POT_MAX_THRESHOLD]
        change = int(delta_x * sensitivity)
        new_value = self.current_value + change
        self.current_value = max(POT_MIN_THRESHOLD, min(POT_MAX_THRESHOLD, new_value))

    def process_value(self, threshold: int):
        # Use a simplified threshold for mouse input, or directly use current_value if updated
        if abs(self.current_value - self.last_value) > threshold:
            self._fire_event(PotEvent.CHANGE_VALUE, self.current_value)

            # Detect direction change
            current_direction = 0
            if self.current_value > self.last_value:
                current_direction = 1
            elif self.current_value < self.last_value:
                current_direction = -1

            if current_direction != 0 and current_direction != self.last_direction:
                self._fire_event(PotEvent.CHANGE_DIRECTION, self.current_value)
                self.last_direction = current_direction

            self.last_value = self.current_value
            self.last_change_time = time.time()
            self.is_min = False
            self.is_max = False

        # Check for min/max thresholds
        if self.current_value <= POT_MIN_THRESHOLD and not self.is_min:
            self._fire_event(PotEvent.ON_MIN, self.current_value)
            self.is_min = True
        elif self.current_value > POT_MIN_THRESHOLD and self.is_min:
            self._fire_event(PotEvent.LEAVE_MIN, self.current_value)
            self.is_min = False

        if self.current_value >= POT_MAX_THRESHOLD and not self.is_max:
            self._fire_event(PotEvent.ON_MAX, self.current_value)
            self.is_max = True
        elif self.current_value < POT_MAX_THRESHOLD and self.is_max:
            self._fire_event(PotEvent.LEAVE_MAX, self.current_value)
            self.is_max = False


    def check_stop_changing(self):
        if (time.time() - self.last_change_time) > POT_STOP_CHANGING_TIMEOUT and self.last_direction != 0:
            self._fire_event(PotEvent.STOP_CHANGING, self.current_value)
            self.last_direction = 0 # Reset direction after stop changing event

    def _fire_event(self, event_type: PotEvent, value: int):
        action = self.actions.get(event_type)
        if action:
            logging.debug(f"Firing PotEvent {event_type} for {self.name} with value {value}")
            action(value)
        # else: # Too much noise for debug
            # logging.debug(f"No action defined for PotEvent {event_type} on {self.name}")


class MouseInputHandler(InputHandler):
    def __init__(self, config: AppConfig):
        self.config = config
        self.mouse_potentiometers: dict[int, MousePotentiometer] = {} # Map analog_pin_id to MousePotentiometer
        self._initialize_mouse_listener()
        logging.info("MouseInputHandler initialized.")

    def _initialize_mouse_listener(self):
        global _mouse_listener
        if _mouse_listener is None:
            _mouse_listener = mouse.Listener(on_move=on_move)
            _mouse_listener.start()
            logging.info("Mouse listener started.")

    def add_potentiometer(self, name: str, analog_pin: int, actions: dict):
        if analog_pin not in [0, 1]:
            logging.warning(f"MouseInputHandler only supports analog_pin 0 and 1. {name} not added.")
            return

        pot = MousePotentiometer(name, analog_pin, actions)
        self.mouse_potentiometers[analog_pin] = pot
        logging.info(f"Added mouse potentiometer {name} on virtual AIN{analog_pin}")

    # Not applicable for MouseInputHandler
    def add_button(self, key_name, actions, tap_time=0.25, long_press=0.6):
        logging.warning("MouseInputHandler does not support buttons.")
        pass

    # Not applicable for MouseInputHandler
    def add_encoder(self, left_key, right_key, callback):
        logging.warning("MouseInputHandler does not support encoders.")
        pass

    def tick(self):
        global _mouse_delta_x
        current_delta_x = _mouse_delta_x
        _mouse_delta_x = 0 # Reset delta for next tick

        is_shift_pressed = keyboard.is_pressed('shift')
        is_ctrl_pressed = keyboard.is_pressed('ctrl')

        if is_shift_pressed and not is_ctrl_pressed:
            if 0 in self.mouse_potentiometers:
                pot = self.mouse_potentiometers[0]
                if current_delta_x != 0:
                    pot.update_value(current_delta_x, self.config.mouse_pot_sensitivity) # Assuming sensitivity config exists or default
                pot.process_value(self.config.mouse_pot_threshold) # Assuming threshold config exists
                pot.check_stop_changing()
        elif is_ctrl_pressed and not is_shift_pressed:
            if 1 in self.mouse_potentiometers:
                pot = self.mouse_potentiometers[1]
                if current_delta_x != 0:
                    pot.update_value(current_delta_x, self.config.mouse_pot_sensitivity)
                pot.process_value(self.config.mouse_pot_threshold)
                pot.check_stop_changing()
        elif is_shift_pressed and is_ctrl_pressed:
            # Optionally handle both pressed, e.g., ignore or special action
            logging.debug("Both Shift and Ctrl pressed, ignoring mouse potentiometer input.")
        else:
            # If no modifier is pressed, still check stop changing for any active pots
            for pot in self.mouse_potentiometers.values():
                pot.check_stop_changing()

    def stop(self):
        global _mouse_listener
        if _mouse_listener:
            _mouse_listener.stop()
            _mouse_listener = None
            logging.info("Mouse listener stopped.")
