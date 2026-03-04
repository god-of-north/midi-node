from typing import Dict
from enum import Enum
from .menu_state import MenuState
from core.device_event import EventType
from actions import ActionRegistry, ActionRegistryEntry, Action
from controls import Control

class ActionSelectorState(MenuState):
    def __init__(self, context, control_id: Control, control_event: Enum):
        super().__init__(context)

        self.control_id = control_id
        self.control_event = control_event
    
        self.action_types: Dict[str, ActionRegistryEntry] = {}
        action_types = ActionRegistry.get_keys()
        for action_type in action_types:
            action_info = ActionRegistry.get_registered(action_type)
            if action_info:
                self.action_types[action_info.title] = action_info
        self.items = list(self.action_types.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_action_type = self.action_types[selected]

            control = self.context.data.preset.controls.get(self.control_id, None)
            existing_action:Action = control.actions.get(self.control_event, None)
            if not existing_action or existing_action.__class__ != new_action_type.action_cls:
                # Create new action
                control.actions[self.control_event] = new_action_type.action_cls(context=self.context)

            self.return_to_previous()
        else:
            super().handle_event(event)
