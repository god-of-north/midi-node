from actions.action import Action
from midi.rules.midi_routing_rule import MidiRoutingRule
from midi.midi_message_type import MidiMessageType


from dataclasses import dataclass
from typing import Optional
from mido import Message, replace


@dataclass
class MidiCommandRemapRule(MidiRoutingRule):
    """Map specific command/value to an action"""
    type: str = "MidiCommandRemapRule"
    trigger_type: MidiMessageType  # e.g., 'control_change'
    trigger_id: int    # e.g., CC #7
    action: Action = None

    def apply(self, msg: Message) -> Optional[Message]:
        if msg.type == self.trigger_type.value:
            if (msg.type == MidiMessageType.CONTROL_CHANGE.value and msg.value == self.trigger_id) or \
                (msg.type == MidiMessageType.PROGRAM_CHANGE.value and msg.program == self.trigger_id) or \
                (msg.type in [MidiMessageType.NOTE_ON.value, MidiMessageType.NOTE_OFF.value] and msg.note == self.trigger_id):
                if self.action:
                    self.action.execute()
        return None
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "type": self.type,
            "trigger_type": self.trigger_type.value,
            "trigger_id": self.trigger_id,
            "action": self.action.to_dict() if self.action else None,
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        trigger_type_str = data.get("trigger_type")
        trigger_id = data.get("trigger_id")
        action_data = data.get("action")

        trigger_type = MidiMessageType(trigger_type_str) if trigger_type_str else None
        action = Action.from_dict(action_data, context=context) if action_data else None

        return cls(
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            action=action
        )