from core.device_event import EventType
from storage.app_config import PotCalibration
from ui.states.boolean_selector_state import BooleanWithCallbackState
from ui.states.int_selector_state import IntSelectorState
from ui.states.menu_selector_state import MenuSelectorState
from ui.states.menu_state import MenuState


class PotConfigState(MenuState):
    def __init__(self, context, pot: PotCalibration):
        super().__init__(context)
        self.pot = pot

    def on_enter(self):
        self.transitions = {}
        
        self.transitions[f"MinValue:{self.pot.min_value}"] = {"class": IntSelectorState, "args": {
            "value": self.pot.min_value,
            "callback": self._update_min_value,
            "header": f"Min Value",
            "min_value": 0,
            "max_value": max(0, self.pot.max_value - 1)
        }}
        
        self.transitions[f"MaxValue:{self.pot.max_value}"] = {"class": IntSelectorState, "args": {
            "value": self.pot.max_value,
            "callback": self._update_max_value,
            "header": f"Max Value",
            "min_value": min(0, self.pot.min_value + 1),
            "max_value": 65535
        }}

        self.transitions[f"MinThreshold:{self.pot.min_threshold}"] = {"class": IntSelectorState, "args": {
            "value": self.pot.min_threshold,
            "callback": self._update_min_threshold,
            "header": f"Min Threshold",
            "min_value": max(0, self.pot.min_value),
            "max_value": min(65535, self.pot.max_threshold)
        }}

        self.transitions[f"MaxThreshold:{self.pot.max_threshold}"] = {"class": IntSelectorState, "args": {
            "value": self.pot.max_threshold,
            "callback": self._update_max_threshold,
            "header": f"Max Threshold",
            "min_value": max(0, self.pot.min_threshold),
            "max_value": min(65535, self.pot.max_value)
        }}

        self.transitions[f"EMA:a-min:{self.pot.ema_filter_alpha_min:.2f}"] = {"class": IntSelectorState, "args": {
            "value": int(self.pot.ema_filter_alpha_min * 100),
            "callback": self._update_ema_alpha_min,
            "header": f"EMA Alpha Min",
            "min_value": 0,
            "max_value": 100
        }}

        self.transitions[f"EMA:a-max:{self.pot.ema_filter_alpha_max:.2f}"] = {"class": IntSelectorState, "args": {
            "value": int(self.pot.ema_filter_alpha_max * 100),
            "callback": self._update_ema_alpha_max,
            "header": f"EMA Alpha Max",
            "min_value": 0,
            "max_value": 100
        }}

        self.transitions[f"Sensitivity:{self.pot.ema_filter_sensitivity:.2f}"] = {"class": IntSelectorState, "args": {
            "value": int(self.pot.ema_filter_sensitivity * 100),
            "callback": self._update_ema_filter_sensitivity,
            "header": f"EMA Sensitivity",
            "min_value": 0,
            "max_value": 100
        }}

        self.transitions[f"StopChanging:{self.pot.stop_changing_timeout:.2f}s"] = {"class": IntSelectorState, "args": {
            "value": int(self.pot.stop_changing_timeout * 1000),
            "callback": self._update_stop_changing_timeout,
            "header": f"StopChanging Timeout",
            "min_value": 0,
            "max_value": 10000
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

    def _update_stop_changing_timeout(self, value: int):
        self.pot.stop_changing_timeout = value / 1000.0
        self.context.data.save_app_config()

    def _update_ema_filter_sensitivity(self, value: int):
        self.pot.ema_filter_sensitivity = value / 100.0
        self.context.data.save_app_config()

    def _update_ema_alpha_max(self, value: int):
        self.pot.ema_filter_alpha_max = value / 100.0
        self.context.data.save_app_config()

    def _update_ema_alpha_min(self, value: int):
        self.pot.ema_filter_alpha_min = value / 100.0
        self.context.data.save_app_config()

    def _update_min_value(self, value: int):
        self.pot.min_value = value
        self.context.data.save_app_config()

    def _update_max_value(self, value: int):
        self.pot.max_value = value
        self.context.data.save_app_config()

    def _update_min_threshold(self, value: int):
        self.pot.min_threshold = value
        self.context.data.save_app_config()

    def _update_max_threshold(self, value: int):
        self.pot.max_threshold = value
        self.context.data.save_app_config()


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

        self.transitions["BTN:Active Low"] = {"class": BooleanWithCallbackState, "args": {
            "value": self.context.data.config.buttons_active_low,
            "callback": self._update_buttons_active_low,
            "true_value": "Active Low",
            "false_value": "Active High"
        }}

        self.transitions["Input Poll Interval"] = {"class": IntSelectorState, "args": {
            "value": int(self.context.data.config.input_poll_interval*1000),
            "callback": self._update_input_poll_interval,
            "header": "Input Poll Interval",
            "min_value": 1,
            "max_value": 1000
        }}

        self.transitions["ADS1115 Address"] = {"class": IntSelectorState, "args": {
            "value": int(self.context.data.config.ads1115_address),
            "callback": self._update_ads1115_address,
            "header": "ADS1115 Address",
            "min_value": 0,
            "max_value": 127,
            "base": 16
        }}

        self.transitions["ADS1115 Gain"] = {"class": MenuSelectorState, "args": {
            "param": str(self.context.data.config.ads1115_gain),
            "callback": self._update_ads1115_gain,
            "header": "ADS1115 Gain",
            "items": [1, 2, 4, 8, 16, 32]
        }}

        self.transitions["ADS1115 PotThreshold"] = {"class": IntSelectorState, "args": {
            "value": int(self.context.data.config.ads1115_pot_threshold),
            "callback": self._update_ads1115_pot_threshold,
            "header": "ADS1115 PotThreshold",
            "min_value": 1,
            "max_value": 1000
        }}

        for pot_ctrl, pot in self.context.data.config.pot_calibration.items():
            self.transitions[f"Config {pot_ctrl.name}"] = {"class": PotConfigState, "args": {
                "pot": pot,
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

    def _update_buttons_active_low(self, value: bool):
        self.context.data.config.buttons_active_low = value
        self.context.data.save_app_config()

    def _update_input_poll_interval(self, value: int):
        self.context.data.config.input_poll_interval = value / 1000.0
        self.context.data.save_app_config()

    def _update_ads1115_address(self, value: int):
        self.context.data.config.ads1115_address = value
        self.context.data.save_app_config()
    
    def _update_ads1115_gain(self, value):
        self.context.data.config.ads1115_gain = int(value)
        self.context.data.save_app_config()

    def _update_ads1115_pot_threshold(self, value: int):
        self.context.data.config.ads1115_pot_threshold = value
        self.context.data.save_app_config()
