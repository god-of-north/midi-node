from ui.states.menu_selector_state import MenuSelectorState
from ui.states.save_bank_state import SaveBankState
from ui.states.system_config_state import SystemConfigState
from .menu_state import MenuState
from .control_settings_menu_state import ControlSettingsMenuState
from .save_preset_state import SavePresetState
from .error_state import ErrorState
from core.device_event import EventType
from controls import Control

class SettingsMenuState(MenuState):
    def __init__(self, context):
        super().__init__(context)

        self.transitions = {
            "Back to Live Mode ": None,
            "Select Preset": {"class": MenuSelectorState, "args": {
                "items": [f'{preset["number"]:03d}:{preset["name"]}' for preset in self.context.data.preset_list],
                "param": f'{self.context.data.current_preset_index:03d}:{self.context.data.preset.name}',
                "callback": self._select_preset_callback}},
            "Select Bank": {"class": MenuSelectorState, "args": {
                "items": [f'{bank["number"]:02d}:{bank["name"]}' for bank in self.context.data.bank_list],
                "param": f'{self.context.data.current_bank_index:02d}:{self.context.data.bank.name}',
                "callback": self._select_bank_callback}},
            "Save Preset": {"class": SavePresetState},
            "Save Bank": {"class": SaveBankState},
            "Setup Button 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_1}},
            "Setup Button 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_2}},
            "Setup Button 3": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_3}},
            "Setup Button 4": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_4}},
            "Setup Exp Pedal 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_1}},
            "Setup Exp Pedal 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_2}},
            "System Config": {"class": SystemConfigState},
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

    def _select_preset_callback(self, selected):
        preset_number = int(selected.split(":")[0])
        self.context.set_preset(preset_number)
        self.return_to_previous()

    def _select_bank_callback(self, selected):
        bank_number = int(selected.split(":")[0])
        self.context.set_bank(bank_number)
        self.return_to_previous()