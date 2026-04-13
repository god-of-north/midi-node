from typing import Dict

from .menu_state import MenuState
from core.device_event import EventType
from actions import ActionRegistry, ActionRegistryEntry, Action


class BankActionSelectorState(MenuState):
    """
    State for selecting the Action type used as Bank Enter/Exit action.
    """

    def __init__(self, context, is_enter: bool):
        super().__init__(context)
        self.is_enter = is_enter

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

            bank = self.context.get_current_bank()
            existing_action: Action = bank.enter_action if self.is_enter else bank.exit_action
            if not existing_action or existing_action.__class__ != new_action_type.action_cls:
                if self.is_enter:
                    bank.enter_action = new_action_type.action_cls(context=self.context)
                else:
                    bank.exit_action = new_action_type.action_cls(context=self.context)

            self.return_to_previous()
        else:
            super().handle_event(event)
