from .menu_state import MenuState
from core.device_event import EventType

class BooleanSelectorState(MenuState):
    def __init__(self, context, value:bool, true_value:str="True", false_value:str="False"):
        super().__init__(context)
        self.true_value = true_value
        self.false_value = false_value
        self.selected_value = value

        self.transitions = {}
        self.transitions[self.true_value] = True
        self.transitions[self.false_value] = False
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            self.return_to_previous()
        else:
            super().handle_event(event)
    
    def get_value(self) -> bool:
        return self.selected_value

class BooleanWithCallbackState(BooleanSelectorState):
    def __init__(self, context, value:bool, callback, true_value:str="True", false_value:str="False"):
        super().__init__(context, value, true_value, false_value)
        self.callback = callback

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            if self.selected_value:
                self.callback(True)
            else:
                self.callback(False)
            self.return_to_previous()
        else:
            super().handle_event(event)
