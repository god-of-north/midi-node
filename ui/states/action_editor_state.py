from enum import Enum

from actions.action import ActionParam
from actions.param_selector import CustomParamSelectorRegistry
from ui.states.menu_selector_state import MenuSelectorState
from .menu_state import MenuState
from .dummy_state import DummyState
from .action_param_selector_states import ActionParamBoolSelectorState, ActionParamIntSelectorState, ActionParamStringSelectorState, ActionParamEnumSelectorState
from .boolean_selector_state import BooleanWithCallbackState
from .action_param_list_editor_state import ActionParamListEditorState
from core.device_event import EventType
from actions import Action

class ActionEditorState(MenuState):
    def __init__(self, context, action: Action, delete_callback=None):
        super().__init__(context)
        self.action = action
        self.delete_callback = delete_callback

    def on_enter(self):
        if not self.action:
            self.return_to_previous()
            return

        params = self.action.params

        self.transitions = {}
        for key, param in params.items():
            transition = {"class": DummyState}
            display_value = param.value
            if(param.custom_selector):
                # TODO: add custom value selector support
                selector = CustomParamSelectorRegistry.get_selector(param.custom_selector)
                if selector:
                    transition = {"class": MenuSelectorState, "args": {"param":param, "items":selector.get_list(params), 
                                                                       "callback": self._update_param_callback_factory(param)}}
            elif param.param_type == bool:
                transition = {"class": ActionParamBoolSelectorState, "args": {"param":param}}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param":param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param":param}}
            elif issubclass(param.param_type, Enum):
                display_value = param.value.name if param.value else "None"
                transition = {"class": ActionParamEnumSelectorState, "args": {"param":param}}
            elif param.param_type == list:
                display_value = "[]"
                transition = {"class": ActionParamListEditorState, "args": {"param":param}}

            self.transitions[f"{key.capitalize()}: {display_value}"] = transition
        self.transitions["Delete"] = {"class": BooleanWithCallbackState, "args": {"value": False, "callback": self._delete, "true_value": "Confirm Delete", "false_value": "Cancel"}}
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

    def _delete(self, confirmed: bool):
        if confirmed:
            self.delete_callback()
            self.action = None

    def _update_param_callback_factory(self, param: ActionParam):
        return lambda selected: self._update_param(param, selected)
    
    def _update_param(self, param: ActionParam, selected):
        if param.param_type == int:
            param.value = int(selected)
        elif param.param_type == bool:
            param.value = selected == "True"
        elif issubclass(param.param_type, Enum):
            param.value = param.param_type[selected]
        else:
            param.value = selected
