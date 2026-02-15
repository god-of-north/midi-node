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


ACTION_REGISTRY = {}

def register_action(cls):
    action_type = getattr(cls, 'TYPE', cls.__name__)
    title = getattr(cls, 'TITLE', action_type)

    ACTION_REGISTRY[action_type] = {
        "class": cls,
        "title": title,
    }
    return cls

class ActionParam:
    def __init__(self, name: str, param_type: type, value, default=None, options:dict={}):
        self.name = name
        self.param_type = param_type
        self.value = value
        self.default = default
        self.options = options or {}

class Action:
    TYPE = "base"
    TITLE = "Base Action"

    def __init__(self, context):
        self.context = context  # Reference to the MidiNodeDevice

        self.params: dict[str, ActionParam] = {}

    def execute(self):
        raise NotImplementedError

    def to_dict(self):
        return {
            "type": self.TYPE,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@register_action
class InfoAction(Action):
    TYPE = "info"
    TITLE = "Show Info"

    def __init__(self, info:str, **kwargs):
        super().__init__(**kwargs)
        self.params["info"] = ActionParam("info", str, info)

    def execute(self):
        self.context.show_info(self.params["info"].value)

    def to_dict(self):
        data = super().to_dict()
        return {**data, "info": self.params["info"].value}

@register_action
class CCAction(Action):
    TYPE = "cc"
    TITLE = "Send CC"

    def __init__(self, cc:int, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=127, options={"min_value":0, "max_value":127, "header":"Control Change"})

    def execute(self):
        self.context.show_info(self.params["cc"].value)

    def to_dict(self):
        data = super().to_dict()
        return {**data, "cc": self.params["cc"].value}

@register_action
class PCAction(Action):
    TYPE = "pc"
    TITLE = "Send PC"

    def __init__(self, pc:int, **kwargs):
        super().__init__(**kwargs)
        self.params["pc"] = ActionParam("pc", int, pc, default=0, options={"min_value":0, "max_value":127, "header":"Program Change"})

    def execute(self):
        self.context.show_info(self.params["pc"].value)

    def to_dict(self):
        data = super().to_dict()
        return {**data, "pc": self.params["pc"].value}


class Controls(Enum):
    BUTTON_1 = auto()
    BUTTON_2 = auto()
    BUTTON_3 = auto()
    BUTTON_4 = auto()
    EXP_PEDAL_1 = auto()
    EXP_PEDAL_2 = auto()






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

    def transition_to(self, new_state_class, **kwargs):
        """Helper to switch states."""
        self.context.push_state(new_state_class(self.context, **kwargs))

    def return_to_previous(self):
        """Helper to go back to the previous state."""
        self.context.pop_state()

class HomeState(DeviceState):
    def on_enter(self):
        self.context.clear_ui()
        self.context.write_ui("LIVE MODE\r\n\r\n\r\nPress [Select] to Setup", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.transition_to(SettingsMenuState)
        elif event.type == EventType.INFO_MESSAGE:
            info = event.data.get("info", "")
            self.context.write_ui(f"[{info}]".center(20), 0, 1, True)

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

class DummyState(DeviceState):
    def on_enter(self):
        self.context.clear_ui()
        self.context.write_ui("DUMMY STATE\r\nNo Actions", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

class IntNumberSelectorState(DeviceState):
    LINE_WIDTH = 20

    def __init__(
        self,
        context,
        min_value: int = 0,
        max_value: int = 100,
        value: int = 0,
        header: str = "Integer Selector"
    ):
        super().__init__(context)

        self.min_value = min_value
        self.max_value = max_value
        self.header = header

        self.origin_x = 0
        self.origin_y = 0

        self.value = value

        # Pre-calc width for zero-padded numbers (optional but nice)
        self._num_width = len(str(max(abs(min_value), abs(max_value))))


    def on_enter(self):
        self.context.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Draw header and current integer value.
        """
        # Header
        self.context.write_ui(self.header.ljust(self.LINE_WIDTH), self.origin_x, self.origin_y, True)

        # Value line
        formatted = self._format_value(self.value)
        value_line = f"< {formatted} >".center(self.LINE_WIDTH)

        self.context.write_ui(value_line[:self.LINE_WIDTH], self.origin_x, self.origin_y + 1, True)

        # Clear remaining lines
        for i in range(2, 4):
            self.context.write_ui(" " * self.LINE_WIDTH, self.origin_x, self.origin_y + i, True)

    def _next(self) -> None:
        """
        Increment value by 1 (cyclic).
        """
        if self.value >= self.max_value:
            self.value = self.min_value
        else:
            self.value += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Decrement value by 1 (cyclic).
        """
        if self.value <= self.min_value:
            self.value = self.max_value
        else:
            self.value -= 1

        self._refresh_display()

    def get_value(self) -> int:
        """
        Return current integer value.
        """
        return self.value

    def _format_value(self, value: int) -> str:
        """
        Format value for display (zero-padded).
        """
        sign = "-" if value < 0 else ""
        return f"{sign}{abs(value):0{self._num_width}d}"

class ActionParamIntSelectorState(IntNumberSelectorState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != int:
            raise ValueError(f"Parameter '{param.name}' is not a valid integer parameter.")

        super().__init__(
            context,
            min_value=param.options.get("min_value", 0),
            max_value=param.options.get("max_value", 100),
            value=param.value,
            header=param.options.get("header", f"Set {param.name.capitalize()}:")
        )
        self.param = param

    def return_to_previous(self):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()   

class StringCreatorState(DeviceState):
    VISIBLE_WIDTH = 20

    def __init__(
        self,
        context,
        value: str = "",
        characters: str = "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _",
        header: str = "Create String:",
        centered: bool = True,
    ):
        super().__init__(context)

        self.origin_x = 0
        self.origin_y = 0
        self.centered = centered
        self.characters: List[str] = list("√←" + characters)
        self.selected_index = 0
        self.scroll_offset = 0
        self.header = header

        self.chars: List[str] = list(value)

    def on_enter(self):
        self.context.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            if self._get_selected() == "√":
                self.return_to_previous()
            elif self._get_selected() == "←":
                self._backspace()
            else:
                self._add_char()

    def _refresh_display(self) -> None:
        # Header
        self.context.write_ui(self.header.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y, True)

        # Characters line
        visible_chars = self._get_visible_chars()
        self.context.write_ui("".join(visible_chars).ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 1, True)

        # Cursor line
        cursor_x = self.selected_index - self.scroll_offset
        cursor_line = " " * cursor_x + "^"
        self.context.write_ui(cursor_line.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 2, True)

        # Draw the current string.
        current_string = "".join(self.chars)

        if self.centered:
            self.context.write_ui(current_string.center(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)
        else:
            self.context.write_ui(current_string.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)

    def _add_char(self) -> None:
        """
        Add currently selected character to the string.
        """
        selected_char = self._get_selected()
        self.chars.append(selected_char)
        self._refresh_display()

    def _backspace(self) -> None:
        """
        Remove last character from the string.
        """
        if not self.chars:
            return

        self.chars.pop()
        self._refresh_display()

    def _get_string(self) -> str:
        """
        Return the current string.
        """
        return "".join(self.chars)
    
    def _next(self) -> None:
        """
        Move cursor right. Scroll if needed.
        """
        if self.selected_index >= len(self.characters) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.VISIBLE_WIDTH:
            self.scroll_offset += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Move cursor left. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected character.
        """
        return self.characters[self.selected_index]

    def _get_visible_chars(self) -> List[str]:
        end = self.scroll_offset + self.VISIBLE_WIDTH
        return self.characters[self.scroll_offset:end]

class ActionParamStringSelectorState(StringCreatorState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != str:
            raise ValueError(f"Parameter '{param.name}' is not a valid string parameter.")

        super().__init__(
            context,
            value=param.value,
            characters=param.options.get("characters", "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _"),
            header=param.options.get("header", f"Set {param.name.capitalize()}:"),
            centered=param.options.get("centered", True),
        )
        self.param = param

    def return_to_previous(self):
        # Update the action parameter before returning
        self.param.value = self._get_string()
        super().return_to_previous()

class ButtonSettingsMenuState(MenuState):
    def __init__(self, context, button_id):
        super().__init__(context)
        self.button_id = button_id

    def on_enter(self):
        action = self.context.actions.get(self.button_id, None)
        if not action:
            # TODO transition to action creation page
            self.return_to_previous()

        params = action.params

        self.transitions = {}
        self.transitions["Type: "+getattr(action, "TITLE", "Unknown")] = transition = {"class": DummyState}
        for key, param in params.items():
            transition = {"class": DummyState}
            if param.param_type == bool:
                transition = {"class": DummyState}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param":param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param":param}}
            elif param.param_type == Enum:
                transition = {"class": DummyState}

            self.transitions[f"{key.capitalize()}: {param.value}"] = transition
        self.transitions["Delete"] = transition = {"class": DummyState}
        self.transitions["Back to Settings"] = None
        self.items = list(self.transitions.keys())

        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

class SettingsMenuState(MenuState):
    def __init__(self, context):
        super().__init__(context)

        self.transitions = {
            "Setup Button 1": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.BUTTON_1}},
            "Setup Button 2": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.BUTTON_2}},
            "Setup Button 3": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.BUTTON_3}},
            "Setup Button 4": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.BUTTON_4}},
            "Setup Exp Pedal 1": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.EXP_PEDAL_1}},
            "Setup Exp Pedal 2": {"class": ButtonSettingsMenuState, "args": {"button_id": Controls.EXP_PEDAL_2}},
            "Delete Preset": {"class": DummyState},
            "Clone Preset": {"class": DummyState},
            "Back to Live Mode": None
        }
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)





class EventType(Enum):
    SYSTEM_SHUTDOWN = auto()
    LCD_TEXT = auto()
    LCD_CLEAR = auto()
    ENCODER_CW = auto()
    ENCODER_CCW = auto()
    ENCODER_SELECT = auto()
    INFO_MESSAGE = auto()

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
    def __init__(self):
        self.lcd = CharLCD()

    def clear(self):
        self.lcd.clear()

    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        if set_pos:
            self.lcd.cursor_pos = (x, y)
        self.lcd.write_string(text)






class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event, actions: dict[Controls, Action]):
        super().__init__(daemon=True)
        self.queue = event_queue
        self.shutdown = shutdown_event
        self.input_handler = KeyboardInputManager()
        self.actions = actions

        def encoder_callback(direction):
            if direction == 1:
                self.queue.put(DeviceEvent(EventType.ENCODER_CW))
            else:
                self.queue.put(DeviceEvent(EventType.ENCODER_CCW))

        self.input_handler.add_encoder('down', "up", encoder_callback)
        self.input_handler.add_button('enter', {ButtonEvent.PRESS: lambda: self.queue.put(DeviceEvent(EventType.ENCODER_SELECT))})

        key_map = {
            Controls.BUTTON_1: '1',
            Controls.BUTTON_2: '2',
            Controls.BUTTON_3: '3',
            Controls.BUTTON_4: '4',
        }
        for control, action in actions.items():
            if control in key_map.keys():
                self.input_handler.add_button(key_map[control], {ButtonEvent.PRESS: (lambda c=control: actions[c].execute())})

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
        
        # Event Queues and Shutdown Event
        self.event_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()

        self.actions = {
            Controls.BUTTON_1: InfoAction(info="Button 1 Pressed", context=self),
            Controls.BUTTON_2: InfoAction(info="Button 2 Pressed", context=self),
            Controls.BUTTON_3: InfoAction(info="Button 3 Pressed", context=self),
            Controls.BUTTON_4: CCAction(cc=100, context=self),
            Controls.EXP_PEDAL_1: InfoAction(info="Exp Pedal 1 Act", context=self),
            Controls.EXP_PEDAL_2: InfoAction(info="Exp Pedal 2 Act", context=self),
        }

        # Initialize Hardware
        self.lcd = MockLCD()
        self.lcd.clear()

        # Initialize Threads
        self.input_thread = InputManager(self.event_queue, self.shutdown_event, self.actions)
        self.ui_thread = UIManager(self.ui_queue, self.lcd, self.shutdown_event)
        
        # Start in the Home State
        self.state_stack = []
        self.push_state(HomeState(self))

    
    # Action Helpers

    def show_info(self, info: str):
        """Display an informational message"""
        self.event_queue.put(DeviceEvent(EventType.INFO_MESSAGE, data={"info": info}))


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
