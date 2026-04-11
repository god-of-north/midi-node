from actions.action import Action, ActionParam, ActionRegistry
from typing import List, Optional


class ToggleAction(Action):
    TYPE = "toggle"
    TITLE = "Toggle Action"

    toggle_slots = {}

    def __init__(self, actions:List[Action]=[], slot:int=0, **kwargs):
        super().__init__(**kwargs)

        fixed_actions = []
        for action in actions:
            if isinstance(action, Action):
                fixed_actions.append(action)
            if isinstance(action, dict):
                action = self.create_action_by_type(action["type"], action)
                fixed_actions.append(action)

        self.params["actions"] = ActionParam("actions", list, fixed_actions, default=[],
                                             options={"class_type": Action,
                                                      "creator_func": self.create_action_by_type,
                                                      "creator_items_func": self.get_creator_items})
        self.params["slot"] = ActionParam("slot", int, slot, default=0, options={"min_value":0, "max_value":100, "header":"Toggle Slot"})

    def execute(self):
        actions = self.params["actions"].value
        next_action_index = self.toggle_slots.get(self.params["slot"].value, -1) + 1
        max_index = len(actions) - 1
        if next_action_index > max_index:
            next_action_index = 0
        action = actions[next_action_index]
        self.toggle_slots[self.params["slot"].value] = next_action_index
        action.execute()

    def get_creator_items(self):
        return list(ActionRegistry.get_keys())

    def create_action_by_type(self, action_type:str, data:dict={}) -> Optional[Action]:
        action_info = ActionRegistry.get_registered(action_type)
        if action_info:
            return action_info.action_cls(context=self.context, **data)
        return None