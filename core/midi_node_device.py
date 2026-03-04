import threading
import queue
import logging

from storage.app_config import AppConfig
from .device_context import DeviceContext
from .threading.input_manager import InputManager
from .threading.ui_manager import UIManager
from display.mock_lcd import MockLCD
from ui.states.home_state import HomeState

class MidiNodeDevice:
    def __init__(self):
        # logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')
        logging.basicConfig(level=logging.ERROR, format='%(threadName)s: %(message)s')
        

        # Event Queues and Shutdown Event
        self.event_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()

        self.context = DeviceContext(self.event_queue, self.ui_queue)

        if self.context.data.config.app_mode == AppConfig.SIMULATION:
            self.lcd = MockLCD()
            self.lcd.clear()

            self.input_thread = InputManager(self.event_queue, self.shutdown_event, self.context.data.preset.controls)

        self.ui_thread = UIManager(self.ui_queue, self.lcd, self.shutdown_event)
    
        self.context.state.push_state(HomeState(self.context))

    
    # Main Loop

    def start(self):
        self.input_thread.start()
        self.ui_thread.start()
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.stop()

    def _main_loop(self):
        while not self.shutdown_event.is_set():
            try:
                event = self.event_queue.get(timeout=0.5)
                self.context.state.current_state.handle_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        logging.info("Stopping MIDI Node...")
        self.shutdown_event.set()
        self.input_thread.join()
        self.ui_thread.join()
        logging.info("MIDI Node Stopped Cleanly")
