from actions.action import Action, ActionParam
from actions.param_selector import CustomSelectorType
from midi.midi_output_type import MidiOutputType

class MIDIAction(Action):
    TYPE = "midi"
    TITLE = "MIDI base action"

    def __init__(self, output: MidiOutputType = MidiOutputType.UART, port_name:str="/dev/serial0", channel:int = 1, **kwargs):
        super().__init__(**kwargs)
        self.params["channel"] = ActionParam("channel", int, channel, default=1, options={"min_value":0, "max_value":127, "header":"MIDI Channel"})
        self.params["output"] = ActionParam("output", MidiOutputType, output, default=MidiOutputType.UART, options={"header":"MIDI Type"})
        self.params["port_name"] = ActionParam("port_name", str, port_name, default="/dev/serial0", options={"header":"MIDI Port Name"}, custom_selector=CustomSelectorType.MIDI_OUTPUT)

    def execute(self, **kwargs):
        super().execute(**kwargs)