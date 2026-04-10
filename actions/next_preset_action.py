from actions.action import Action, ActionParam


class NextPresetAction(Action):
    TYPE = "next_preset"
    TITLE = "Next Preset"

    def __init__(self, stop_at_end: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.params["stop_at_end"] = ActionParam("stop_at_end", bool, stop_at_end, default=False, options={"header":"Stop at End"})

    def execute(self):
        next_preset_index = self.context.data.current_preset_index + 1
        if next_preset_index > self.context.data.max_preset_index:
            if not self.params["stop_at_end"].value:
                next_preset_index = 0
            else:
                next_preset_index = self.context.data.max_preset_index
        self.context.set_preset(next_preset_index)