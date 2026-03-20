import gpiod
from gpiod.line import Direction, Edge, Bias
from datetime import timedelta
import time
from enum import Enum, auto

from input.input_handler import InputHandler


class ButtonEvent(Enum):
    PRESS = auto()
    RELEASE = auto()
    TAP = auto()
    DOUBLE_TAP = auto()
    TRIPLE_TAP = auto()
    LONG_PRESS = auto()


class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin, on_rotate):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.on_rotate = on_rotate # Callback: lambda direction: ...
        self.last_clk_value = 1

    def process(self, event, chip_request):
        # We only trigger logic on the CLK pin changing
        if event.line_offset == self.clk_pin:
            # Get current values of both pins
            # Note: request.get_values is very fast in gpiod v2
            vals = chip_request.get_values([self.clk_pin, self.dt_pin])
            clk_val = vals[0]
            dt_val = vals[1]

            if clk_val != self.last_clk_value: # Edge detected
                if dt_val != clk_val:
                    self.on_rotate(1)  # Clockwise
                else:
                    self.on_rotate(-1) # Counter-clockwise
                self.last_clk_value = clk_val


class GPIOInputHandler(InputHandler):
    def __init__(self, debounce_ms=30):
        self.chip_path = "/dev/gpiochip0"
        self.debounce_ms = debounce_ms
        self.buttons = {}   # pin -> GestureButton logic
        self.encoders = {}  # clk_pin -> RotaryEncoder logic
        self.all_pins = []        

    def add_button(self, pin, actions, tap_time=0.25, long_press=0.6):
        """Register a button without starting the loop yet."""
        self.buttons[pin] = {
            "actions": actions,
            "tap_time": tap_time,
            "long_press_time": long_press,
            "press_timestamp": None,
            "tap_count": 0,
            "tap_timer_start": None,
            "long_press_fired": False
        }
        self.all_pins.append(pin)

    def add_encoder(self, clk_pin, dt_pin, callback):
        encoder = RotaryEncoder(clk_pin, dt_pin, callback)
        self.encoders[clk_pin] = encoder
        if clk_pin not in self.all_pins: self.all_pins.append(clk_pin)
        if dt_pin not in self.all_pins: self.all_pins.append(dt_pin)

    def _fire(self, pin_data, event_type: ButtonEvent):
        action = pin_data["actions"].get(event_type)
        if action:
            action()

    def start(self):
        # Configure ALL pins (Buttons and Encoder pins)
        configs = {}
        for pin in self.all_pins:
            configs[pin] = gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
                edge_detection=Edge.BOTH,
                # Encoder pins need VERY low debounce or NONE to catch fast spins
                debounce_period=timedelta(milliseconds=2 if pin in self.encoders else 30)
            )

        with gpiod.request_lines("/dev/gpiochip0", consumer="multi_ctrl", config=configs) as request:
            while True:
                if request.wait_edge_events(timedelta(milliseconds=50)):
                    for event in request.read_edge_events():
                        # Dispatch to Encoder
                        if event.line_offset in self.encoders:
                            self.encoders[event.line_offset].process(event, request)
                        
                        # Dispatch to Button logic
                        elif event.line_offset in self.buttons:
                            self._handle_hardware_event(event)
                            pass
                
                # Check timeouts for all buttons (Long press / Tap release)
                self._check_all_timeouts()

    def _handle_hardware_event(self, event):
        pin = event.line_offset
        data = self.buttons[pin]
        now = time.time()

        if event.event_type == Edge.FALLING: # Press
            data["press_timestamp"] = now
            data["long_press_fired"] = False
            self._fire(data, ButtonEvent.PRESS)
        
        elif event.event_type == Edge.RISING: # Release
            if data["press_timestamp"]:
                duration = now - data["press_timestamp"]
                self._fire(data, ButtonEvent.RELEASE)
                if duration < data["long_press_time"]:
                    data["tap_count"] += 1
                    data["tap_timer_start"] = now
                data["press_timestamp"] = None

    def _check_all_timeouts(self):
        now = time.time()
        for pin, data in self.buttons.items():
            # Long Press logic
            if data["press_timestamp"] and not data["long_press_fired"]:
                if (now - data["press_timestamp"]) >= data["long_press_time"]:
                    data["long_press_fired"] = True
                    data["tap_count"] = 0
                    self._fire(data, ButtonEvent.LONG_PRESS)

            # Tap/Multi-tap logic
            if data["tap_count"] > 0 and data["tap_timer_start"]:
                if (now - data["tap_timer_start"]) > data["tap_time"]:
                    gestures = {1: ButtonEvent.TAP, 2: ButtonEvent.DOUBLE_TAP, 3: ButtonEvent.TRIPLE_TAP}
                    # Trigger the specific multi-tap or default to TRIPLE_TAP
                    event = gestures.get(data["tap_count"], ButtonEvent.TRIPLE_TAP)
                    self._fire(data, event)
                    data["tap_count"] = 0
                    data["tap_timer_start"] = None

