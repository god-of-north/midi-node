from .action import Action, ActionParam

class CCAction(Action):
    TYPE = "cc"
    TITLE = "Send CC"

    def __init__(self, cc:int = 127, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=127, options={"min_value":0, "max_value":127, "header":"Control Change"})

    def execute(self):
        self.context.show_info(self.params["cc"].value)
