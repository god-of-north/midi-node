import logging
import threading
import time

from midi.midi_input_router import MidiInputRouter
from midi.midi_router import MidiRouter
from midi.midi_output_type import MidiOutputType


class MIDIManager(threading.Thread):
    def __init__(self, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.shutdown = shutdown_event
        self.router = MidiRouter()

    def send_cc(self, output: MidiOutputType, name: str, channel: int, cc: int, value: int):
        self.router.send_cc(output, name, channel, cc, value)

    def send_pc(self, output: MidiOutputType, name: str, channel: int, program: int):
        self.router.send_pc(output, name, channel, program)

    def list_outputs(self, output_type: MidiOutputType) -> list[str]:
        return self.router.list_outputs(output_type)

    def close(self):
        self.router.close()

    def run(self):
        logging.info("MIDI Thread Started")
        try:
            while not self.shutdown.is_set():
                # future MIDI input background tasks.

                # MidiInputRouter.process_incoming() # TODO: implement this method to handle incoming MIDI messages and route them accordingly.

                time.sleep(0.01)
        finally:
            self.close()
            logging.info("MIDI Thread Shutting Down")

