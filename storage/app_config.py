from enum import Enum, auto


class AppMode(Enum):
    SIMULATION = auto()
    LIVE = auto()

class AppConfig:
    def __init__(self):
        self.app_mode: AppMode = AppMode.LIVE

    def to_dict(self):
        return {
            "app_mode": str(self.app_mode),
        }

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        mode_name = data.get("app_mode", "LIVE").split(".")[-1]
        instance.app_mode = AppMode[mode_name]
        return instance