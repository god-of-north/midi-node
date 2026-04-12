from typing import List
from actions import Action, EmptyAction

class Bank:
    def __init__(self, name: str, preset_numbers: List[int] = None, enter_action: Action = None, exit_action: Action = None):
        self.name = name
        self.preset_numbers = preset_numbers or []
        self.enter_action = enter_action or EmptyAction(context=None)
        self.exit_action = exit_action or EmptyAction(context=None)

    def to_dict(self):
        return {"name": self.name, "presets": self.preset_numbers, "enter_action": self.enter_action.to_dict(), "exit_action": self.exit_action.to_dict()}

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        enter_action = Action.from_dict(data.get("enter_action"), context=context) if data.get("enter_action") else EmptyAction(context=context)
        exit_action = Action.from_dict(data.get("exit_action"), context=context) if data.get("exit_action") else EmptyAction(context=context)
        return cls(name=data["name"], preset_numbers=data.get("presets", []), enter_action=enter_action, exit_action=exit_action)
