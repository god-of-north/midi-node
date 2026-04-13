from midi.rules.midi_routing_rule import MidiRoutingRule
from midi.midi_message_type import MidiMessageType


from dataclasses import dataclass, field, replace
from typing import Optional
from mido import Message


@dataclass
class MidiChannelMapRule(MidiRoutingRule):
    """Map input channel X to output channel Y"""
    type: str = "MidiChannelMapRule"
    channel_map: dict = field(default_factory=dict) # {in_chan: out_chan}

    def apply(self, msg: Message) -> Optional[Message]:
        if msg.type in [MidiMessageType.NOTE_ON.value, MidiMessageType.NOTE_OFF.value, MidiMessageType.CONTROL_CHANGE.value, MidiMessageType.PROGRAM_CHANGE.value]:
            new_channel = self.channel_map.get(msg.channel, msg.channel)
            return replace(msg, channel=new_channel)
        return None
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "type": self.type,
            "channel_map": self.channel_map,
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        channel_map = data.get("channel_map", {})
        return cls(channel_map=channel_map)