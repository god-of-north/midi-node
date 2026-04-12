import time
from .string_creator_state import StringCreatorState
from .list_item_replace_state import ListItemReplaceState

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

    def return_to_previous(self, deep: int = 1):
        preset_name = self._get_string().strip()
        self.transition_to(ListItemReplaceState, 
                           items=[f"{p['name']}" for p in self.context.data.preset_list],
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

