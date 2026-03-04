from .menu_state import MenuState
from core.device_event import EventType

class ListItemCreatorState(MenuState):
    def __init__(self, context, items, item_add_func):
        super().__init__(context, items)
        self.item_add_func = item_add_func

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.item_add_func(selected)
            self.return_to_previous()
        else:
            super().handle_event(event)
