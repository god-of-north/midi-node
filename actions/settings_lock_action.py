from .action import Action, ActionParam


class SettingsLockAction(Action):
    TYPE = "settings_lock"
    TITLE = "Settings Lock"

    def __init__(self, locked: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.params["locked"] = ActionParam(
            "locked",
            bool,
            locked,
            default=True,
            options={"header": "Settings Locked"},
        )

    def execute(self, **kwargs):
        on = self.params["locked"].value
        self.context.set_settings_menu_locked(on)
