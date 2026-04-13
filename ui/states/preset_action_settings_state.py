from enum import Enum

from actions.action import ActionParam
from actions.param_selector import CustomParamSelectorRegistry
from ui.states.menu_selector_state import MenuSelectorState
from .menu_state import MenuState
from .error_state import ErrorState
from .action_param_selector_states import (
    ActionParamBoolSelectorState,
    ActionParamIntSelectorState,
    ActionParamStringSelectorState,
    ActionParamEnumSelectorState,
)
from .action_param_list_editor_state import ActionParamListEditorState
from .preset_action_selector_state import PresetActionSelectorState
from core.device_event import EventType
from actions import Action


class PresetActionSettingsState(MenuState):
    """
    Settings menu for editing Preset Enter/Exit actions.
    Very similar to ButtonSettingsMenuState but operates on Preset.enter_action / exit_action.
    """

    def __init__(self, context, is_enter: bool):
        super().__init__(context)
        self.is_enter = is_enter

    def on_enter(self):
        preset = self.context.get_current_preset()
        action: Action = preset.enter_action if self.is_enter else preset.exit_action
        if not action:
            self.return_to_previous()
            return

        params = action.params

        self.transitions = {}
        title = getattr(action, "TITLE", "Unknown")
        self.transitions[f"Type: {title}"] = {
            "class": PresetActionSelectorState,
            "args": {"is_enter": self.is_enter},
        }

        for key, param in params.items():
            transition = {"class": ErrorState}
            display_value = param.value

            if param.custom_selector:
                selector = CustomParamSelectorRegistry.get_selector(param.custom_selector)
                if selector:
                    transition = {
                        "class": MenuSelectorState,
                        "args": {
                            "param": param,
                            "items": selector.get_list(params, self.context),
                            "callback": self._update_param_callback_factory(param),
                        },
                    }
            elif param.param_type == bool:
                transition = {"class": ActionParamBoolSelectorState, "args": {"param": param}}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param": param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param": param}}
            elif issubclass(param.param_type, Enum):
                display_value = param.value.name if param.value else "None"
                transition = {"class": ActionParamEnumSelectorState, "args": {"param": param}}
            elif param.param_type == list:
                display_value = "[]"
                transition = {"class": ActionParamListEditorState, "args": {"param": param}}

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

