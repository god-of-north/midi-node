from enum import Enum
from .int_selector_state import IntNumberSelectorState
from .string_creator_state import StringCreatorState
from .boolean_selector_state import BooleanSelectorState
from .enum_selector_state import EnumSelectorState
from actions import ActionParam

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

    def return_to_previous(self, deep: int = 1):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()   

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

    def return_to_previous(self, deep: int = 1):
        # Update the action parameter before returning
        self.param.value = self._get_string()
        super().return_to_previous()

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

    def return_to_previous(self, deep: int = 1):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()

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

    def return_to_previous(self, deep: int = 1):
        # Update the action parameter before returning
        self.param.value = self.get_value()
        super().return_to_previous()
