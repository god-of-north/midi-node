from midi.midi_output import MidiOutput
from midi.midi_output_type import MidiOutputType


class MidiRouter:
    def __init__(self):
        self.outputs: dict[str, MidiOutput] = {}

    def send_cc(self, output: MidiOutputType, name: str, channel:int, cc:int, value:int):
        device = self.outputs.get(name)
        if not device:
            device = self._create_output(output, name)
        device.send_cc(channel, cc, value)

    def send_pc(self, output: MidiOutputType, name: str, channel:int, program:int):
        device = self.outputs.get(name)
        if not device:
            device = self._create_output(output, name)
        device.send_pc(channel, program)

    def list_outputs(self, output_type: MidiOutputType) -> list[str]:
        if output_type == MidiOutputType.UART:
            from midi.uart_midi_output import UartMidiOutput
            return UartMidiOutput.list_serial_ports()
        elif output_type == MidiOutputType.USB:
            from midi.usb_midi_output import UsbMidiOutput
            return UsbMidiOutput.list_usb_midi_devices()

    def close(self):
        for o in self.outputs.values():
            o.close()

    def _create_output(self, output: MidiOutputType, name: str) -> MidiOutput:
        device = None
        if output == MidiOutputType.UART:
            from midi.uart_midi_output import UartMidiOutput
            device = UartMidiOutput(name)
        elif output == MidiOutputType.USB:
            from midi.usb_midi_output import UsbMidiOutput
            device = UsbMidiOutput(name)
        else:
            raise ValueError(f"Unknown MIDI output type: {name}")
        self.outputs[name] = device
        return device