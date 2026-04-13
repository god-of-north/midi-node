from midi.rules.midi_filter import MidiFilter
from midi.port import Port

from dataclasses import dataclass
from typing import List, Optional
from mido import Message


class MidiRoutingRegistryEntry:
    def __init__(self, rule_type: str, rule_cls):
        self.rule_type = rule_type
        self.rule_cls = rule_cls

class MidiRoutingRegistry:
    _registry: dict[str, MidiRoutingRegistryEntry] = {}

    @classmethod
    def register(cls, rule_cls):
        entry = MidiRoutingRegistryEntry(rule_cls.type, rule_cls)
        cls._registry[entry.rule_type] = entry

    @classmethod
    def get_class(cls, rule_type: str):
        entry = cls._registry.get(rule_type)
        return entry.rule_cls if entry else None


@dataclass
class MidiRoutingRule:
    type: str = "MidiRoutingRule"
    source_port: Port = None
    destination_ports: List[Port] = None
    filters: Optional[MidiFilter] = None


    def __init_subclass__(cls):
        super().__init_subclass__()
        if hasattr(cls, "type"):
            MidiRoutingRegistry.register(cls)

    def is_allowed(self, msg: Message) -> bool:
        if self.filters:
            return self.filters.is_allowed(msg)
        return True

    def apply(self, msg: Message) -> Optional[Message]:
        return None
    
    def to_dict(self):
        return {
            "source_port": self.source_port.to_dict() if self.source_port else None,
            "destination_ports": [port.to_dict() for port in self.destination_ports] if self.destination_ports else [],
            "filters": self.filters.to_dict() if self.filters else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        source_port_data = data.get("source_port")
        source_port = Port.from_dict(source_port_data) if source_port_data else None
        destination_ports_data = data.get("destination_ports", [])
        destination_ports = [Port.from_dict(port_data) for port_data in destination_ports_data]
        filters_data = data.get("filters")
        filters = [filter for filter in (MidiFilter.from_dict(filters_data) if filters_data else [])]

        rule_type = data.get("type")
        rule_cls = MidiRoutingRegistry.get_class(rule_type)
        if rule_cls:
            rule = rule_cls.from_dict(data, context=context)
            rule.source_port = source_port
            rule.destination_ports = destination_ports
            rule.filters = filters
            return rule

        return cls(source_port=source_port, destination_ports=destination_ports, filters=filters)