from actions.action import Action, ActionParam


class SelectPresetAction(Action):
    TYPE = "select_preset"
    TITLE = "Select Preset"

    def __init__(self, preset_number:int=0, **kwargs):
        super().__init__(**kwargs)
        self.params["preset_number"] = ActionParam("preset_number", int, preset_number, default=0, options={"min_value":0, "max_value":100, "header":"Preset Number"})

    def execute(self, **kwargs):
        self.context.set_preset(self.params["preset_number"].value)

