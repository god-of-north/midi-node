from enum import Enum, auto
from typing import List
from .action import Action, ActionParam
from .midi_action import MIDIAction

class PCAction(MIDIAction):
    TYPE = "pc"
    TITLE = "Send PC"

    def __init__(self, pc:int = 0, **kwargs):
        super().__init__(**kwargs)
        self.params["pc"] = ActionParam("pc", int, pc, default=0, options={"min_value":0, "max_value":127, "header":"Program Change"})

    def execute(self, **kwargs):
        # self.context.show_info(f"MIDI PC {self.params['pc'].value}")
        self.context.send_pc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, self.params["pc"].value)


class ChangePCDirection(Enum):
    NEXT = auto()
    PREVIOUS = auto()

class ChangePCStyle(Enum):
    CYCLE = auto()
    END_TO_END = auto()

class ChangePCAction(MIDIAction):
    TYPE = "change_pc"
    TITLE = "Change PC"

    change_slots = {}

    def __init__(self, direction:ChangePCDirection=ChangePCDirection.NEXT, slot:int=0, min_pc:int=0, max_pc:int=127, style:ChangePCStyle=ChangePCStyle.CYCLE, **kwargs):
        super().__init__(**kwargs)

        if isinstance(direction, str):
            direction = ChangePCDirection[direction]
        if isinstance(style, str):
            style = ChangePCStyle[style]

        self.params["direction"] = ActionParam("direction", ChangePCDirection, direction, default=ChangePCDirection.NEXT)
        self.params["slot"] = ActionParam("slot", int, slot, default=0, options={"min_value":0, "max_value":100, "header":"Toggle Slot"})
        self.params["min_pc"] = ActionParam("min_pc", int, min_pc, default=0, options={"min_value":0, "max_value":127, "header":"Min PC"})
        self.params["max_pc"] = ActionParam("max_pc", int, max_pc, default=127, options={"min_value":0, "max_value":127, "header":"Max PC"})
        self.params["style"] = ActionParam("style", ChangePCStyle, style, default=ChangePCStyle.CYCLE)

    def execute(self, **kwargs):
        direction = self.params["direction"].value
        slot = self.params["slot"].value
        max_pc = self.params["max_pc"].value
        min_pc = self.params["min_pc"].value
        style = self.params["style"].value

        next_pc_index = self.change_slots.get(slot, 0)
        if direction == ChangePCDirection.NEXT:
            next_pc_index += 1
            if next_pc_index > max_pc:
                next_pc_index = max_pc if style == ChangePCStyle.END_TO_END else min_pc
        else:
            next_pc_index -= 1
            if next_pc_index < min_pc:
                next_pc_index = min_pc if style == ChangePCStyle.END_TO_END else max_pc
        self.change_slots[slot] = next_pc_index

        # self.context.show_info(f"Change PC Slot {slot} {'Next' if direction == ChangePCDirection.NEXT else 'Previous'}: {next_pc_index}")
        self.context.send_pc(self.params["output"].value, self.params["port_name"].value, self.params["channel"].value, next_pc_index)

