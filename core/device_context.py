from __future__ import annotations
import queue
import logging

from input.pot_event import PotEvent
from midi.midi_output_type import MidiOutputType
from midi.midi_router import MidiRouter
from storage.app_config import AppMode
from .device_event import DeviceEvent, EventType
from storage.storage_manager import StorageManager
from storage.bank import Bank
from storage.preset import Preset
from controls.control import Control, ControlType
from controls.control_model import ButtonControlModel, PotControlModel
from input.button_event import ButtonEvent
from actions import InfoAction

class DataContext:
    def __init__(self, device_context: 'DeviceContext'):
        self.storage = StorageManager("./data", context=device_context)

        self.config = self.storage.load_app_config()
        if self.config is None:
            self.config = self._default_app_config()
            self.storage.save_app_config(self.config)
        self.bank_list = self.storage.get_bank_list()
        self.current_bank_index = self.storage.load_current_bank_index()
        self.preset_list = self.storage.get_preset_list()
        self.current_preset_index = self.storage.load_current_preset_index()
        
        if self.current_bank_index is not None:
            self.bank = self.storage.load_bank(self.current_bank_index) 
        else:
            self.bank = Bank(name="Default Bank", preset_numbers=[0])
            self.current_bank_index = 0

        if self.current_preset_index is not None:
            self.preset = self.storage.load_preset(self.current_preset_index) 
        else:
            controls = {
                Control.BUTTON_1: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 1 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 1 Released", context=device_context),
                }),
                Control.BUTTON_2: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 2 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 2 Released", context=device_context),
                }),
                Control.BUTTON_3: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 3 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 3 Released", context=device_context),
                }),
                Control.BUTTON_4: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 4 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 4 Released", context=device_context),
                }),
                Control.EXP_PEDAL_1: PotControlModel(control_type=ControlType.POTENTIOMETER, actions={
                    PotEvent.CHANGE_VALUE: InfoAction(info="Exp Pedal 1 Active", context=device_context),
                    PotEvent.ON_MIN: InfoAction(info="Exp Pedal 1 Inactive", context=device_context),
                }),
                Control.EXP_PEDAL_2: PotControlModel(control_type=ControlType.POTENTIOMETER, actions={
                    PotEvent.CHANGE_VALUE: InfoAction(info="Exp Pedal 2 Active", context=device_context),
                    PotEvent.ON_MIN: InfoAction(info="Exp Pedal 2 Inactive", context=device_context),
                }),
            }

            self.preset = Preset(name="Default Preset", controls=controls)
            self.current_preset_index = 0

    def save_current_preset(self):
        self.storage.save_preset(self.current_preset_index, self.preset)
    
    def _default_app_config(self) -> 'AppConfig':
        from storage.app_config import AppConfig
        return AppConfig()
    
class UIContext:
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def write_ui(self, text, x=0, y=0, set_pos=False):
        """Helper to write text to the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_TEXT, data={"x": x, "y": y, "str": text, "set_pos": set_pos}))

    def clear_ui(self):
        """Helper to clear the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_CLEAR))

class StateContext:
    def __init__(self, device_context: 'DeviceContext'):
        self.context = device_context
        self._state_stack = []

    @property
    def current_state(self) -> 'DeviceState':
        return self._state_stack[-1] if self._state_stack else None

    def push_state(self, new_state: 'DeviceState'):
        """Go deeper into a menu."""
        logging.info(f"Transitioning to {type(new_state).__name__}")
        self._state_stack.append(new_state)
        new_state.on_enter()

    def pop_state(self, deep: int = 1):
        """Go back to the previous menu."""
        for _ in range(deep):
            if len(self._state_stack) > 1:
                self._state_stack.pop()

        logging.info(f"Returning to {type(self.current_state).__name__}")
        self.current_state.on_enter()

class DeviceContext:
    def __init__(self, event_queue: queue.Queue, ui_queue: queue.Queue, midi_router: MidiRouter):
        self.data = DataContext(self)
        self.ui = UIContext(ui_queue)
        self.state = StateContext(self)
        self.event_queue = event_queue
        self.midi_router = midi_router

    def show_info(self, info: str):
        """Display an informational message"""
        self.event_queue.put(DeviceEvent(EventType.INFO_MESSAGE, data={"info": info}))

    def send_cc(self, output: MidiOutputType, name: str, channel:int, cc:int, value:int):
        """Send a MIDI CC message to the specified output and channel."""
        self.midi_router.send_cc(output, name, channel, cc, value)

    def send_pc(self, output: MidiOutputType, name: str, channel:int, program:int):
        """Send a MIDI Program Change message to the specified output and channel."""
        self.midi_router.send_pc(output, name, channel, program)

    def list_midi_outputs(self, output_type: MidiOutputType) -> list[str]:
        """List available MIDI outputs of the specified type."""
        return self.midi_router.list_outputs(output_type)