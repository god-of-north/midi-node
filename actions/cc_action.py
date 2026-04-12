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
        self.context.show_info(f"MIDI CC {self.params['cc'].value}:{self.params['value'].value}")
        self.context.send_cc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["cc"].value, self.params["value"].value)

        