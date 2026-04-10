from actions.action import Action, ActionParam


class PreviousPresetAction(Action):
    TYPE = "previous_preset"
    TITLE = "Previous Preset"

    def __init__(self, stop_at_start: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.params["stop_at_start"] = ActionParam("stop_at_start", bool, stop_at_start, default=False, options={"header":"Stop at Start"})

    def execute(self):
        previous_preset_index = self.context.data.current_preset_index - 1
        if previous_preset_index < 0:
            if not self.params["stop_at_start"].value:
                previous_preset_index = self.context.data.max_preset_index
            else:
                previous_preset_index = 0
        self.context.set_preset(previous_preset_index)