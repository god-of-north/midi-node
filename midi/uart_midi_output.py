import serial
import serial.tools.list_ports
from mido import Message
from mido.parser import Parser
from midi.midi_output import MidiOutput


class UartMidiOutput(MidiOutput):
    def __init__(self, port="/dev/serial0"):
        # /dev/serial0 - UART0 (PL011)
        # /dev/ttyAMA0 - old UART0 (PL011)
        # /dev/ttyS0 - UART1 (mini-UART) Might need 'core_freq=250' in config.txt for stability (or 'force_turbo=1' to disable dynamic frequency scaling)
        self.ser = serial.Serial(port, 31250)

        self.read_buffer = bytearray(32)  # MIDI messages are max 3 bytes, but we can read in chunks
        self.parser = Parser()

    def send_cc(self, channel, cc, value):
        self.ser.write(bytes([0xB0 | channel, cc, value]))

    def send_pc(self, channel, program):
        self.ser.write(bytes([0xC0 | channel, program]))

    def close(self):
        self.ser.close()

    @staticmethod
    def list_serial_ports():
        """
        Lists serial ports
        """
        ports_data = serial.tools.list_ports.comports()
        ports = []
        if not ports_data:
            print("No serial ports found.")
        else:
            print("Available serial ports:")
            for port, desc, hwid in sorted(ports_data):
                ports.append(port)
        return ports
    
    def __del__(self):
        self.close()

    def read_chunk(self):
        if self.ser.in_waiting > 0:
            n = self.ser.readinto(self.read_buffer)
            return memoryview(self.read_buffer)[:n]
        return None

    def read_message(self) -> Message | None:
        chunk = self.read_chunk()
        if chunk:
            self.parser.feed(chunk)
            msg = self.parser.get_message()
            if msg:
                return msg
        return None


if __name__ == "__main__":
    midi_out = UartMidiOutput("/dev/serial0")
    # midi_out = UartMidiOutput("/dev/ttyAMA0")  # Try the other UART if the first one doesn't work
    # midi_out = UartMidiOutput("/dev/ttyS0")  # Try the other UART if the first one doesn't work

    # midi_out.send_cc(0, 80, 127)  # Send CC1 with value 127 on channel 0
    midi_out.send_pc(0, 10)       # Send Program Change to program 10 on channel 0
    midi_out.close()
