from .action import Action, ActionParam
from .midi_action import MIDIAction

class PCAction(MIDIAction):
    TYPE = "pc"
    TITLE = "Send PC"

    def __init__(self, pc:int = 0, **kwargs):
        super().__init__(**kwargs)
        self.params["pc"] = ActionParam("pc", int, pc, default=0, options={"min_value":0, "max_value":127, "header":"Program Change"})

    def execute(self):
        self.context.show_info(f"MIDI PC {self.params['pc'].value}")
        # self.context.send_pc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["pc"].value)
