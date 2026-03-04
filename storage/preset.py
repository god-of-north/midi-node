from __future__ import annotations
from typing import Dict
from controls import Control, BaseControlModel

class Preset:
    def __init__(self, name: str, controls: Dict[Control, BaseControlModel] = None):
        self.name = name
        self.controls = controls or {}

    def to_dict(self):
        return {
            "name": self.name,
            "controls": {str(k): v.to_dict() for k, v in self.controls.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        name = data.get("name", "[Unnamed]")
        controls = {}
        for ctrl_name, model_data in data.get("controls", {}).items():
            model = BaseControlModel.from_dict(model_data, context=context)
            member_name = ctrl_name.split(".")[-1]
            controls[Control[member_name]] = model
        return cls(name=name, controls=controls)

