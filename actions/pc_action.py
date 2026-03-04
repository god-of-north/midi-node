from .action import Action, ActionParam

class PCAction(Action):
    TYPE = "pc"
    TITLE = "Send PC"

    def __init__(self, pc:int = 0, **kwargs):
        super().__init__(**kwargs)
        self.params["pc"] = ActionParam("pc", int, pc, default=0, options={"min_value":0, "max_value":127, "header":"Program Change"})

    def execute(self):
        self.context.show_info(self.params["pc"].value)
