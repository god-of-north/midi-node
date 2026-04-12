from actions.action import Action, ActionParam


class NextBankAction(Action):
    TYPE = "next_bank"
    TITLE = "Next Bank"

    def __init__(self, stop_at_end: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.params["stop_at_end"] = ActionParam("stop_at_end", bool, stop_at_end, default=False, options={"header":"Stop at End"})

    def execute(self, **kwargs):
        self.context.next_bank(self.params["stop_at_end"].value)