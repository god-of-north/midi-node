from .menu_state import MenuState
from .list_item_creator_state import ListItemCreatorState
from core.device_event import EventType
from actions import ActionParam

class ActionParamListEditorState(MenuState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != list:
            raise ValueError(f"Parameter '{param.name}' is not a valid list parameter.")

        super().__init__(context)
        self.param = param
        self.creator_items = param.options.get("creator_items_func")() if "creator_items_func" in param.options else []
        self.creator_func = param.options.get("creator_func") if "creator_func" in param.options else None

    def on_enter(self):
        from .action_editor_state import ActionEditorState
        self.transitions = {}
        for idx, item in enumerate(self.param.value):
            self.transitions[f"{idx+1}:{item.__str__()}"] = {"class": ActionEditorState, "args": {"action": item, "delete_callback": lambda i=item: self.param.value.remove(i)}}
        self.transitions["Add Item"] = {"class": ListItemCreatorState, "args": {"items": self.creator_items, "item_add_func": self._add_item}}
        self.transitions["Back"] = None
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

    def _add_item(self, item_type:str):
        if self.creator_func:
            new_item = self.creator_func(item_type)
            if new_item:
                self.param.value.append(new_item)