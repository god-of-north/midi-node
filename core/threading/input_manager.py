import threading
import queue
import logging
import time

from storage.app_config import AppConfig

class InputManager(threading.Thread):
    """Monitors GPIO pins and puts events into the queue."""
    def __init__(self, event_queue: queue.Queue, shutdown_event: threading.Event, input_handlers: list, config: AppConfig):
        super().__init__(daemon=True)
        self.queue = event_queue
        self.shutdown = shutdown_event
        self.input_handlers = input_handlers if input_handlers is not None else []
        self.config = config


    def run(self):
        logging.info("Input Thread Started")

        # All input handlers should be initialized and ready to tick
        # Their 'start' logic (setup) should be in their __init__ or a separate setup method
        while not self.shutdown.is_set():
            for handler in self.input_handlers:
                handler.tick()
            time.sleep(self.config.input_poll_interval) # Control the overall polling rate

        for handler in self.input_handlers:
            handler.stop()

        logging.info("Input Thread Shutting Down")
