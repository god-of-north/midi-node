from .menu_state import MenuState
from .button_settings_menu_state import ButtonSettingsMenuState
from core.device_event import EventType
from controls import Control

class ControlSettingsMenuState(MenuState):
    def __init__(self, context, control_id:Control):
        super().__init__(context)
        self.control_id = control_id
    
    def on_enter(self):
        control = self.context.data.preset.controls[self.control_id]

        self.transitions = {}
        for control_event in control.actions.keys():
            self.transitions[f"Setup {control_event.name}"] = {"class": ButtonSettingsMenuState, "args": {"control_id": self.control_id, "control_event": control_event}}
        self.transitions["Back"] = None

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
