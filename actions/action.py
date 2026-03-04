from __future__ import annotations
from typing import Dict, List, Optional, Type, Any, Union

class ActionParam:
    def __init__(self, name: str, param_type: type, value, default=None, options:dict={}):
        self.name = name
        self.param_type = param_type
        self.value = value
        self.default = default
        self.options = options or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "param_type": self.param_type.__name__,
            "value": self.value,
            "default": self.default,
            "options": self.options
        }
    
    def __dict__(self):
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ActionParam':
        param_type = eval(data["param_type"])
        return cls(
            name=data["name"],
            param_type=param_type,
            value=data["value"],
            default=data.get("default"),
            options=data.get("options", {})
        )

class ActionRegistryEntry:
    def __init__(self, action_type: str, action_cls: Type['Action'], title: str):
        self.action_type = action_type
        self.action_cls = action_cls
        self.title = title

class ActionRegistry:
    """A dedicated registry to keep the global namespace clean."""
    _registry: Dict[str, ActionRegistryEntry] = {}

    @classmethod
    def register(cls, action_type: str, action_cls: Type['Action'], title: str):
        cls._registry[action_type] = ActionRegistryEntry(action_type, action_cls, title)

    @classmethod
    def get_class(cls, action_type: str) -> Optional[Type['Action']]:
        entry = cls._registry.get(action_type)
        return entry.action_cls if entry else None

    @classmethod
    def get_registered(cls, action_type: str) -> Optional[ActionRegistryEntry]:
        entry = cls._registry.get(action_type)
        return entry if entry else None
    
    @classmethod
    def get_keys(cls) -> List[str]:
        return list(cls._registry.keys())


class Action:
    TYPE = "base"
    TITLE = "Base Action"

    def __init__(self, context: 'DeviceContext', **kwargs):
        self.context = context
        self.params: dict[str, ActionParam] = kwargs.get("params", {})

    def __init_subclass__(cls, **kwargs):
        """
        Automatically called when any subclass is defined.
        Registers the subclass in the ActionRegistry.
        """
        super().__init_subclass__(**kwargs)
        if cls.TYPE != "base":
            ActionRegistry.register(cls.TYPE, cls, cls.TITLE)

    def execute(self):
        raise NotImplementedError

    def to_dict(self) -> dict:
        result = {"type": self.TYPE}
        
        for param in self.params.values():
            if hasattr(param.value, "to_dict"):
                result[param.name] = param.value.to_dict()
            elif isinstance(param.value, list):
                result[param.name] = self.list_to_dict(param.value)
            else:
                result[param.name] = param.value

        return result
    
    def list_to_dict(self, items: List[Any]) -> List[dict]:
        result = []
        for item in items:
            if hasattr(item, "to_dict"):
                result.append(item.to_dict())
            else:
                result.append(item)
        return result

    @staticmethod
    def from_dict(data: dict, context: 'DeviceContext') -> 'Action':
        action_type = data.get("type")
        action_cls = ActionRegistry.get_class(action_type)

        if not action_cls:
            # Fallback to base or raise error if type is unknown
            print(f"Warning: Unknown action type '{action_type}'. Using base Action.")
            return Action(context=context)

        return action_cls(context=context, **data)

    def __str__(self):
        return self.TITLE
