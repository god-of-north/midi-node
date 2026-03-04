from typing import List

class Bank:
    def __init__(self, name: str, preset_numbers: List[int] = None):
        self.name = name
        self.preset_numbers = preset_numbers or []

    def to_dict(self):
        return {"name": self.name, "presets": self.preset_numbers}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(name=data["name"], preset_numbers=data.get("presets", []))
