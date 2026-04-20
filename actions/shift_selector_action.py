from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .action import Action, ActionParam, ActionRegistry
from .empty_action import EmptyAction

if TYPE_CHECKING:
    from core.device_context import DeviceContext


class ShiftBranch:
    """Maps a shift index (1-based, same as ShiftAction) to an action when that shift is active."""

    def __init__(self, shift_number: int, action: Action):
        self.shift_number = shift_number
        self.action = action

    def __str__(self) -> str:
        return f"Shift {self.shift_number}: {self.action}"

    def to_dict(self) -> Dict[str, Any]:
        return {"shift_number": self.shift_number, "action": self.action.to_dict()}

    @classmethod
    def from_dict(cls, data: dict, context: "DeviceContext") -> "ShiftBranch":
        from .action import Action as ActionCls

        sn = int(data["shift_number"])
        act = ActionCls.from_dict(data["action"], context=context)
        return cls(sn, act)


def _shift_branch_item_editor_state_class():
    from ui.states.shift_branch_item_editor_state import ShiftBranchItemEditorState

    return ShiftBranchItemEditorState


class ShiftSelectorAction(Action):
    """
    Runs the nested action for the highest active global shift that has a branch;
    otherwise runs default_action.
    """

    TYPE = "shift_selector"
    TITLE = "Shift Selector"

    def __init__(
        self,
        branches: Optional[List[Any]] = None,
        default_action: Optional[Any] = None,
        **kwargs,
        
    ):
        super().__init__(**kwargs)

        fixed: List[ShiftBranch] = []
        for raw in branches or []:
            if isinstance(raw, ShiftBranch):
                fixed.append(raw)
            elif isinstance(raw, dict):
                fixed.append(ShiftBranch.from_dict(raw, self.context))

        da = default_action
        if isinstance(da, dict):
            from .action import Action as ActionCls

            da = ActionCls.from_dict(da, context=self.context)
        elif da is None:
            da = EmptyAction(context=self.context)

        self.params["branches"] = ActionParam(
            "branches",
            list,
            fixed,
            default=[],
            options={
                "creator_func": self._create_branch,
                "creator_items_func": self._creator_items,
                "item_editor_state_class": _shift_branch_item_editor_state_class,
            },
        )
        self.params["default_action"] = ActionParam(
            "default_action",
            Action,
            da,
            default=None,
            options={"header": "Default when no shift matches"},
        )

    def _creator_items(self) -> List[str]:
        return list(ActionRegistry.get_keys())

    def _create_branch(self, action_type: str) -> Optional[ShiftBranch]:
        action_info = ActionRegistry.get_registered(action_type)
        if not action_info:
            return None
        action = action_info.action_cls(context=self.context, **{"type": action_type})
        return ShiftBranch(1, action)

    def _branch_map(self) -> dict[int, ShiftBranch]:
        m: dict[int, ShiftBranch] = {}
        for b in self.params["branches"].value:
            m[b.shift_number] = b
        return m

    def execute(self, **kwargs):
        bm = self._branch_map()
        candidates = [n for n in bm if self.context.get_shift_flag(n)]
        if candidates:
            bm[max(candidates)].action.execute(**kwargs)
            return
        self.params["default_action"].value.execute(**kwargs)
