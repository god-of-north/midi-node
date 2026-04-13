from midi.rules.midi_filter import MidiFilter
from midi.rules.midi_routing_rule import MidiRoutingRule


from dataclasses import dataclass
from typing import Optional
from mido import Message


@dataclass
class MidiForwardingRule(MidiRoutingRule):
    """Simple mirror: Source -> Destinations"""

    type: str = "MidiForwardingRule"

    def apply(self, msg: Message) -> Optional[Message]:
        return msg
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict["type"] = self.type
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        return cls()
            