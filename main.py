import threading
import queue
import time
import logging
import signal
from enum import Enum, auto
from abc import ABC, abstractmethod
from input import KeyboardInputManager,ButtonEvent
from MockLCD import CharLCD
from typing import List


class DeviceState(ABC):
    def __init__(self, context):
        self.context = context  # Reference to the MidiNodeDevice

    @abstractmethod
    def on_enter(self):
        """Called when switching TO this state."""
        pass

    @abstractmethod
    def handle_event(self, event):
        """Logic for input events while in this state."""
        pass

    def transition_to(self, new_state_class):
        """Helper to switch states."""
        self.context.push_state(new_state_class(self.context))

    def return_to_previous(self):
        """Helper to go back to the previous state."""
        self.context.pop_state()

class HomeState(DeviceState):
    def on_enter(self):
        self.context.clear_ui()
        self.context.write_ui("LIVE MODE\r\nPress [Select] to Setup", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:    
            self.transition_to(SettingsMenuState)

class ParamAdjustState(DeviceState):
    def __init__(self, context):
        super().__init__(context)
        self.param = 50

    def on_enter(self):
        self.context.clear_ui()
        self._refresh_display()

    def _refresh_display(self):
        self.context.write_ui(f"PARAM CONTROL\r\nLevel: {self.param}%", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self.param = min(100, self.param + 5)
            self._refresh_display()
        elif event.type == EventType.ENCODER_CCW:
            self.param = max(0, self.param - 5)
            self._refresh_display()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

class MenuState(DeviceState):
    MAX_LINES = 4

    def __init__(self, context):
        super().__init__(context)

        self.items = ["Back"]

        self.origin_x = 0
        self.origin_y = 0

        self.selected_index = 0   # index in items
        self.scroll_offset = 0    # first visible item index


    def on_enter(self):
        self.context.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Draw menu with selector.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line

            cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.context.write_ui(" " * 20, cursor_pos[0], cursor_pos[1], True)
                continue

            prefix = ">" if item_index == self.selected_index else " "
            text = f"{prefix} {self.items[item_index]}"

            # Clear line leftovers
            self.context.write_ui(text.ljust(20), cursor_pos[0], cursor_pos[1], True)

    def _down(self) -> None:
        """
        Move cursor down. Scroll if needed.
        """
        if self.selected_index >= len(self.items) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset += 1

        self._refresh_display()

    def _up(self) -> None:
        """
        Move cursor up. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected element.
        """
        return self.items[self.selected_index]

class SettingsMenuState(MenuState):
    def __init__(self, context):
        super().__init__(context)

        self.transitions = {
            "Setup Button 1": ParamAdjustState,
            "Setup Button 2": ParamAdjustState,
            "Setup Button 3": ParamAdjustState,
            "Setup Button 4": ParamAdjustState,
            "Setup Exp Pedal 1": ParamAdjustState,
            "Setup Exp Pedal 2": ParamAdjustState,
            "Delete Preset": ParamAdjustState,
            "Clone Preset": ParamAdjustState,
            "Back to Live Mode": HomeState
        }
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state_class = self.transitions[selected]
            self.transition_to(new_state_class)
        else:
            super().handle_event(event)





class EventType(Enum):
    SYSTEM_SHUTDOWN = auto()
    LCD_TEXT = auto()
    LCD_CLEAR = auto()
    ENCODER_CW = auto()
    ENCODER_CCW = auto()
    ENCODER_SELECT = auto()

class DeviceEvent:
    def __init__(self, event_type: EventType, data=None):
        self.type = event_type
        self.data = data





class DisplayProvider(ABC):
    @abstractmethod
    def clear(self):
        pass
    
    @abstractmethod
    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        pass

class MockLCD(DisplayProvider):
    def clear(self):
        self.lcd.clear()

    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        if set_pos:
            self.lcd.cursor_pos = (x, y)
        self.lcd.write_string(text)






class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.queue = event_queue
        self.shutdown = shutdown_event
        self.input_handler = KeyboardInputManager()
        
        def encoder_callback(direction):
            if direction == 1:
                self.queue.put(DeviceEvent(EventType.ENCODER_CW))
            else:
                self.queue.put(DeviceEvent(EventType.ENCODER_CCW))

        self.input_handler.add_encoder('down', "up", encoder_callback)
        self.input_handler.add_button('enter', {ButtonEvent.PRESS: lambda: self.queue.put(DeviceEvent(EventType.ENCODER_SELECT))})

    def run(self):
        logging.info("Input Thread Started")

        self.input_handler.start(self.shutdown.is_set)

        logging.info("Input Thread Shutting Down")

class UIManager(threading.Thread):
    """Consumes UI events and controls the LCD hardware."""
    def __init__(self, ui_queue: queue.Queue, display: DisplayProvider, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.queue = ui_queue
        self.display = display
        self.shutdown = shutdown_event
        self.current_state = {"line1": "System Ready", "line2": "Waiting..."}
        self.out_data = {"x": 0, "y": 0, "set_pos": False, "str": ""}

    def run(self):
        logging.info("UI Thread Started")
        while not self.shutdown.is_set():
            try:
                # Block for 0.5s to keep the loop responsive to shutdown
                event = self.queue.get(timeout=0.5)
                
                if event.type == EventType.LCD_TEXT:
                    self.out_data.update(event.data)
                    self.display.write_string(self.out_data['str'], self.out_data['x'], self.out_data['y'], self.out_data['set_pos'])
                elif event.type == EventType.LCD_CLEAR:
                    self.display.clear()

                self.queue.task_done()
            except queue.Empty:
                continue
        
        self.display.clear()
        logging.info("UI Thread Shutting Down")

# --- 4. The Main Controller (The Brain) ---

class MidiNodeDevice:
    def __init__(self):
        # logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')
        logging.basicConfig(level=logging.ERROR, format='%(threadName)s: %(message)s')
        
        self.event_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()

        # Initialize Hardware
        self.lcd = MockLCD()
        self.lcd.clear()

        # Initialize Threads
        self.input_thread = InputManager(self.event_queue, self.shutdown_event)
        self.ui_thread = UIManager(self.ui_queue, self.lcd, self.shutdown_event)
        
        # Start in the Home State
        self.state_stack = []
        self.push_state(HomeState(self))

    
    # State Management

    @property
    def current_state(self):
        return self.state_stack[-1] if self.state_stack else None

    def push_state(self, new_state: DeviceState):
        """Go deeper into a menu."""
        logging.info(f"Transitioning to {type(new_state).__name__}")
        self.state_stack.append(new_state)
        new_state.on_enter()

    def pop_state(self):
        """Go back to the previous menu."""
        if len(self.state_stack) > 1:
            self.state_stack.pop()
            logging.info(f"Returning to {type(self.current_state).__name__}")
            self.current_state.on_enter()        


    # UI Helpers

    def write_ui(self, text, x=0, y=0, set_pos=False):
        """Helper to write text to the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_TEXT, data={"x": x, "y": y, "str": text, "set_pos": set_pos}))

    def clear_ui(self):
        """Helper to clear the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_CLEAR))

    
    # Main Loop

    def start(self):
        self.input_thread.start()
        self.ui_thread.start()
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.stop()

    def _main_loop(self):
        while not self.shutdown_event.is_set():
            try:
                event = self.event_queue.get(timeout=0.5)
                self.current_state.handle_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        logging.info("Stopping MIDI Node...")
        self.shutdown_event.set()
        self.input_thread.join()
        self.ui_thread.join()
        logging.info("MIDI Node Stopped Cleanly")

if __name__ == "__main__":
    device = MidiNodeDevice()
    device.start()
