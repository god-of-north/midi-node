from .menu_state import MenuState
from .control_settings_menu_state import ControlSettingsMenuState
from .save_preset_state import SavePresetState
from .dummy_state import DummyState
from core.device_event import EventType
from controls import Control

class SettingsMenuState(MenuState):
    def __init__(self, context):
        super().__init__(context)

        self.transitions = {
            "Setup Button 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_1}},
            "Setup Button 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_2}},
            "Setup Button 3": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_3}},
            "Setup Button 4": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_4}},
            "Setup Exp Pedal 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_1}},
            "Setup Exp Pedal 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_2}},
            "Save Preset": {"class": SavePresetState},
            "Clone Preset": {"class": DummyState},
            "Delete Preset": {"class": DummyState},
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
