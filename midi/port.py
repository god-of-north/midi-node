from midi.midi_output_type import MidiOutputType


from dataclasses import dataclass


@dataclass
class Port:
    port_name: str
    type: MidiOutputType

    def to_dict(self):
        return {
            "port_name": self.port_name,
            "type": self.type.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        port_name = data.get("port_name")
        type_value = data.get("type")
        type_enum = MidiOutputType(type_value) if type_value else None
        return cls(port_name=port_name, type=type_enum)