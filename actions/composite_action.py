from __future__ import annotations
from typing import List, Optional
from .action import Action, ActionParam, ActionRegistry

class CompositeAction(Action):
    TYPE = "composite"
    TITLE = "Composite Action"

    def __init__(self, actions:List[Action]=[], **kwargs):
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

    def execute(self):
        for action in self.params["actions"].value:
            action.execute()

    def get_creator_items(self):
        return list(ActionRegistry.get_keys())
    
    def create_action_by_type(self, action_type:str, data:dict={}) -> Optional[Action]:
        action_info = ActionRegistry.get_registered(action_type)
        if action_info:
            return action_info.action_cls(context=self.context, **data)
        return None
