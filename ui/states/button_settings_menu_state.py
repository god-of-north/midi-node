from enum import Enum
from .menu_state import MenuState
from .dummy_state import DummyState
from .action_param_selector_states import ActionParamBoolSelectorState, ActionParamIntSelectorState, ActionParamStringSelectorState, ActionParamEnumSelectorState
from .action_param_list_editor_state import ActionParamListEditorState
from .action_selector_state import ActionSelectorState
from core.device_event import EventType
from actions import Action
from controls import Control

class ButtonSettingsMenuState(MenuState):
    def __init__(self, context, control_id: Control, control_event: Enum):
        super().__init__(context)
        self.control_id = control_id
        self.control_event = control_event

    def on_enter(self):
        if not self.control_id:
            self.return_to_previous()
            return

        control = self.context.data.preset.controls.get(self.control_id, None)
        if not control:
            self.return_to_previous()
            return
        
        action: Action = control.actions.get(self.control_event, None)
        if not action:
            self.return_to_previous()
            return

        params = action.params

        self.transitions = {}
        self.transitions["Type: "+getattr(action, "TITLE", "Unknown")] = {"class": ActionSelectorState, "args": {"control_id": self.control_id, "control_event": self.control_event}}
        for key, param in params.items():
            transition = {"class": DummyState}
            display_value = param.value
            if param.param_type == bool:
                transition = {"class": ActionParamBoolSelectorState, "args": {"param":param}}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param":param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param":param}}
            elif issubclass(param.param_type, Enum):
                transition = {"class": ActionParamEnumSelectorState, "args": {"param":param}}
            elif param.param_type == list:
                display_value = "[]"
                transition = {"class": ActionParamListEditorState, "args": {"param":param}}

            self.transitions[f"{key.capitalize()}: {display_value}"] = transition
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
