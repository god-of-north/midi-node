import threading
import queue
import logging
from ..device_event import EventType
from display.display_provider import DisplayProvider

class UIManager(threading.Thread):
    """Consumes UI events and controls the LCD hardware."""
    def __init__(self, ui_queue: queue.Queue, display: DisplayProvider, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.queue = ui_queue
        self.display = display
        self.shutdown = shutdown_event
        self.current_state = {"line1": "System Ready", "line2": "Waiting..."}
        self.out_data = {"x": 0, "y": 0, "set_pos": False, "str": ""}

    def run(self):
        logging.info("UI Thread Started")
        while not self.shutdown.is_set():
            try:
                # Block for 0.5s to keep the loop responsive to shutdown
                event = self.queue.get(timeout=0.5)
                
                if event.type == EventType.LCD_TEXT:
                    self.out_data.update(event.data)
                    self.display.write_string(self.out_data['str'], self.out_data['x'], self.out_data['y'], self.out_data['set_pos'])
                elif event.type == EventType.LCD_CLEAR:
                    self.display.clear()

                self.queue.task_done()
            except queue.Empty:
                continue
        
        self.display.clear()
        logging.info("UI Thread Shutting Down")
