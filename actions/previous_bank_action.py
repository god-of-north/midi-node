from actions.action import Action, ActionParam


class PreviousBankAction(Action):
    TYPE = "previous_bank"
    TITLE = "Previous Bank"

    def __init__(self, stop_at_start: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.params["stop_at_start"] = ActionParam("stop_at_start", bool, stop_at_start, default=False, options={"header":"Stop at Start"})

    def execute(self, **kwargs):
        self.context.previous_bank(self.params["stop_at_start"].value)