from __future__ import annotations
import logging
import queue
import subprocess
import sys

from core.align_text import AlignText
from input.pot_event import PotEvent
from midi.midi_output_type import MidiOutputType
from storage.app_config import AppMode
from .device_event import DeviceEvent, EventType
from config import APP_MODE
from storage.app_config import AppMode
from storage.storage_manager import StorageManager
from storage.bank import Bank
from storage.preset import Preset
from controls.control import Control, ControlType
from controls.control_model import ButtonControlModel, PotControlModel
from input.button_event import ButtonEvent
from core.threading.midi_manager import MIDIManager
from wifi import WifiManager


class DataContext:
    def __init__(self, device_context: 'DeviceContext'):
        from actions import InfoAction # Local import to break circular dependency

        self.storage = StorageManager("./data", context=device_context)

        self.config = self.storage.load_app_config()
        if self.config is None:
            self.config = self._default_app_config()
            self.storage.save_app_config(self.config)
        self.bank_list = self.storage.get_bank_list()
        self.current_bank_index = self.storage.load_current_bank_index()
        self.preset_list = self.storage.get_preset_list()
        self.current_preset_index = self.storage.load_current_preset_index()
        self.max_preset_index = len(self.preset_list) - 1
        self.shift_flags: dict[int, bool] = {}
        self.settings_menu_locked: bool = False

        if self.current_bank_index is not None:
            self.bank = self.storage.load_bank(self.current_bank_index) 
        else:
            self.bank = Bank(name="Default Bank", preset_numbers=[0])
            self.current_bank_index = 0

        self._update_bank_preset_list()

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

    def set_preset(self, preset_number:int):
        if self.current_preset_index == preset_number:
            logging.info(f"Preset {preset_number} is already active.")
            return

        self.preset.exit_action.execute() # Execute exit action of current preset before switching

        self.preset = self.storage.load_preset(preset_number)
        self.storage.save_current_preset_index(preset_number)
        self.current_preset_index = preset_number
        
        self.preset.enter_action.execute() # Execute enter action of new preset after switching

    def save_app_config(self):
        self.storage.save_app_config(self.config)

    def save_current_bank(self):
        self.storage.save_bank(self.current_bank_index, self.bank)

    def set_shift_flag(self, shift_number: int, active: bool) -> None:
        self.shift_flags[shift_number] = active

    def get_shift_flag(self, shift_number: int) -> bool:
        return self.shift_flags.get(shift_number, False)

    def set_settings_menu_locked(self, locked: bool) -> None:
        self.settings_menu_locked = locked

    def get_settings_menu_locked(self) -> bool:
        return self.settings_menu_locked

    def next_preset(self, stop_at_end: bool = False):
        current_index_in_bank = 0
        preset_list = self.get_bank_preset_list()
        for i, preset in enumerate(preset_list):
            if preset["number"] == self.current_preset_index:
                current_index_in_bank = i
                break

        next_preset_index = current_index_in_bank + 1
        if next_preset_index > len(preset_list) - 1:
            if stop_at_end:
                next_preset_index = len(preset_list) - 1
            else:
                next_preset_index = 0

        next_preset = preset_list[next_preset_index]["number"]
        self.set_preset(next_preset)

    def previous_preset(self, stop_at_start: bool = False):
        current_index_in_bank = 0
        preset_list = self.get_bank_preset_list()
        for i, preset in enumerate(preset_list):
            if preset["number"] == self.current_preset_index:
                current_index_in_bank = i
                break

        previous_preset_index = current_index_in_bank - 1
        if previous_preset_index < 0:
            if stop_at_start:
                previous_preset_index = 0
            else:
                previous_preset_index = len(preset_list) - 1

        previous_preset = preset_list[previous_preset_index]["number"]
        self.set_preset(previous_preset)

    def set_bank(self, bank_number:int):
        if self.current_bank_index == bank_number:
            logging.info(f"Bank {bank_number} is already active.")
            return

        self.bank = self.storage.load_bank(bank_number)
        self.storage.save_current_bank_index(bank_number)
        self.current_bank_index = bank_number
        self._update_bank_preset_list()

    def next_bank(self, stop_at_end: bool = False):
        next_bank = self.current_bank_index + 1
        if next_bank >= len(self.bank_list):
            if stop_at_end:
                next_bank = len(self.bank_list) - 1
            else:
                next_bank = 0
        self.set_bank(next_bank)

    def previous_bank(self, stop_at_start: bool = False):
        previous_bank = self.current_bank_index - 1
        if previous_bank < 0:
            if stop_at_start:
                previous_bank = 0
            else:
                previous_bank = len(self.bank_list) - 1
        self.set_bank(previous_bank)

    def get_bank_preset_list(self) -> list[Preset]:
        return self.bank_preset_list

    def _update_bank_preset_list(self):
        self.bank_preset_list = [preset for preset in self.preset_list if preset["number"] in self.bank.preset_numbers]

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
    def __init__(self, event_queue: queue.Queue, ui_queue: queue.Queue, midi_manager: MIDIManager):
        self.data = DataContext(self)
        self.ui = UIContext(ui_queue)
        self.state = StateContext(self)
        self.event_queue = event_queue
        self.midi_manager = midi_manager
        self.wifi = WifiManager()

    def show_info(self, info: str, line: int = 1, clear_screen: bool = False, align:AlignText = AlignText.CENTER):
        """Display an informational message"""
        self.event_queue.put(DeviceEvent(EventType.INFO_MESSAGE, data={"info": info, "line": line, "clear_screen": clear_screen, "align": align}))

    def send_cc(self, output: MidiOutputType, name: str, channel:int, cc:int, value:int):
        """Send a MIDI CC message to the specified output and channel."""
        self.midi_manager.send_cc(output, name, channel, cc, value)

    def send_pc(self, output: MidiOutputType, name: str, channel:int, program:int):
        """Send a MIDI Program Change message to the specified output and channel."""
        self.midi_manager.send_pc(output, name, channel, program)

    def list_midi_outputs(self, output_type: MidiOutputType) -> list[str]:
        """List available MIDI outputs of the specified type."""
        return self.midi_manager.list_outputs(output_type)
    
    def set_preset(self, preset_number:int):
        """Set the current preset by its number."""
        self.data.set_preset(preset_number)
    
    def next_preset(self, stop_at_end: bool = False):
        """Go to the next preset, optionally stopping at the end of the list."""
        self.data.next_preset(stop_at_end=stop_at_end)

    def previous_preset(self, stop_at_start: bool = False):
        """Go to the previous preset, optionally stopping at the start of the list."""
        self.data.previous_preset(stop_at_start=stop_at_start)

    def set_bank(self, bank_number:int):
        """Set the current bank by its number."""
        self.data.set_bank(bank_number)

    def next_bank(self, stop_at_end: bool = False):
        """Go to the next bank, optionally stopping at the end of the list."""
        self.data.next_bank(stop_at_end=stop_at_end)

    def previous_bank(self, stop_at_start: bool = False):
        """Go to the previous bank, optionally stopping at the start of the list."""
        self.data.previous_bank(stop_at_start=stop_at_start)

    def get_bank_index(self) -> int:
        """Get the current bank number."""
        return self.data.current_bank_index
    
    def get_preset_index(self) -> int:
        """Get the current preset number."""
        return self.data.current_preset_index
    
    def get_current_bank(self) -> Bank:
        """Get the current bank object."""
        return self.data.bank
    
    def get_current_preset(self) -> Preset:
        """Get the current preset object."""
        return self.data.preset
    
    def save_current_preset(self):
        """Save the current preset to storage."""
        self.data.save_current_preset()

    def save_current_bank(self):
        """Save the current bank to storage."""
        self.data.save_current_bank()

    def get_preset_list(self, all: bool = True) -> list[Preset]:
        """Get the list of all presets."""
        if all:
            return self.data.preset_list
        return self.data.get_bank_preset_list()

    def set_shift_flag(self, shift_number: int, active: bool) -> None:
        self.data.set_shift_flag(shift_number, active)

    def get_shift_flag(self, shift_number: int) -> bool:
        return self.data.get_shift_flag(shift_number)

    def set_settings_menu_locked(self, locked: bool) -> None:
        self.data.set_settings_menu_locked(locked)

    def get_settings_menu_locked(self) -> bool:
        return self.data.get_settings_menu_locked()

    def shutdown_device(self) -> None:
        """Halt the host immediately (Raspberry Pi / Linux). No-op in simulation mode."""
        if APP_MODE == AppMode.SIMULATION:
            logging.info("shutdown_device: skipped (simulation mode)")
            return
        if sys.platform == "win32":
            return
        try:
            import os
            os.system('sudo systemctl poweroff')
            # subprocess.run(["/sbin/shutdown", "-h", "now"], check=False)
        except OSError as e:
            logging.warning("shutdown_device failed: %s", e)