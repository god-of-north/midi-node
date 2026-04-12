import logging
import gpiod
from gpiod.line import Direction, Edge, Bias, Value
from gpiod import EdgeEvent  # Added for correct event type comparison
from datetime import timedelta
import time
from enum import Enum, auto

from .button_event import ButtonEvent
from .input_handler import InputHandler


class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin, on_rotate):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.on_rotate = on_rotate 

        self.last_clk_falling_time = 0
        self.last_dt_value = 0
        self.rotation_threshold = 0.1

    def process(self, event, chip_request):

        dt_val = chip_request.get_value(self.dt_pin)

        # print(f"CLK event: {event.event_type}, DT value: {dt_val}, Time: {time.time():.3f}")

        if event.event_type == EdgeEvent.Type.FALLING_EDGE:
            self.last_clk_falling_time = time.time()
            self.last_dt_value = dt_val

            # print(f"CLK falling edge detected. Updated last_clk_rising_time: {self.last_clk_falling_time:.3f}, last_dt_value: {self.last_dt_value}")

            return

        if self.last_clk_falling_time == 0 or (time.time() - self.last_clk_falling_time) > self.rotation_threshold or dt_val == self.last_dt_value:

            # print(f"Ignoring CLK rising edge. Time since last falling: {time.time() - self.last_clk_falling_time:.3f}s, DT value: {dt_val}, Last DT value: {self.last_dt_value}")

            return

        direction = 1 if dt_val == Value.ACTIVE else -1
        self.on_rotate(direction)

class GPIOInputHandler(InputHandler):
    def __init__(self, config):
        self.chip_path = "/dev/gpiochip0"
        self.buttons = {}
        self.encoders = {}
        self.all_pins = []
        self.config = config
        self._chip_request = None # Will hold the gpiod.Lines object

    def add_button(self, pin, actions):
        logging.info(f"Adding button on pin {pin}")

        self.buttons[pin] = {
            "actions": actions,
            "press_timestamp": None,
            "tap_count": 0,
            "tap_timer_start": None,
            "long_press_fired": False
        }
        if pin not in self.all_pins: self.all_pins.append(pin)

    def add_encoder(self, clk_pin, dt_pin, callback):
        encoder = RotaryEncoder(clk_pin, dt_pin, callback)
        self.encoders[clk_pin] = encoder
        if clk_pin not in self.all_pins: self.all_pins.append(clk_pin)
        if dt_pin not in self.all_pins: self.all_pins.append(dt_pin)

    def setup_gpio(self):
        """Initializes the gpiod lines after all buttons and encoders are added."""
        configs = {}
        for pin in self.all_pins:
            configs[pin] = gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
                edge_detection=Edge.BOTH,
                debounce_period=timedelta(milliseconds=5) 
            )
        try:
            self._chip_request = gpiod.request_lines(self.chip_path, consumer="multi_ctrl", config=configs)
            logging.info("GPIO lines successfully requested.")
        except Exception as e:
            logging.error(f"Failed to request GPIO lines: {e}. Is gpiod installed and permissions set?")
            self._chip_request = None

    def _fire(self, pin_data, event_type: ButtonEvent):
        logging.info(f"Firing event {event_type}")

        action = pin_data["actions"].get(event_type)
        if action: 
            logging.info(f"Executing action for event {event_type}")
            action()
        else:
            logging.info(f"No action defined for event {event_type}")

    def tick(self):
        if not self._chip_request:
            return # GPIO not setup or failed

        # Wait for events with a short timeout to allow check_all_timeouts to run
        if self._chip_request.wait_edge_events(timedelta(milliseconds=1)): # Reduced timeout for faster loop
            for event in self._chip_request.read_edge_events():
                pin = event.line_offset
                
                if pin in self.encoders:
                    self.encoders[pin].process(event, self._chip_request)
                
                elif pin in self.buttons:
                    self._handle_hardware_event(event)
        
        self._check_all_timeouts()

    def stop(self):
        if self._chip_request:
            logging.info("Releasing GPIO lines.")
            self._chip_request.release()
            self._chip_request = None # Clear the reference

    def _handle_hardware_event(self, event):
        pin = event.line_offset
        data = self.buttons[pin]
        now = time.time()

        # gpiod v2 uses EdgeEvent.Type for event.event_type
        if event.event_type == EdgeEvent.Type.FALLING_EDGE:  # Press (Active Low)
            data["press_timestamp"] = now
            data["long_press_fired"] = False
            self._fire(data, ButtonEvent.PRESS)
        
        elif event.event_type == EdgeEvent.Type.RISING_EDGE:  # Release
            if data["press_timestamp"]:
                duration = now - data["press_timestamp"]
                self._fire(data, ButtonEvent.RELEASE)
                if not data["long_press_fired"]:
                    data["tap_count"] += 1
                    data["tap_timer_start"] = now
                else:
                    self._fire(data, ButtonEvent.LONG_PRESS_RELEASE)
                data["press_timestamp"] = None

    def _check_all_timeouts(self):
        now = time.time()
        for pin, data in self.buttons.items():
            # Handle Long Press while button is still held
            if data["press_timestamp"] and not data["long_press_fired"]:
                if (now - data["press_timestamp"]) >= self.config.buttons_long_press_time:
                    data["long_press_fired"] = True
                    data["tap_count"] = 0
                    self._fire(data, ButtonEvent.LONG_PRESS)

            # Handle Tap timeout
            if data["tap_count"] > 0 and data["tap_timer_start"]:
                if (now - data["tap_timer_start"]) > self.config.buttons_tap_time:
                    gestures = {1: ButtonEvent.TAP, 2: ButtonEvent.DOUBLE_TAP, 3: ButtonEvent.TRIPLE_TAP}
                    event = gestures.get(data["tap_count"], ButtonEvent.TRIPLE_TAP)
                    self._fire(data, event)
                    data["tap_count"] = 0
                    data["tap_timer_start"] = None
