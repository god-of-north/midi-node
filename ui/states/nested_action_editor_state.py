from typing import Dict

from core.device_event import EventType
from actions import ActionParam, ActionRegistry, ActionRegistryEntry

from .menu_state import MenuState


class NestedActionTypeSelectorState(MenuState):
    """Lets the user pick which Action class fills an Action-typed ActionParam."""

    def __init__(self, context, param: ActionParam):
        super().__init__(context)
        self.param = param
        self.action_types: Dict[str, ActionRegistryEntry] = {}
        for key in ActionRegistry.get_keys():
            entry = ActionRegistry.get_registered(key)
            if entry:
                self.action_types[entry.title] = entry
        self.items = list(self.action_types.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            entry = self.action_types[selected]
            current = self.param.value
            if current is None or current.__class__ != entry.action_cls:
                self.param.value = entry.action_cls(context=self.context)
            self.return_to_previous()
        else:
            super().handle_event(event)


class NestedActionEditorState(MenuState):
    """Editor for an Action-typed ActionParam: change the action type, configure its params."""

    def __init__(self, context, param: ActionParam):
        super().__init__(context)
        self.param = param

    def on_enter(self):
        from .action_editor_state import ActionEditorState

        action = self.param.value
        title = getattr(action, "TITLE", "Unknown") if action is not None else "None"

        self.transitions = {
            f"Type: {title}": {
                "class": NestedActionTypeSelectorState,
                "args": {"param": self.param},
            },
            "Configure": {
                "class": ActionEditorState,
                "args": {"action": action, "delete_callback": None},
            },
            "Back": None,
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
