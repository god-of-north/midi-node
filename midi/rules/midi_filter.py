from midi.midi_message_type import MidiMessageType


from dataclasses import dataclass, field
from typing import List
from mido import Message


@dataclass
class MidiFilter:
    channels: List[int] = field(default_factory=lambda: list(range(16)))
    note_range: tuple = (0, 127)
    cc_range: tuple = (0, 127)
    blocked_types: List[str] = field(default_factory=list)

    def is_allowed(self, msg: Message) -> bool:
        if msg.type in self.blocked_types:
            return False
        if msg.channel not in self.channels:
            return False
        if msg.note is not None and not (self.note_range[0] <= msg.note <= self.note_range[1]):
            return False
        if msg.type == MidiMessageType.CONTROL_CHANGE.value and not (self.cc_range[0] <= msg.note <= self.cc_range[1]):
            # Note: in CC, the 'note' field often stores the CC number
            return False
        return True
    
    def to_dict(self):
        return {
            "channels": self.channels,
            "note_range": self.note_range,
            "cc_range": self.cc_range,
            "blocked_types": self.blocked_types,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        channels = data.get("channels", list(range(16)))
        note_range = tuple(data.get("note_range", (0, 127)))
        cc_range = tuple(data.get("cc_range", (0, 127)))
        blocked_types = data.get("blocked_types", [])
        return cls(channels=channels, note_range=note_range, cc_range=cc_range, blocked_types=blocked_types)