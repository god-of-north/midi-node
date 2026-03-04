import threading
import queue
import logging
from ..device_event import DeviceEvent, EventType
from input.keyboard_input_manager import KeyboardInputManager
from input.button_event import ButtonEvent
from controls.control import Control

class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event, controls:dict):
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
