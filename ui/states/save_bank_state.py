from ui.states.list_item_replace_state import ListItemReplaceState
from ui.states.string_creator_state import StringCreatorState


import time


class SaveBankState(StringCreatorState):
    def __init__(self, context):
        super().__init__(
            context,
            value=context.data.bank.name,
            characters="_ ABCDEFGHIJKLMNOPQRSTUVWXYZ_ abcdefghijklmnopqrstuvwxyz _0123456789 _",
            header="Save Bank As:",
            centered=False,
        )
        self.saved = False

    def return_to_previous(self, deep: int = 1):
        bank_name = self._get_string().strip()
        self.transition_to(ListItemReplaceState,
                           items=[f"{b['name']}" for b in self.context.data.bank_list],
                           element_name=bank_name,
                           current_index=self.context.data.current_bank_index,
                           callback=self.save_bank,
                           return_to_previous_depth=2)

    def save_bank(self, index: int):
        bank_name = self._get_string().strip()
        if bank_name:
            self.context.data.bank.name = bank_name
            self.context.data.current_bank_index = index

            # Save to storage
            self.context.data.storage.save_bank(index, self.context.data.bank)
            self.context.data.storage.save_current_bank_index(index)

            # Show confirmation
            self.context.ui.clear_ui()
            self.context.ui.write_ui(f"Bank Saved as \r\n'{bank_name}'", 0, 1, True)
            time.sleep(1.5)