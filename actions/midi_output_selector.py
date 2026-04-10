from actions.action import ActionParam
from actions.param_selector import CustomSelectorType, ParamSelector
from midi.midi_output_type import MidiOutputType


class MIDIOutputSelector(ParamSelector):
    TYPE:CustomSelectorType = CustomSelectorType.MIDI_OUTPUT

    def get_list(self, params: list[ActionParam], context: 'DeviceContext') -> list[str]:
        output = params.get("output")
        output_type = output.value if output else MidiOutputType.UART
        return context.list_midi_outputs(output_type)
        