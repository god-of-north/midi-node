from .action import Action, ActionParam


class ShiftAction(Action):
    TYPE = "shift"
    TITLE = "Shift"

    def __init__(self, shift_number: int = 1, active: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.params["shift_number"] = ActionParam(
            "shift_number",
            int,
            shift_number,
            default=1,
            options={"min_value": 1, "max_value": 16, "header": "Shift Number"},
        )
        self.params["active"] = ActionParam(
            "active",
            bool,
            active,
            default=True,
            options={"header": "Active"},
        )

    def execute(self, **kwargs):
        n = self.params["shift_number"].value
        on = self.params["active"].value
        self.context.set_shift_flag(n, on)
        self.context.show_info(f"Shift {n} {'ON' if on else 'OFF'}")
