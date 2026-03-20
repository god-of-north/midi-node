from abc import ABC


class InputHandler(ABC):
    def add_button(self, key_name, actions, tap_time=0.25, long_press=0.6):
        raise NotImplementedError

    def add_encoder(self, left_key, right_key, callback):
        raise NotImplementedError

    def start(self, shutdown_event=None):
        raise NotImplementedError