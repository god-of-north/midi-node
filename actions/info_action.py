from core.align_text import AlignText
from .action import Action, ActionParam

class InfoAction(Action):
    TYPE = "info"
    TITLE = "Show Info"

    def __init__(self, info:str = "Info", line:int=2, clear_scr:bool=False, align:AlignText=AlignText.CENTER, **kwargs):
        super().__init__(**kwargs)
        self.params["info"] = ActionParam("info", str, info)
        self.params["line"] = ActionParam("line", int, line, default=1, options={"min_value":1, "max_value":4, "header":"Line"})
        self.params["clear_scr"] = ActionParam("clear_scr", bool, clear_scr, default=False, options={"header":"Clear Screen"})
        self.params["align"] = ActionParam("align", AlignText, align, default=False, options={"header":"Align"})

    def execute(self, **kwargs):

        info = self.params["info"].value
        for key, value in kwargs.items():
            info = info.replace(f"__{key}__", str(value))

        self.context.show_info(info, line=self.params["line"].value, clear_screen=self.params["clear_scr"].value, align=self.params["align"].value)

