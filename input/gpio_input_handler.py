import logging
import gpiod
from gpiod.line import Direction, Edge, Bias, Value
from gpiod import EdgeEvent  # Added for correct event type comparison
from datetime import timedelta
import time
from enum import Enum, auto

from .button_event import ButtonEvent
from .input_handler import InputHandler


# class ButtonEvent(Enum):
#     PRESS = auto()
#     RELEASE = auto()
#     TAP = auto()
#     DOUBLE_TAP = auto()
#     TRIPLE_TAP = auto()
#     LONG_PRESS = auto()

class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin, on_rotate):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.on_rotate = on_rotate 

    def process(self, event, chip_request):
        # Only process on the FALLING edge of the CLK pin.
        if event.event_type != EdgeEvent.Type.FALLING_EDGE:
            return

        dt_val = chip_request.get_value(self.dt_pin)
        direction = 1 if dt_val == Value.ACTIVE else -1
        self.on_rotate(direction)

class GPIOInputHandler(InputHandler):
    def __init__(self, config):
        self.chip_path = "/dev/gpiochip0"
        self.buttons = {}
        self.encoders = {}
        self.all_pins = []
        self.config = config

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

    def _fire(self, pin_data, event_type: ButtonEvent):
        logging.info(f"Firing event {event_type}")

        action = pin_data["actions"].get(event_type)
        if action: 
            logging.info(f"Executing action for event {event_type}")
            action()
        else:
            logging.info(f"No action defined for event {event_type}")

    def start(self, shutdown_event=None):
        configs = {}
        for pin in self.all_pins:
            # We use Edge.BOTH for everything, but filter inside the logic
            configs[pin] = gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
                edge_detection=Edge.BOTH,
                debounce_period=timedelta(milliseconds=5) 
            )

        with gpiod.request_lines(self.chip_path, consumer="multi_ctrl", config=configs) as request:
            while not (shutdown_event and shutdown_event.is_set()):
                # Wait for events with a short timeout to allow check_all_timeouts to run
                if request.wait_edge_events(timedelta(milliseconds=10)):
                    for event in request.read_edge_events():
                        pin = event.line_offset
                        
                        if pin in self.encoders:
                            self.encoders[pin].process(event, request)
                        
                        elif pin in self.buttons:
                            self._handle_hardware_event(event)
                
                self._check_all_timeouts()

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

if __name__ == "__main__":
    handler = GPIOInputHandler()
    
    def encoder_callback(direction):
        print(f"Rotation: {'CW' if direction == 1 else 'CCW'}")

    handler.add_encoder(clk_pin=17, dt_pin=18, callback=encoder_callback)
    handler.add_button(pin=27, actions={
        ButtonEvent.TAP: lambda: print("Button: Tap"),
        ButtonEvent.DOUBLE_TAP: lambda: print("Button: Double Tap"),
        ButtonEvent.LONG_PRESS: lambda: print("Button: Long Press"),
        ButtonEvent.PRESS: lambda: print("Button: Press"),
        ButtonEvent.RELEASE: lambda: print("Button: Release"),
        ButtonEvent.TRIPLE_TAP: lambda: print("Button: Triple Tap"),
    })

    print("Listening... Press Ctrl+C to stop.")
    handler.start()
