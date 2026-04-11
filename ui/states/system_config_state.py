from actions import Action
from actions.action import ActionParam
from actions.param_selector import CustomParamSelectorRegistry
from controls import Control
from core.device_event import EventType
from ui.states.action_param_list_editor_state import ActionParamListEditorState
from ui.states.action_param_selector_states import ActionParamBoolSelectorState, ActionParamEnumSelectorState, ActionParamIntSelectorState, ActionParamStringSelectorState
from ui.states.action_selector_state import ActionSelectorState
from ui.states.error_state import ErrorState
from ui.states.int_selector_state import IntNumberSelectorState
from ui.states.menu_selector_state import MenuSelectorState
from ui.states.menu_state import MenuState


from enum import Enum


class IntSelectorState(IntNumberSelectorState):
    def __init__(self, context, value: int = 0, callback=None, header="Set Value:", min_value=0, max_value=100):
        super().__init__(
            context,
            min_value=min_value,
            max_value=max_value,
            value=value,
            header=header
        )
        self.callback = callback


    def return_to_previous(self, deep: int = 1):
        self.callback(self.get_value())
        super().return_to_previous()


class SystemConfigState(MenuState):
    def __init__(self, context, ):
        super().__init__(context)

    def on_enter(self):

        self.transitions = {}
        self.transitions["BTN:Tap Time"] = {"class": IntSelectorState, "args": {
            "value": int(self.context.data.config.buttons_tap_time*1000), 
            "callback": self._update_buttons_tap_time,
            "header": "Tap Time (ms)",
            "min_value": 50,
            "max_value": min(int(self.context.data.config.buttons_long_press_time*1000) - 50, 1000)
        }}
        self.transitions["BTN:Long Press Time"] = {"class": IntSelectorState, "args": {
            "value": int(self.context.data.config.buttons_long_press_time*1000),
            "callback": self._update_buttons_long_press_time,
            "header": "Long Press Time (ms)",
            "min_value": max(int(self.context.data.config.buttons_tap_time*1000) + 50, 300),
            "max_value": 5000
        }}

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

    def _update_buttons_tap_time(self, value: int):
        self.context.data.config.buttons_tap_time = value / 1000.0

    def _update_buttons_long_press_time(self, value: int):
        self.context.data.config.buttons_long_press_time = value / 1000.0