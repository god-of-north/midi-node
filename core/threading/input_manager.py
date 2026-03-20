import threading
import queue
import logging
from ..device_event import DeviceEvent, EventType
from input.button_event import ButtonEvent

class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event, input_handler=None):
        super().__init__(daemon=True)
        self.queue = event_queue
        self.shutdown = shutdown_event
        self.input_handler = input_handler


    def run(self):
        logging.info("Input Thread Started")

        self.input_handler.start(self.shutdown.is_set)

        logging.info("Input Thread Shutting Down")
