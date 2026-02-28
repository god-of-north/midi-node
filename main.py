import threading
import queue
import time
import logging
import signal
from enum import Enum, auto
from abc import ABC, abstractmethod
from input import KeyboardInputManager,ButtonEvent
from MockLCD import CharLCD
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Union


class ActionParam:
    def __init__(self, name: str, param_type: type, value, default=None, options:dict={}):
        self.name = name
        self.param_type = param_type
        self.value = value
        self.default = default
        self.options = options or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "param_type": self.param_type.__name__,
            "value": self.value,
            "default": self.default,
            "options": self.options
        }
    
    def __dict__(self):
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ActionParam':
        param_type = eval(data["param_type"])
        return cls(
            name=data["name"],
            param_type=param_type,
            value=data["value"],
            default=data.get("default"),
            options=data.get("options", {})
        )

class ActionRegistryEntry:
    def __init__(self, action_type: str, action_cls: Type['Action'], title: str):
        self.action_type = action_type
        self.action_cls = action_cls
        self.title = title

class ActionRegistry:
    """A dedicated registry to keep the global namespace clean."""
    _registry: Dict[str, ActionRegistryEntry] = {}

    @classmethod
    def register(cls, action_type: str, action_cls: Type['Action'], title: str):
        cls._registry[action_type] = ActionRegistryEntry(action_type, action_cls, title)

    @classmethod
    def get_class(cls, action_type: str) -> Optional[Type['Action']]:
        entry = cls._registry.get(action_type)
        return entry.action_cls if entry else None

    @classmethod
    def get_registered(cls, action_type: str) -> Optional[ActionRegistryEntry]:
        entry = cls._registry.get(action_type)
        return entry if entry else None
    
    @classmethod
    def get_keys(cls) -> List[str]:
        return list(cls._registry.keys())


class Action:
    TYPE = "base"
    TITLE = "Base Action"

    def __init__(self, context: 'DeviceContext', **kwargs):
        self.context = context
        self.params: dict[str, ActionParam] = kwargs.get("params", {})

    def __init_subclass__(cls, **kwargs):
        """
        Automatically called when any subclass is defined.
        Registers the subclass in the ActionRegistry.
        """
        super().__init_subclass__(**kwargs)
        if cls.TYPE != "base":
            ActionRegistry.register(cls.TYPE, cls, cls.TITLE)

    def execute(self):
        raise NotImplementedError

    def to_dict(self) -> dict:
        result = {"type": self.TYPE}
        
        for param in self.params.values():
            if hasattr(param.value, "to_dict"):
                result[param.name] = param.value.to_dict()
            elif isinstance(param.value, list):
                result[param.name] = self.list_to_dict(param.value)
            else:
                result[param.name] = param.value

        return result
    
    def list_to_dict(self, items: List[Any]) -> List[dict]:
        result = []
        for item in items:
            if hasattr(item, "to_dict"):
                result.append(item.to_dict())
            else:
                result.append(item)
        return result

    @staticmethod
    def from_dict(data: dict, context: 'DeviceContext') -> 'Action':
        action_type = data.get("type")
        action_cls = ActionRegistry.get_class(action_type)

        if not action_cls:
            # Fallback to base or raise error if type is unknown
            print(f"Warning: Unknown action type '{action_type}'. Using base Action.")
            return Action(context=context)

        return action_cls(context=context, **data)

    def __str__(self):
        return self.TITLE

class InfoAction(Action):
    TYPE = "info"
    TITLE = "Show Info"

    def __init__(self, info:str = "Info", **kwargs):
        super().__init__(**kwargs)
        self.params["info"] = ActionParam("info", str, info)

    def execute(self):
        self.context.show_info(self.params["info"].value)
   
class CCAction(Action):
    TYPE = "cc"
    TITLE = "Send CC"

    def __init__(self, cc:int = 127, **kwargs):
        super().__init__(**kwargs)
        self.params["cc"] = ActionParam("cc", int, cc, default=127, options={"min_value":0, "max_value":127, "header":"Control Change"})

    def execute(self):
        self.context.show_info(self.params["cc"].value)

class PCAction(Action):
    TYPE = "pc"
    TITLE = "Send PC"

    def __init__(self, pc:int = 0, **kwargs):
        super().__init__(**kwargs)
        self.params["pc"] = ActionParam("pc", int, pc, default=0, options={"min_value":0, "max_value":127, "header":"Program Change"})

    def execute(self):
        self.context.show_info(self.params["pc"].value)

class CompositeAction(Action):
    TYPE = "composite"
    TITLE = "Composite Action"

    def __init__(self, actions:List[Action]=[], **kwargs):
        super().__init__(**kwargs)

        fixed_actions = []
        for action in actions:
            if isinstance(action, Action):
                fixed_actions.append(action)
            if isinstance(action, dict):
                action = self.create_action_by_type(action["type"], action)
                fixed_actions.append(action)

        self.params["actions"] = ActionParam("actions", list, fixed_actions, default=[], 
                                             options={"class_type": Action, 
                                                      "creator_func": self.create_action_by_type, 
                                                      "creator_items_func": self.get_creator_items})

    def execute(self):
        for action in self.params["actions"].value:
            action.execute()

    def get_creator_items(self):
        return list(ActionRegistry.get_keys())
    
    def create_action_by_type(self, action_type:str, data:dict={}) -> Optional[Action]:
        action_info = ActionRegistry.get_registered(action_type)
        if action_info:
            return action_info.action_cls(context=self.context, **data)
        return None

class Control(Enum):
    BUTTON_1 = auto()
    BUTTON_2 = auto()
    BUTTON_3 = auto()
    BUTTON_4 = auto()
    EXP_PEDAL_1 = auto()
    EXP_PEDAL_2 = auto()



class PotEvent(Enum):
    CHANGE_VALUE = auto()
    CHANGE_DIRECTION = auto()
    ON_MIN = auto()
    LEAVE_MIN = auto()
    ON_MAX = auto()
    LEAVE_MAX = auto()
    STOP_CHANGING = auto()


class ControlType(Enum):
    BUTTON = auto()
    POTENTIOMETER = auto()


class BaseControlModel(ABC):
    def __init__(self, control_type: ControlType, actions:Dict[ButtonEvent, Action]={}, context: 'DeviceContext'=None):
        self.control_type = control_type
        self.actions = actions
        self.context = context

    def to_dict(self) -> dict:
        return {
            "control_type": str(self.control_type),
            "actions": {str(k): v.to_dict() for k, v in self.actions.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'BaseControlModel':
        name = data["control_type"].split(".")[-1]
        control_type = ControlType[name]
        if control_type == ControlType.BUTTON:
            instance = ButtonControlModel.from_dict(data, context=context)
        elif control_type == ControlType.POTENTIOMETER:
            instance = PotControlModel.from_dict(data, context=context)
        else:
            instance = cls(control_type)
        return instance

class ButtonControlModel(BaseControlModel):
    def __init__(self, control_type: ControlType, actions:Dict[ButtonEvent, Action]={}, context: 'DeviceContext'=None):
        super().__init__(control_type, actions, context=context)

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'ButtonControlModel':
        actions = {ButtonEvent[k.split(".")[-1]]: Action.from_dict(v, context=context) for k, v in data["actions"].items()}
        instance = cls(control_type=ControlType.BUTTON, actions=actions, context=context)
        return instance

class PotControlModel(BaseControlModel):
    def __init__(self, control_type: ControlType, actions:Dict[PotEvent, Action]={}, context: 'DeviceContext'=None):
        super().__init__(control_type, actions, context=context)

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext') -> 'PotControlModel':
        actions = {PotEvent[k.split(".")[-1]]: Action.from_dict(v, context=context) for k, v in data["actions"].items()}
        instance = cls(control_type=ControlType.POTENTIOMETER, actions=actions, context=context)
        return instance






class Preset:
    def __init__(self, name: str, controls: Dict[Control, BaseControlModel] = None):
        self.name = name
        self.controls = controls or {}

    def to_dict(self):
        return {
            "name": self.name,
            "controls": {str(k): v.to_dict() for k, v in self.controls.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, context: 'DeviceContext'):
        name = data.get("name", "[Unnamed]")
        controls = {}
        for ctrl_name, model_data in data.get("controls", {}).items():
            model = BaseControlModel.from_dict(model_data, context=context)
            member_name = ctrl_name.split(".")[-1]
            controls[Control[member_name]] = model
        return cls(name=name, controls=controls)

class Bank:
    def __init__(self, name: str, preset_numbers: List[int] = None):
        self.name = name
        self.preset_numbers = preset_numbers or []

    def to_dict(self):
        return {"name": self.name, "presets": self.preset_numbers}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(name=data["name"], preset_numbers=data.get("presets", []))

class StorageManager:
    def __init__(self, root_path: str, context: 'DeviceContext'):
        self.root = Path(root_path)
        self.preset_dir = self.root / "presets"
        self.bank_dir = self.root / "banks"
        self.context = context
        
        # Ensure directories exist
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self.bank_dir.mkdir(parents=True, exist_ok=True)

    # --- Internal Utilities ---

    def _get_preset_path(self, number: int) -> Path:
        return self.preset_dir / f"{number:03d}.json"

    def _get_bank_path(self, number: int) -> Path:
        return self.bank_dir / f"{number:03d}.json"

    # --- Preset API ---

    def save_preset(self, number: int, preset: Preset):
        path = self._get_preset_path(number)
        with open(path, 'w') as f:
            preset_dict = preset.to_dict()
            json.dump(preset_dict, f, indent=4)

    def load_preset(self, number: int) -> Optional[Preset]:
        path = self._get_preset_path(number)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return Preset.from_dict(json.load(f), context=self.context)

    def get_preset_list(self) -> List[dict]:
        """Returns list of {number: int, name: str}"""
        presets = []
        for file in sorted(self.preset_dir.glob("*.json")):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    presets.append({
                        "number": int(file.stem),
                        "name": data.get("name", "Unnamed")
                    })
            except Exception as e:
                print(f"Error loading preset file {file}: {e}")
                presets.append({
                    "number": int(file.stem),
                    "name": "Error"
                })
        return presets

    def reorder_presets(self, source_num: int, target_num: int, mode: str = "move"):
        """
        Handles moving/cloning and triggers bank updates.
        mode: 'move' (renames) or 'clone' (copies)
        """
        source_path = self._get_preset_path(source_num)
        target_path = self._get_preset_path(target_num)

        if not source_path.exists():
            raise FileNotFoundError(f"Source preset {source_num} not found.")

        # If target exists, we shift everything or overwrite? 
        # Expert choice: Let's implement a clean move and notify banks.
        if mode == "move":
            shutil.move(str(source_path), str(target_path))
            self._update_banks_on_preset_change(source_num, target_num)
        else:
            shutil.copy(str(source_path), str(target_path))

    def remove_preset(self, number: int):
        path = self._get_preset_path(number)
        if path.exists():
            os.remove(path)
            self._update_banks_on_preset_change(number, None) # None = Deleted

    def save_current_preset_index(self, preset_number: int):
        path = self.root / "current_preset.txt"
        with open(path, 'w') as f:
            f.write(str(preset_number))
    
    def load_current_preset_index(self) -> Optional[int]:
        path = self.root / "current_preset.txt"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return int(f.read().strip())


    # --- Bank API ---

    def create_bank(self, number: int, name: str):
        bank = Bank(name=name)
        self.save_bank(number, bank)

    def save_bank(self, number: int, bank: Bank):
        path = self._get_bank_path(number)
        with open(path, 'w') as f:
            json.dump(bank.to_dict(), f, indent=4)

    def load_bank(self, number: int) -> Optional[Bank]:
        path = self._get_bank_path(number)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return Bank.from_dict(json.load(f))

    def get_bank_list(self) -> List[dict]:
        banks = []
        for file in sorted(self.bank_dir.glob("*.json")):
            with open(file, 'r') as f:
                data = json.load(f)
                banks.append({
                    "number": int(file.stem),
                    "name": data.get("name", "Unnamed")
                })
        return banks

    def save_current_bank_index(self, bank_number: int):
        path = self.root / "current_bank.txt"
        with open(path, 'w') as f:
            f.write(str(bank_number))

    def load_current_bank_index(self) -> Optional[int]:
        path = self.root / "current_bank.txt"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return int(f.read().strip())


    # --- Integrity Logic ---

    def _update_banks_on_preset_change(self, old_num: int, new_num: Optional[int]):
        """
        Scans all banks and updates references if a preset moved or was deleted.
        """
        for bank_file in self.bank_dir.glob("*.json"):
            bank_id = int(bank_file.stem)
            bank = self.load_bank(bank_id)
            
            if old_num in bank.preset_numbers:
                # Replace or Remove
                updated_list = []
                for p_num in bank.preset_numbers:
                    if p_num == old_num:
                        if new_num is not None:
                            updated_list.append(new_num)
                    else:
                        updated_list.append(p_num)
                
                bank.preset_numbers = updated_list
                self.save_bank(bank_id, bank)












class DeviceState(ABC):
    def __init__(self, context: 'DeviceContext'):
        self.context = context  # Reference to the MidiNodeDevice

    @abstractmethod
    def on_enter(self):
        """Called when switching TO this state."""
        pass

    @abstractmethod
    def handle_event(self, event):
        """Logic for input events while in this state."""
        pass

    def transition_to(self, new_state_class, **kwargs):
        """Helper to switch states."""
        self.context.state.push_state(new_state_class(self.context, **kwargs))

    def return_to_previous(self, deep: int = 1):
        """Helper to go back to the previous state."""
        self.context.state.pop_state(deep)

class HomeState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("LIVE MODE\r\n\r\n\r\nPress [Select] to Setup", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.transition_to(SettingsMenuState)
        elif event.type == EventType.INFO_MESSAGE:
            info = event.data.get("info", "")
            self.context.ui.write_ui(f"[{info}]".center(20), 0, 1, True)

class MenuState(DeviceState):
    MAX_LINES = 4

    def __init__(self, context, items:List[str]=None):
        super().__init__(context)

        self.items = items or ["Back"]

        self.origin_x = 0
        self.origin_y = 0

        self.selected_index = 0   # index in items
        self.scroll_offset = 0    # first visible item index


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Draw menu with selector.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line

            cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.context.ui.write_ui(" " * 20, cursor_pos[0], cursor_pos[1], True)
                continue

            prefix = ">" if item_index == self.selected_index else " "
            text = f"{prefix} {self.items[item_index]}"

            # Clear line leftovers
            self.context.ui.write_ui(text.ljust(20), cursor_pos[0], cursor_pos[1], True)

    def _down(self) -> None:
        """
        Move cursor down. Scroll if needed.
        """
        if self.selected_index >= len(self.items) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset += 1

        self._refresh_display()

    def _up(self) -> None:
        """
        Move cursor up. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected element.
        """
        return self.items[self.selected_index]

class DummyState(DeviceState):
    def on_enter(self):
        self.context.ui.clear_ui()
        self.context.ui.write_ui("DUMMY STATE\r\nNo Actions", 0, 0, True)

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

class IntNumberSelectorState(DeviceState):
    LINE_WIDTH = 20

    def __init__(
        self,
        context,
        min_value: int = 0,
        max_value: int = 100,
        value: int = 0,
        header: str = "Integer Selector"
    ):
        super().__init__(context)

        self.min_value = min_value
        self.max_value = max_value
        self.header = header

        self.origin_x = 0
        self.origin_y = 0

        self.value = value

        # Pre-calc width for zero-padded numbers (optional but nice)
        self._num_width = len(str(max(abs(min_value), abs(max_value))))


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Draw header and current integer value.
        """
        # Header
        self.context.ui.write_ui(self.header.ljust(self.LINE_WIDTH), self.origin_x, self.origin_y, True)

        # Value line
        formatted = self._format_value(self.value)
        value_line = f"< {formatted} >".center(self.LINE_WIDTH)

        self.context.ui.write_ui(value_line[:self.LINE_WIDTH], self.origin_x, self.origin_y + 1, True)

        # Clear remaining lines
        for i in range(2, 4):
            self.context.ui.write_ui(" " * self.LINE_WIDTH, self.origin_x, self.origin_y + i, True)

    def _next(self) -> None:
        """
        Increment value by 1 (cyclic).
        """
        if self.value >= self.max_value:
            self.value = self.min_value
        else:
            self.value += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Decrement value by 1 (cyclic).
        """
        if self.value <= self.min_value:
            self.value = self.max_value
        else:
            self.value -= 1

        self._refresh_display()

    def get_value(self) -> int:
        """
        Return current integer value.
        """
        return self.value

    def _format_value(self, value: int) -> str:
        """
        Format value for display (zero-padded).
        """
        sign = "-" if value < 0 else ""
        return f"{sign}{abs(value):0{self._num_width}d}"

class ActionParamIntSelectorState(IntNumberSelectorState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != int:
            raise ValueError(f"Parameter '{param.name}' is not a valid integer parameter.")

        super().__init__(
            context,
            min_value=param.options.get("min_value", 0),
            max_value=param.options.get("max_value", 100),
            value=param.value,
            header=param.options.get("header", f"Set {param.name.capitalize()}:")
        )
        self.param = param

    def return_to_previous(self):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()   

class StringCreatorState(DeviceState):
    VISIBLE_WIDTH = 20

    def __init__(
        self,
        context,
        value: str = "",
        characters: str = "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _",
        header: str = "Create String:",
        centered: bool = True,
    ):
        super().__init__(context)

        self.origin_x = 0
        self.origin_y = 0
        self.centered = centered
        self.characters: List[str] = list("√←" + characters)
        self.selected_index = 0
        self.scroll_offset = 0
        self.header = header

        self.chars: List[str] = list(value)

    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._next()
        elif event.type == EventType.ENCODER_CCW:
            self._prev()
        elif event.type == EventType.ENCODER_SELECT:
            if self._get_selected() == "√":
                self.return_to_previous()
            elif self._get_selected() == "←":
                self._backspace()
            else:
                self._add_char()

    def _refresh_display(self) -> None:
        # Header
        self.context.ui.write_ui(self.header.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y, True)

        # Characters line
        visible_chars = self._get_visible_chars()
        self.context.ui.write_ui("".join(visible_chars).ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 1, True)

        # Cursor line
        cursor_x = self.selected_index - self.scroll_offset
        cursor_line = " " * cursor_x + "^"
        self.context.ui.write_ui(cursor_line.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 2, True)

        # Draw the current string.
        current_string = "".join(self.chars)

        if self.centered:
            self.context.ui.write_ui(current_string.center(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)
        else:
            self.context.ui.write_ui(current_string.ljust(self.VISIBLE_WIDTH), self.origin_x, self.origin_y + 3, True)

    def _add_char(self) -> None:
        """
        Add currently selected character to the string.
        """
        selected_char = self._get_selected()
        self.chars.append(selected_char)
        self._refresh_display()

    def _backspace(self) -> None:
        """
        Remove last character from the string.
        """
        if not self.chars:
            return

        self.chars.pop()
        self._refresh_display()

    def _get_string(self) -> str:
        """
        Return the current string.
        """
        return "".join(self.chars)
    
    def _next(self) -> None:
        """
        Move cursor right. Scroll if needed.
        """
        if self.selected_index >= len(self.characters) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.VISIBLE_WIDTH:
            self.scroll_offset += 1

        self._refresh_display()

    def _prev(self) -> None:
        """
        Move cursor left. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected character.
        """
        return self.characters[self.selected_index]

    def _get_visible_chars(self) -> List[str]:
        end = self.scroll_offset + self.VISIBLE_WIDTH
        return self.characters[self.scroll_offset:end]

class ActionParamStringSelectorState(StringCreatorState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != str:
            raise ValueError(f"Parameter '{param.name}' is not a valid string parameter.")

        super().__init__(
            context,
            value=param.value,
            characters=param.options.get("characters", "_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _"),
            header=param.options.get("header", f"Set {param.name.capitalize()}:"),
            centered=param.options.get("centered", True),
        )
        self.param = param

    def return_to_previous(self):
        # Update the action parameter before returning
        self.param.value = self._get_string()
        super().return_to_previous()

class BooleanSelectorState(MenuState):
    def __init__(self, context, value:bool, true_value:str="True", false_value:str="False"):
        super().__init__(context)
        self.true_value = true_value
        self.false_value = false_value
        self.selected_value = value

        self.transitions = {}
        self.transitions[self.true_value] = True
        self.transitions[self.false_value] = False
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            self.return_to_previous()
        else:
            super().handle_event(event)
    
    def get_value(self) -> bool:
        return self.selected_value
    
class ActionParamBoolSelectorState(BooleanSelectorState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != bool:
            raise ValueError(f"Parameter '{param.name}' is not a valid boolean parameter.")

        super().__init__(
            context,
            value=param.value,
            true_value=param.options.get("true_value", "True"),
            false_value=param.options.get("false_value", "False"),
        )
        self.param = param

    def return_to_previous(self):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()

class EnumSelectorState(MenuState):
    def __init__(self, context, enum_type: type[Enum], value: Enum):
        super().__init__(context)
        self.enum_type = enum_type
        self.selected_value = value

        self.transitions = {}
        for member in enum_type:
            self.transitions[member.name] = member
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            self.return_to_previous()
        else:
            super().handle_event(event)
    
    def get_value(self) -> Enum:
        return self.selected_value

class ActionParamEnumSelectorState(EnumSelectorState):
    def __init__(self, context, param: ActionParam):
        if not param or not issubclass(param.param_type, Enum):
            raise ValueError(f"Parameter '{param.name}' is not a valid enum parameter.")

        super().__init__(
            context,
            enum_type=param.param_type,
            value=param.value,
        )
        self.param = param

class ActionSelectorState(MenuState):
    def __init__(self, context, control_id: Control, control_event: Enum):
        super().__init__(context)

        self.control_id = control_id
        self.control_event = control_event
    
        self.action_types: Dict[str, ActionRegistryEntry] = {}
        action_types = ActionRegistry.get_keys()
        for action_type in action_types:
            action_info = ActionRegistry.get_registered(action_type)
            if action_info:
                self.action_types[action_info.title] = action_info
        self.items = list(self.action_types.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_action_type = self.action_types[selected]

            control = self.context.data.preset.controls.get(self.control_id, None)
            existing_action:Action = control.actions.get(self.control_event, None)
            if not existing_action or existing_action.__class__ != new_action_type.action_cls:
                # Create new action
                control.actions[self.control_event] = new_action_type.action_cls(context=self.context)

            self.return_to_previous()
        else:
            super().handle_event(event)

class BooleanWithCallbackState(BooleanSelectorState):
    def __init__(self, context, value:bool, callback, true_value:str="True", false_value:str="False"):
        super().__init__(context, value, true_value, false_value)
        self.callback = callback

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.selected_value = self.transitions[selected]
            if self.selected_value:
                self.callback(True)
            else:
                self.callback(False)
            self.return_to_previous()
        else:
            super().handle_event(event)

class ListItemCreatorState(MenuState):
    def __init__(self, context, items, item_add_func):
        super().__init__(context, items)
        self.item_add_func = item_add_func

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            self.item_add_func(selected)
            self.return_to_previous()
        else:
            super().handle_event(event)

class ActionParamListEditorState(MenuState):
    def __init__(self, context, param: ActionParam):
        if not param or param.param_type != list:
            raise ValueError(f"Parameter '{param.name}' is not a valid list parameter.")

        super().__init__(context)
        self.param = param
        self.creator_items = param.options.get("creator_items_func")() if "creator_items_func" in param.options else []
        self.creator_func = param.options.get("creator_func") if "creator_func" in param.options else None

    def on_enter(self):
        self.transitions = {}
        for idx, item in enumerate(self.param.value):
            self.transitions[f"{idx+1}:{item.__str__()}"] = {"class": ActionEditorState, "args": {"action": item, "delete_callback": lambda i=item: self.param.value.remove(i)}}
        self.transitions["Add Item"] = {"class": ListItemCreatorState, "args": {"items": self.creator_items, "item_add_func": self._add_item}}
        self.transitions["Back"] = None
        self.items = list(self.transitions.keys())

        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

    def _add_item(self, item_type:str):
        if self.creator_func:
            new_item = self.creator_func(item_type)
            if new_item:
                self.param.value.append(new_item)

class ActionEditorState(MenuState):
    def __init__(self, context, action: Action, delete_callback=None):
        super().__init__(context)
        self.action = action
        self.delete_callback = delete_callback

    def on_enter(self):
        if not self.action:
            self.return_to_previous()
            return

        params = self.action.params

        self.transitions = {}
        for key, param in params.items():
            transition = {"class": DummyState}
            display_value = param.value
            if param.param_type == bool:
                transition = {"class": ActionParamBoolSelectorState, "args": {"param":param}}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param":param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param":param}}
            elif issubclass(param.param_type, Enum):
                transition = {"class": ActionParamEnumSelectorState, "args": {"param":param}}
            elif param.param_type == list:
                display_value = "[]"
                transition = {"class": ActionParamListEditorState, "args": {"param":param}}

            self.transitions[f"{key.capitalize()}: {display_value}"] = transition
        self.transitions["Delete"] = transition = {"class": BooleanWithCallbackState, "args": {"value": False, "callback": self._delete, "true_value": "Confirm Delete", "false_value": "Cancel"}}
        self.transitions["Back to Settings"] = None
        self.items = list(self.transitions.keys())

        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

    def _delete(self, confirmed: bool):
        if confirmed:
            self.delete_callback()
            self.action = None

class ButtonSettingsMenuState(MenuState):
    def __init__(self, context, control_id: Control, control_event: Enum):
        super().__init__(context)
        self.control_id = control_id
        self.control_event = control_event

    def on_enter(self):
        if not self.control_id:
            self.return_to_previous()
            return

        control = self.context.data.preset.controls.get(self.control_id, None)
        if not control:
            self.return_to_previous()
            return
        
        action: Action = control.actions.get(self.control_event, None)
        if not action:
            self.return_to_previous()
            return

        params = action.params

        self.transitions = {}
        self.transitions["Type: "+getattr(action, "TITLE", "Unknown")] = {"class": ActionSelectorState, "args": {"control_id": self.control_id, "control_event": self.control_event}}
        for key, param in params.items():
            transition = {"class": DummyState}
            display_value = param.value
            if param.param_type == bool:
                transition = {"class": ActionParamBoolSelectorState, "args": {"param":param}}
            elif param.param_type == int:
                transition = {"class": ActionParamIntSelectorState, "args": {"param":param}}
            elif param.param_type == str:
                transition = {"class": ActionParamStringSelectorState, "args": {"param":param}}
            elif issubclass(param.param_type, Enum):
                transition = {"class": ActionParamEnumSelectorState, "args": {"param":param}}
            elif param.param_type == list:
                display_value = "[]"
                transition = {"class": ActionParamListEditorState, "args": {"param":param}}

            self.transitions[f"{key.capitalize()}: {display_value}"] = transition
        self.transitions["Back to Settings"] = None
        self.items = list(self.transitions.keys())

        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

class SavePresetState(StringCreatorState):
    def __init__(self, context):
        super().__init__(
            context,
            value=context.data.preset.name,
            characters="_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _",
            header="Save Preset As:",
            centered=False,
        )
        self.saved = False

    def return_to_previous(self):
        preset_name = self._get_string().strip()
        self.transition_to(ListItemReplaceState, 
                           items=[f"{p['name']}" for p in self.context.data.storage.get_preset_list()],
                           element_name=preset_name, 
                           current_index=self.context.data.current_preset_index, 
                           callback=self.save_preset,
                           return_to_previous_depth=2)

    def save_preset(self, index: int):
        preset_name = self._get_string().strip()
        if preset_name:
            self.context.data.preset.name = preset_name
            self.context.data.current_preset_index = index

            # Save to storage
            self.context.data.storage.save_preset(index, self.context.data.preset)
            self.context.data.storage.save_current_preset_index(index)

            # Show confirmation
            self.context.ui.clear_ui()
            self.context.ui.write_ui(f"Preset Saved as \r\n'{preset_name}'", 0, 1, True)
            time.sleep(1.5)

class ControlSettingsMenuState(MenuState):
    def __init__(self, context, control_id:Control):
        super().__init__(context)
        self.control_id = control_id
    
    def on_enter(self):
        control = self.context.data.preset.controls[self.control_id]

        self.transitions = {}
        for control_event in control.actions.keys():
            self.transitions[f"Setup {control_event.name}"] = {"class": ButtonSettingsMenuState, "args": {"control_id": self.control_id, "control_event": control_event}}
        self.transitions["Back"] = None

        self.items = list(self.transitions.keys())
        super().on_enter()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

class SettingsMenuState(MenuState):
    def __init__(self, context):
        super().__init__(context)

        self.transitions = {
            "Setup Button 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_1}},
            "Setup Button 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_2}},
            "Setup Button 3": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_3}},
            "Setup Button 4": {"class": ControlSettingsMenuState, "args": {"control_id": Control.BUTTON_4}},
            "Setup Exp Pedal 1": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_1}},
            "Setup Exp Pedal 2": {"class": ControlSettingsMenuState, "args": {"control_id": Control.EXP_PEDAL_2}},
            "Save Preset": {"class": SavePresetState},
            "Clone Preset": {"class": DummyState},
            "Delete Preset": {"class": DummyState},
            "Back to Live Mode": None
        }
        self.items = list(self.transitions.keys())

    def handle_event(self, event):
        if event.type == EventType.ENCODER_SELECT:
            selected = self._get_selected()
            new_state = self.transitions[selected]
            if new_state is not None:
                self.transition_to(new_state["class"], **new_state.get("args", {}))
            else:
                self.return_to_previous()
        else:
            super().handle_event(event)

class ListOrderingState(DeviceState):
    MAX_LINES = 4
    LINE_WIDTH = 40

    def __init__(self, context, items:List[str]=None, current_index:int=0):
        super().__init__(context)

        self.items = items or ["Back"]

        self.origin_x = 0
        self.origin_y = 0

        self.current_index = 0
        self.scroll_offset = 0

        self._set_current(current_index)


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            self.return_to_previous()

    def _refresh_display(self) -> None:
        """
        Redraw visible part of the list.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line
            self.console.cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.console.write_string(" " * self.LINE_WIDTH)
                continue

            prefix = "> " if item_index == self.current_index else "  "
            text = prefix + self.items[item_index]
            self.console.write_string(text[:self.LINE_WIDTH].ljust(self.LINE_WIDTH))

    def _set_current(self, index: int) -> None:
        """
        Select element by index and ensure it's visible.
        """
        if index < 0 or index >= len(self.items):
            raise IndexError("Index out of range")

        self.current_index = index

        if self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index
        elif self.current_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset = self.current_index - self.MAX_LINES + 1

        self._refresh_display()

    def _down(self) -> None:
        """
        Move selected element down in list.
        """
        if self.current_index >= len(self.items) - 1:
            return

        # Swap elements
        self.items[self.current_index], self.items[self.current_index + 1] = (
            self.items[self.current_index + 1],
            self.items[self.current_index],
        )

        self.current_index += 1

        # Scroll if needed (same rule as Menu)
        if self.current_index >= self.scroll_offset + self.MAX_LINES - 1:
            self.scroll_offset += 1

        self._refresh_display()

    def _up(self) -> None:
        """
        Move selected element up in list.
        """
        if self.current_index <= 0:
            return

        # Swap elements
        self.items[self.current_index], self.items[self.current_index - 1] = (
            self.items[self.current_index - 1],
            self.items[self.current_index],
        )

        self.current_index -= 1

        if self.current_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def get_list(self) -> List[str]:
        """
        Return reordered list.
        """
        return self.items

class ListItemReplaceState(DeviceState):
    MAX_LINES = 4

    def __init__(self, context, items:List[str]=None, current_index:int=0, element_name:str="Item", callback=None, return_to_previous_depth:int=1):
        super().__init__(context)

        self.callback = callback
        self.items = items or ["Back"]
        self.origin_x = 0
        self.origin_y = 0

        self.selected_index = current_index
        self.scroll_offset = 0
        self.element_name = element_name
        self.return_to_previous_depth = return_to_previous_depth


    def on_enter(self):
        self.context.ui.clear_ui()
        self._refresh_display()

    def handle_event(self, event):
        if event.type == EventType.ENCODER_CW:
            self._up()
        elif event.type == EventType.ENCODER_CCW:
            self._down()
        elif event.type == EventType.ENCODER_SELECT:
            if self.callback:
                index = self._get_index()
                self.callback(index)
            self.return_to_previous(self.return_to_previous_depth)

    def _refresh_display(self) -> None:
        """
        Draw menu with selector.
        """
        for line in range(self.MAX_LINES):
            item_index = self.scroll_offset + line

            cursor_pos = (self.origin_x, self.origin_y + line)

            if item_index >= len(self.items):
                self.context.ui.write_ui(" " * 20, cursor_pos[0], cursor_pos[1], True)
                continue

            is_selected = item_index == self.selected_index
            item_name = self.element_name if is_selected else self.items[item_index]
            line_text = f"{item_index:3d}: {item_name}"
            prefix = ">" if is_selected else " "
            text = f"{prefix} {line_text}"

            # Clear line leftovers
            self.context.ui.write_ui(text.ljust(20), cursor_pos[0], cursor_pos[1], True)

    def _down(self) -> None:
        """
        Move cursor down. Scroll if needed.
        """
        if self.selected_index >= len(self.items) - 1:
            return

        self.selected_index += 1

        if self.selected_index >= self.scroll_offset + self.MAX_LINES:
            self.scroll_offset += 1

        self._refresh_display()

    def _up(self) -> None:
        """
        Move cursor up. Scroll if needed.
        """
        if self.selected_index <= 0:
            return

        self.selected_index -= 1

        if self.selected_index < self.scroll_offset:
            self.scroll_offset -= 1

        self._refresh_display()

    def _get_selected(self) -> str:
        """
        Return currently selected element.
        """
        return self.items[self.selected_index]
    
    def _get_index(self) -> int:
        """
        Return currently selected index.
        """
        return self.selected_index





class EventType(Enum):
    SYSTEM_SHUTDOWN = auto()
    LCD_TEXT = auto()
    LCD_CLEAR = auto()
    ENCODER_CW = auto()
    ENCODER_CCW = auto()
    ENCODER_SELECT = auto()
    INFO_MESSAGE = auto()

class DeviceEvent:
    def __init__(self, event_type: EventType, data=None):
        self.type = event_type
        self.data = data





class DisplayProvider(ABC):
    @abstractmethod
    def clear(self):
        pass
    
    @abstractmethod
    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        pass

class MockLCD(DisplayProvider):
    def __init__(self):
        self.lcd = CharLCD()

    def clear(self):
        self.lcd.clear()

    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        if set_pos:
            self.lcd.cursor_pos = (x, y)
        self.lcd.write_string(text)






class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event, controls:Dict[Control, BaseControlModel]):
        super().__init__(daemon=True)
        self.queue = event_queue
        self.shutdown = shutdown_event
        self.input_handler = KeyboardInputManager()
        self.controls = controls

        def encoder_callback(direction):
            if direction == 1:
                self.queue.put(DeviceEvent(EventType.ENCODER_CW))
            else:
                self.queue.put(DeviceEvent(EventType.ENCODER_CCW))

        self.input_handler.add_encoder('down', "up", encoder_callback)
        self.input_handler.add_button('enter', {ButtonEvent.PRESS: lambda: self.queue.put(DeviceEvent(EventType.ENCODER_SELECT))})

        key_map = {
            Control.BUTTON_1: '1',
            Control.BUTTON_2: '2',
            Control.BUTTON_3: '3',
            Control.BUTTON_4: '4',
        }

        for control, button in key_map.items():
            self.input_handler.add_button(button, {
                ButtonEvent.PRESS: (lambda c=control: self.controls[c].actions[ButtonEvent.PRESS].execute()),
                ButtonEvent.RELEASE: (lambda c=control: self.controls[c].actions[ButtonEvent.RELEASE].execute()),
            })


    def run(self):
        logging.info("Input Thread Started")

        self.input_handler.start(self.shutdown.is_set)

        logging.info("Input Thread Shutting Down")

class UIManager(threading.Thread):
    """Consumes UI events and controls the LCD hardware."""
    def __init__(self, ui_queue: queue.Queue, display: DisplayProvider, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.queue = ui_queue
        self.display = display
        self.shutdown = shutdown_event
        self.current_state = {"line1": "System Ready", "line2": "Waiting..."}
        self.out_data = {"x": 0, "y": 0, "set_pos": False, "str": ""}

    def run(self):
        logging.info("UI Thread Started")
        while not self.shutdown.is_set():
            try:
                # Block for 0.5s to keep the loop responsive to shutdown
                event = self.queue.get(timeout=0.5)
                
                if event.type == EventType.LCD_TEXT:
                    self.out_data.update(event.data)
                    self.display.write_string(self.out_data['str'], self.out_data['x'], self.out_data['y'], self.out_data['set_pos'])
                elif event.type == EventType.LCD_CLEAR:
                    self.display.clear()

                self.queue.task_done()
            except queue.Empty:
                continue
        
        self.display.clear()
        logging.info("UI Thread Shutting Down")




class DataContext:
    def __init__(self, device_context: 'DeviceContext'):
        self.storage = StorageManager("./data", context=device_context)

        self.bank_list = self.storage.get_bank_list()
        self.current_bank_index = self.storage.load_current_bank_index()
        self.preset_list = self.storage.get_preset_list()
        self.current_preset_index = self.storage.load_current_preset_index()
        
        if self.current_bank_index is not None:
            self.bank = self.storage.load_bank(self.current_bank_index) 
        else:
            self.bank = Bank(name="Default Bank", preset_numbers=[0])
            self.current_bank_index = 0

        if self.current_preset_index is not None:
            self.preset = self.storage.load_preset(self.current_preset_index) 
        else:
            controls = {
                Control.BUTTON_1: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 1 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 1 Released", context=device_context),
                }),
                Control.BUTTON_2: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 2 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 2 Released", context=device_context),
                }),
                Control.BUTTON_3: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 3 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 3 Released", context=device_context),
                }),
                Control.BUTTON_4: ButtonControlModel(control_type=ControlType.BUTTON, actions={
                    ButtonEvent.PRESS: InfoAction(info="Button 4 Pressed", context=device_context),
                    ButtonEvent.RELEASE: InfoAction(info="Button 4 Released", context=device_context),
                }),
                Control.EXP_PEDAL_1: PotControlModel(control_type=ControlType.POTENTIOMETER, actions={
                    PotEvent.CHANGE_VALUE: InfoAction(info="Exp Pedal 1 Active", context=device_context),
                    PotEvent.ON_MIN: InfoAction(info="Exp Pedal 1 Inactive", context=device_context),
                }),
                Control.EXP_PEDAL_2: PotControlModel(control_type=ControlType.POTENTIOMETER, actions={
                    PotEvent.CHANGE_VALUE: InfoAction(info="Exp Pedal 2 Active", context=device_context),
                    PotEvent.ON_MIN: InfoAction(info="Exp Pedal 2 Inactive", context=device_context),
                }),
            }

            self.preset = Preset(name="Default Preset", controls=controls)
            self.current_preset_index = 0

    def save_current_preset(self):
        self.storage.save_preset(self.current_preset_index, self.preset)

class UIContext:
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def write_ui(self, text, x=0, y=0, set_pos=False):
        """Helper to write text to the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_TEXT, data={"x": x, "y": y, "str": text, "set_pos": set_pos}))

    def clear_ui(self):
        """Helper to clear the UI display."""
        self.ui_queue.put(DeviceEvent(EventType.LCD_CLEAR))

class StateContext:
    def __init__(self, device_context: 'DeviceContext'):
        self.context = device_context
        self._state_stack = []

    @property
    def current_state(self) -> DeviceState:
        return self._state_stack[-1] if self._state_stack else None

    def push_state(self, new_state: DeviceState):
        """Go deeper into a menu."""
        logging.info(f"Transitioning to {type(new_state).__name__}")
        self._state_stack.append(new_state)
        new_state.on_enter()

    def pop_state(self, deep: int = 1):
        """Go back to the previous menu."""
        for _ in range(deep):
            if len(self._state_stack) > 1:
                self._state_stack.pop()

        logging.info(f"Returning to {type(self.current_state).__name__}")
        self.current_state.on_enter()

class DeviceContext:
    def __init__(self, event_queue: queue.Queue, ui_queue: queue.Queue):
        self.data = DataContext(self)
        self.ui = UIContext(ui_queue)
        self.state = StateContext(self)
        self.event_queue = event_queue

    def show_info(self, info: str):
        """Display an informational message"""
        self.event_queue.put(DeviceEvent(EventType.INFO_MESSAGE, data={"info": info}))




class MidiNodeDevice:
    def __init__(self):
        # logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')
        logging.basicConfig(level=logging.ERROR, format='%(threadName)s: %(message)s')
        

        # Event Queues and Shutdown Event
        self.event_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()

        self.context = DeviceContext(self.event_queue, self.ui_queue)

        # Initialize Hardware
        self.lcd = MockLCD()
        self.lcd.clear()

        # Initialize Threads
        self.input_thread = InputManager(self.event_queue, self.shutdown_event, self.context.data.preset.controls)
        self.ui_thread = UIManager(self.ui_queue, self.lcd, self.shutdown_event)
    
        self.context.state.push_state(HomeState(self.context))

    
    # Main Loop

    def start(self):
        self.input_thread.start()
        self.ui_thread.start()
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.stop()

    def _main_loop(self):
        while not self.shutdown_event.is_set():
            try:
                event = self.event_queue.get(timeout=0.5)
                self.context.state.current_state.handle_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        logging.info("Stopping MIDI Node...")
        self.shutdown_event.set()
        self.input_thread.join()
        self.ui_thread.join()
        logging.info("MIDI Node Stopped Cleanly")

if __name__ == "__main__":
    device = MidiNodeDevice()
    device.start()
