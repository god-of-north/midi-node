from core.device_event import EventType
from ui.states.int_selector_state import IntSelectorState
from ui.states.menu_state import MenuState


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
        self.context.data.save_app_config()

    def _update_buttons_long_press_time(self, value: int):
        self.context.data.config.buttons_long_press_time = value / 1000.0
        self.context.data.save_app_config()