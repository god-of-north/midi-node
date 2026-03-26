import serial
from midi.midi_output import MidiOutput


class UartMidiOutput(MidiOutput):
    def __init__(self, port="/dev/serial0"):
        # /dev/ttyAMA0 - UART0 (PL011)
        # /dev/ttyS0 - UART1 (mini-UART) Might need 'core_freq=250' in config.txt for stability (or 'force_turbo=1' to disable dynamic frequency scaling)
        self.ser = serial.Serial(port, 31250)

    def send_cc(self, channel, cc, value):
        self.ser.write(bytes([0xB0 | channel, cc, value]))

    def send_pc(self, channel, program):
        self.ser.write(bytes([0xC0 | channel, program]))

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    # midi_out = UartMidiOutput("/dev/serial0")
    midi_out = UartMidiOutput("/dev/ttyAMA0")  # Try the other UART if the first one doesn't work
    # midi_out = UartMidiOutput("/dev/ttyS0")  # Try the other UART if the first one doesn't work

    # midi_out.send_cc(0, 80, 127)  # Send CC1 with value 127 on channel 0
    midi_out.send_pc(0, 10)       # Send Program Change to program 10 on channel 0
    midi_out.close()