from __future__ import annotations
from abc import ABC, abstractmethod

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
