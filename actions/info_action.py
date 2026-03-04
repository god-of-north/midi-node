from .action import Action, ActionParam

class InfoAction(Action):
    TYPE = "info"
    TITLE = "Show Info"

    def __init__(self, info:str = "Info", **kwargs):
        super().__init__(**kwargs)
        self.params["info"] = ActionParam("info", str, info)

    def execute(self):
        self.context.show_info(self.params["info"].value)
