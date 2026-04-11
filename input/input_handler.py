from abc import ABC, abstractmethod


class InputHandler(ABC):
    def add_button(self, key_name, actions, tap_time=0.25, long_press=0.6):
        raise NotImplementedError

    def add_encoder(self, left_key, right_key, callback):
        raise NotImplementedError

    @abstractmethod
    def tick(self):
        """Processes one cycle of input events."""
        pass

    @abstractmethod
    def stop(self):
        """Stops the input handler and releases any resources."""
        pass