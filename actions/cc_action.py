from .action import ActionParam
from .midi_action import MIDIAction


class CCAction(MIDIAction):
    TYPE = "cc"
    TITLE = "Send CC"

    def __init__(self, cc:int = 80, value:int = 0, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=80, options={"min_value":0, "max_value":127, "header":"CC Number"})
        self.params["value"] = ActionParam("value", int, value, default=127, options={"min_value":0, "max_value":127, "header":"CC Value"})

    def execute(self, **kwargs):
        # self.context.show_info(f"MIDI CC {self.params['cc'].value}:{self.params['value'].value}")
        self.context.send_cc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["cc"].value, self.params["value"].value)

        
class LinearCCAction(MIDIAction):
    TYPE = "linear_cc"
    TITLE = "Linear CC"

    def __init__(self, cc:int = 80, min_value:int = 0, max_value:int = 127, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=80, options={"min_value":0, "max_value":127, "header":"CC Number"})
        self.params["min_value"] = ActionParam("min_value", int, min_value, default=0, options={"min_value":0, "max_value":127, "header":"Min Value"})
        self.params["max_value"] = ActionParam("max_value", int, max_value, default=127, options={"min_value":0, "max_value":127, "header":"Max Value"})

    def execute(self, value, **kwargs):
        # self.context.show_info(f"MIDI CC {self.params['cc'].value}")
        value = self._map(value, 0, 127, self.params["min_value"].value, self.params["max_value"].value)
        self.context.send_cc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["cc"].value, value)

    def _map(self, cc:int, in_min:int, in_max:int, out_min:int, out_max:int):
        value = int((out_max - out_min) * (cc - in_min) / (in_max - in_min) + out_min)
        return value

class ExponentialCCAction(LinearCCAction):
    TYPE = "exponential_cc"
    TITLE = "Exponential CC"

    def __init__(self, cc:int = 80, exponent:float = 2.0, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=80, options={"min_value":0, "max_value":127, "header":"CC Number"})
        self.params["exponent"] = ActionParam("exponent", float, exponent, default=2.0, options={"min_value":1.0, "max_value":5.0, "header":"Exponent"})

    def execute(self, value, **kwargs):
        # self.context.show_info(f"MIDI CC {self.params['cc'].value}")
        value = self._map(value, 0, 127, self.params["min_value"].value, self.params["max_value"].value)
        value = self._exponential_map(value, self.params["exponent"].value)
        self.context.send_cc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["cc"].value, value)

    def _exponential_map(self, cc:int, exponent:float):
        normalized = cc / 127.0
        exp_value = normalized ** exponent
        mapped_value = int(exp_value * 127)
        return mapped_value