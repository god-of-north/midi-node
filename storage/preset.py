from __future__ import annotations
from typing import Dict, List
from actions.action import Action
from actions.empty_action import EmptyAction
from controls import Control, BaseControlModel
from midi.rules.midi_routing_rule import MidiRoutingRule

class Preset:
    def __init__(self, name: str, controls: Dict[Control, BaseControlModel] = None, enter_action: Action = None, exit_action: Action = None, input_midi_rules: List[MidiRoutingRule] = []):
        self.name = name
        self.controls = controls or {}
        self.enter_action = enter_action or EmptyAction(context=None)
        self.exit_action = exit_action or EmptyAction(context=None)
        self.input_midi_rules = input_midi_rules or []

    def to_dict(self):
        return {
            "name": self.name,
            "controls": {str(k): v.to_dict() for k, v in self.controls.items()},
            "enter_action": self.enter_action.to_dict() if self.enter_action else None,
            "exit_action": self.exit_action.to_dict() if self.exit_action else None,
            "input_midi_rules": [rule.to_dict() for rule in self.input_midi_rules],
        }

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        name = data.get("name", "[Unnamed]")
        
        controls = {}
        for ctrl_name, model_data in data.get("controls", {}).items():
            model = BaseControlModel.from_dict(model_data, context=context)
            member_name = ctrl_name.split(".")[-1]
            controls[Control[member_name]] = model

        enter_action_data = data.get("enter_action")
        enter_action = Action.from_dict(enter_action_data, context=context) if enter_action_data else EmptyAction(context=context)

        exit_action_data = data.get("exit_action")
        exit_action = Action.from_dict(exit_action_data, context=context) if exit_action_data else EmptyAction(context=context)

        input_midi_rules_data = data.get("input_midi_rules", [])
        input_midi_rules = [MidiRoutingRule.from_dict(rule_data, context=context) for rule_data in input_midi_rules_data]

        return cls(name=name, controls=controls, enter_action=enter_action, exit_action=exit_action, input_midi_rules=input_midi_rules)

