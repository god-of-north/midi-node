from typing import List
from midi.rules.midi_routing_rule import MidiRoutingRule
from mido import Message

from midi.midi_router import MidiRouter


class MidiInputRouter:
    def __init__(self, midi_router: MidiRouter):
        self.rules: List[MidiRoutingRule] = []
        self.midi_router = midi_router

    def add_rule(self, rule: MidiRoutingRule):
        self.rules.append(rule)

    def process_incoming(self, source_port_id: str, msg: Message):
        for rule in self.rules:
            if rule.source_port != source_port_id:
                continue

            if not rule.is_allowed(msg):
                continue

            out_msg = rule.apply(msg)
            if out_msg is None:
                continue
            
            # Dispatch to Outputs
            for dest in rule.destination_ports:
                self.send_to_hardware(dest, out_msg)

    def send_to_hardware(self, port_id: str, msg: Message):
        # Use the MidiRouter to send the message to the specified port
        self.midi_router.send_message(port_id, msg) # TODO: implement send_message in MidiRouter to handle this.