from mido import Message
from abc import ABC, abstractmethod


class MidiOutput(ABC):
    @abstractmethod
    def send_cc(self, channel, cc, value): pass

    @abstractmethod
    def send_pc(self, channel, program): pass

    @abstractmethod
    def close(self): pass
    
    @abstractmethod
    def read_message(self) -> Message | None: pass
