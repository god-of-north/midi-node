from actions.action import Action


class EmptyAction(Action):
    TYPE = "empty"
    TITLE = "Empty"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self, **kwargs):
        pass