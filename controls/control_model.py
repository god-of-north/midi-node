from __future__ import annotations
from abc import ABC
from typing import Dict

from input.pot_event import PotEvent
from .control import ControlType
from input.button_event import ButtonEvent
from actions import Action

class BaseControlModel(ABC):
    def __init__(self, control_type: ControlType, actions:Dict[ButtonEvent, Action]={}, context: 'DeviceContext'=None):
        self.control_type = control_type
        self.actions = actions
        self.context = context

    def to_dict(self) -> dict:
        return {
            "control_type": str(self.control_type),
            "actions": {str(k): v.to_dict() for k, v in self.actions.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'BaseControlModel':
        name = data["control_type"].split(".")[-1]
        control_type = ControlType[name]
        if control_type == ControlType.BUTTON:
            instance = ButtonControlModel.from_dict(data, context=context)
        elif control_type == ControlType.POTENTIOMETER:
            instance = PotControlModel.from_dict(data, context=context)
        else:
            instance = cls(control_type)
        return instance

class ButtonControlModel(BaseControlModel):
    def __init__(self, control_type: ControlType, actions:Dict[ButtonEvent, Action]={}, context: 'DeviceContext'=None):
        super().__init__(control_type, actions, context=context)

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'ButtonControlModel':
        actions = {ButtonEvent[k.split(".")[-1]]: Action.from_dict(v, context=context) for k, v in data["actions"].items()}
        instance = cls(control_type=ControlType.BUTTON, actions=actions, context=context)
        return instance

class PotControlModel(BaseControlModel):
    def __init__(self, control_type: ControlType, actions:Dict[PotEvent, Action]={}, context: 'DeviceContext'=None):
        super().__init__(control_type, actions, context=context)

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'PotControlModel':
        actions = {PotEvent[k.split(".")[-1]]: Action.from_dict(v, context=context) for k, v in data["actions"].items()}
        instance = cls(control_type=ControlType.POTENTIOMETER, actions=actions, context=context)
        return instance
