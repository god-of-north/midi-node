from actions.action import ActionParam
from core.device_event import EventType
from ui.states.menu_state import MenuState


class MenuSelectorState(MenuState):
    def __init__(self, context, param, items: list[str], callback):
        super().__init__(context)
        self.param = param
        self.items = items
        self.callback = callback

        try:
            self.selected_index = self.items.index(str(param))
        except ValueError:
            self.selected_index = 0

    def on_enter(self):
        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.callback(selected)
            self.return_to_previous()
        else:
            super().handle_event(event)