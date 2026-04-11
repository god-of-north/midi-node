import time
import keyboard
from collections import deque

from input.input_handler import InputHandler
from .button_event import ButtonEvent

# Mocked event to mimic gpiod event structure
class MockEvent:
    def __init__(self, pin, event_type):
        self.line_offset = pin
        self.event_type = event_type # 'FALLING' or 'RISING'

class KeyboardInputHandler(InputHandler):
    def __init__(self, config):
        self.buttons = {}
        self.encoders = {}
        self.event_queue = deque()
        self.key_states = {} # Track if a key is already "down" to prevent auto-repeat
        self.config = config

    def add_button(self, key_name, actions):
        """key_name: the keyboard key (e.g., 'space', 'enter', 'z')"""
        self.buttons[key_name] = {
            "actions": actions,
            "press_timestamp": None,
            "tap_count": 0,
            "tap_timer_start": None,
            "long_press_fired": False
        }
        self.key_states[key_name] = False
        
        # Hook keyboard events
        keyboard.on_press_key(key_name, lambda _: self._on_key_event(key_name, "FALLING"))
        keyboard.on_release_key(key_name, lambda _: self._on_key_event(key_name, "RISING"))

    def add_encoder(self, left_key, right_key, callback):
        """
        Maps two keys to simulate rotation.
        Example: left_key='left', right_key='right'
        """
        # We store this to simulate the RotaryEncoder class behavior
        self.encoders[left_key] = {"callback": callback, "dir": -1}
        self.encoders[right_key] = {"callback": callback, "dir": 1}
        
        keyboard.on_press_key(left_key, lambda _: self._on_encoder_hit(left_key))
        keyboard.on_press_key(right_key, lambda _: self._on_encoder_hit(right_key))

    def _on_key_event(self, key, edge):
        # Prevent keyboard auto-repeat from spamming PRESS events
        if edge == "FALLING":
            if self.key_states[key]: return 
            self.key_states[key] = True
        else:
            self.key_states[key] = False
            
        self.event_queue.append(MockEvent(key, edge))

    def _on_encoder_hit(self, key):
        # Encoders are immediate in this mock for better UX
        data = self.encoders[key]
        data["callback"](data["dir"])

    def _fire(self, pin_data, event_type: ButtonEvent):
        action = pin_data["actions"].get(event_type)
        if action:
            action()

    def tick(self):
        # 1. Process "Hardware" Events
        while self.event_queue:
            event = self.event_queue.popleft()
            if event.line_offset in self.buttons:
                self._handle_mock_hardware_event(event)
        
        # 2. Check timeouts (Long press / Multi-tap)
        self._check_all_timeouts()
    
    def stop(self):
        """
        Stops the input handler. For KeyboardInputHandler, this mainly means unhooking
        keyboard events if necessary. For now, we'll let the program termination handle it.
        """
        # keyboard.unhook_all() # Could be used if explicit unhooking is desired
        pass

    def _handle_mock_hardware_event(self, event):
        key = event.line_offset
        data = self.buttons[key]
        now = time.time()

        if event.event_type == "FALLING":
            data["press_timestamp"] = now
            data["long_press_fired"] = False
            self._fire(data, ButtonEvent.PRESS)
        
        elif event.event_type == "RISING":
            if data["press_timestamp"]:
                duration = now - data["press_timestamp"]
                self._fire(data, ButtonEvent.RELEASE)
                if duration < self.config.buttons_long_press_time:
                    data["tap_count"] += 1
                    data["tap_timer_start"] = now
                if data["long_press_fired"]:
                    self._fire(data, ButtonEvent.LONG_PRESS_RELEASE)

                data["press_timestamp"] = None

    def _check_all_timeouts(self):
        now = time.time()
        for key, data in self.buttons.items():
            if data["press_timestamp"] and not data["long_press_fired"]:
                if (now - data["press_timestamp"]) >= self.config.buttons_long_press_time:
                    data["long_press_fired"] = True
                    data["tap_count"] = 0
                    self._fire(data, ButtonEvent.LONG_PRESS)

            if data["tap_count"] > 0 and data["tap_timer_start"]:
                if (now - data["tap_timer_start"]) > self.config.buttons_tap_time:
                    gestures = {1: ButtonEvent.TAP, 2: ButtonEvent.DOUBLE_TAP, 3: ButtonEvent.TRIPLE_TAP}
                    event = gestures.get(data["tap_count"], ButtonEvent.TRIPLE_TAP)
                    self._fire(data, event)
                    data["tap_count"] = 0
                    data["tap_timer_start"] = None
