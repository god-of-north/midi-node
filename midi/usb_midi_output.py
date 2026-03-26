import mido
from midi.midi_output import MidiOutput


class UsbMidiOutput(MidiOutput):
    def __init__(self, port_name):
        self.port = mido.open_output(port_name)

    def send_cc(self, channel, cc, value):
        self.port.send(mido.Message("control_change",
                                    channel=channel,
                                    control=cc,
                                    value=value))

    def send_pc(self, channel, program):
        self.port.send(mido.Message("program_change",
                                    channel=channel,
                                    program=program))

    def close(self):
        self.port.close()

if __name__ == "__main__":

    midi_name = None
    print("Available MIDI output ports:")
    for port in mido.get_output_names():
        print(f"  {port}")
        # detect port with "MIDI" in the name (case-insensitive)
        if "midi" in port.lower():
            print(f"  -> Detected MIDI port: {port}")
            midi_name = port
            break

    if not midi_name:
        print("No MIDI output port found. Please connect a MIDI device and try again.")
    else:
        midi_out = UsbMidiOutput(midi_name)
        # midi_out.send_cc(0, 80, 127)  # Send CC1 with value 127 on channel 0
        midi_out.send_pc(0, 10)       # Send Program Change to program 10 on channel 0
        midi_out.close()