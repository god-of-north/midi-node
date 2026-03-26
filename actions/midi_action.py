from abc import ABC, abstractmethod
from typing import Dict, Optional
from actions.action import Action, ActionParam, CustomSelectorType
from midi.midi_output_type import MidiOutputType


class ParamSelector(ABC):

    TYPE:CustomSelectorType = None

    @abstractmethod
    def get_list(self, params: list[ActionParam]) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs):
        """
        Automatically called when any subclass is defined.
        Registers the subclass in the CustomParamSelectorRegistry.
        """
        super().__init_subclass__(**kwargs)
        if cls.TYPE != None:
            CustomParamSelectorRegistry.register(cls.TYPE, cls())


class MIDIOutputSelector(ParamSelector):
    def get_list(self, params: list[ActionParam]) -> list[str]:
        output = params.get("output")
        output_type = output.value if output else MidiOutputType.UART
        if output_type == MidiOutputType.UART:
            # TODO: query actual UART MIDI devices
            return ["/dev/ttyAMA0", "/dev/ttyS0"]
        elif output_type == MidiOutputType.USB:
            # TODO: query actual USB MIDI devices
            return ["USB MIDI Device 1", "USB MIDI Device 2"]
        return []

class CustomParamSelectorRegistry:
    _registry: Dict[CustomSelectorType, ParamSelector] = {}

    @classmethod
    def register(cls, name: CustomSelectorType, selector: ParamSelector):
        cls._registry[name] = selector

    @classmethod
    def get_selector(cls, name: CustomSelectorType) -> Optional[ParamSelector]:
        return cls._registry.get(name)
    



class MIDIAction(Action):
    TYPE = "midi"
    TITLE = "MIDI base action"

    def __init__(self, output: MidiOutputType, port_name, channel:int = 1, **kwargs):
        super().__init__(**kwargs)
        self.params["channel"] = ActionParam("channel", int, channel, default=1, options={"min_value":0, "max_value":127, "header":"MIDI Channel"})
        self.params["output"] = ActionParam("output", MidiOutputType, output, default=MidiOutputType.UART, options={"header":"MIDI Type"})
        self.params["port_name"] = ActionParam("port_name", str, port_name, default="/dev/ttyAMA0", options={"header":"MIDI Port Name"})

    def execute(self):
        super().execute()