from core.device_event import EventType
from .menu_state import MenuState
from .int_selector_state import IntSelectorState
from .action_editor_state import ActionEditorState


class ShiftBranchDeleteConfirmState(MenuState):
    """Confirm branch removal; on confirm pops this editor and the branch row editor."""

    def __init__(self, context, delete_callback):
        super().__init__(context, items=["Cancel", "Confirm delete"])
        self.delete_callback = delete_callback

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            if selected == "Confirm delete" and self.delete_callback:
                self.delete_callback()
                self.return_to_previous(deep=2)
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)


class ShiftBranchItemEditorState(MenuState):
    def __init__(self, context, item, delete_callback=None):
        super().__init__(context)
        self.branch = item
        self.delete_callback = delete_callback

    def on_enter(self):
        self.transitions = {
            "Shift number": {
                "class": IntSelectorState,
                "args": {
                    "value": self.branch.shift_number,
                    "min_value": 1,
                    "max_value": 16,
                    "header": "Shift number:",
                    "callback": self._set_shift_number,
                },
            },
            "Action": {
                "class": ActionEditorState,
                "args": {"action": self.branch.action, "delete_callback": None},
            },
            "Back": None,
        }
        if self.delete_callback is not None:
            self.transitions["Delete branch"] = {
                "class": ShiftBranchDeleteConfirmState,
                "args": {"delete_callback": self.delete_callback},
            }
        self.items = list(self.transitions.keys())
        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

    def _set_shift_number(self, value: int) -> None:
        self.branch.shift_number = value
