from enum import Enum
from .menu_state import MenuState
from core.device_event import EventType

class EnumSelectorState(MenuState):
    def __init__(self, context, enum_type: type[Enum], value: Enum):
        super().__init__(context)
        self.enum_type = enum_type
        self.selected_value = value

        self.transitions = {}
        for member in enum_type:
            self.transitions[member.name] = member
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            self.return_to_previous()
        else:
            super().handle_event(event)
    
    def get_value(self) -> Enum:
        return self.selected_value
