from actions.action import Action, ActionParam


class SelectBankAction(Action):
    TYPE = "select_bank"
    TITLE = "Select Bank"

    def __init__(self, bank_number:int=0, **kwargs):
        super().__init__(**kwargs)
        self.params["bank_number"] = ActionParam("bank_number", int, bank_number, default=0, options={"min_value":0, "max_value":100, "header":"Bank Number"})

    def execute(self, **kwargs):
        self.context.set_bank(self.params["bank_number"].value)