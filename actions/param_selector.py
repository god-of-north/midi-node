from enum import Enum, auto
from typing import Dict, Optional
from abc import ABC, abstractmethod


class CustomSelectorType(Enum):
    MIDI_OUTPUT = auto()

class CustomParamSelectorRegistry:
    _registry: Dict[CustomSelectorType, 'ParamSelector'] = {}

    @classmethod
    def register(cls, name: CustomSelectorType, selector: 'ParamSelector'):
        cls._registry[name] = selector

    @classmethod
    def get_selector(cls, name: CustomSelectorType) -> Optional['ParamSelector']:
        return cls._registry.get(name)

class ParamSelector(ABC):
    TYPE:CustomSelectorType = None

    @abstractmethod
    def get_list(self, params: list['ActionParam'], context: 'DeviceContext') -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs):
        """
        Automatically called when any subclass is defined.
        Registers the subclass in the CustomParamSelectorRegistry.
        """
        super().__init_subclass__(**kwargs)
        if cls.TYPE != None:
            CustomParamSelectorRegistry.register(cls.TYPE, cls())