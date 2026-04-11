import threading
import queue
import logging

from controls.control import Control
from core.device_event import DeviceEvent, EventType
from input.button_event import ButtonEvent
from config import APP_MODE
from midi.midi_router import MidiRouter
from storage.app_config import AppMode
from .device_context import DeviceContext
from .threading.input_manager import InputManager
from .threading.ui_manager import UIManager
from ui.states.home_state import HomeState
from input import InputHandlerFactory, InputHandlerType
from display import DisplayFactory, DisplayType

class MidiNodeDevice:
    def __init__(self):
        # Event Queues and Shutdown Event
        self.event_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()

        self.midi = MidiRouter()

        self.context = DeviceContext(self.event_queue, self.ui_queue, self.midi)

        input_handlers = []

        if APP_MODE == AppMode.SIMULATION:
            # Input Handler Setup
            keyboard_input_handler = InputHandlerFactory.create_input_handler(InputHandlerType.KEYBOARD, self.context.data.config)
            
            default_key_map = {
                Control.BUTTON_1: '1',
                Control.BUTTON_2: '2',
                Control.BUTTON_3: '3',
                Control.BUTTON_4: '4',
            }

            for control, button in default_key_map.items():
                keyboard_input_handler.add_button(button, {
                    ButtonEvent.PRESS: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.PRESS].execute()),
                    ButtonEvent.RELEASE: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.RELEASE].execute()),
                    ButtonEvent.LONG_PRESS: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.LONG_PRESS].execute()),
                    ButtonEvent.LONG_PRESS_RELEASE: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.LONG_PRESS_RELEASE].execute()),
                    ButtonEvent.TAP: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.TAP].execute()),
                    ButtonEvent.DOUBLE_TAP: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.DOUBLE_TAP].execute()),
                    ButtonEvent.TRIPLE_TAP: (lambda c=control: self.context.data.preset.controls[c].actions[ButtonEvent.TRIPLE_TAP].execute()),
                })

            def encoder_callback(direction):
                if direction == 1:
                    self.event_queue.put(DeviceEvent(EventType.ENCODER_CW))
                else:
                    self.event_queue.put(DeviceEvent(EventType.ENCODER_CCW))

            keyboard_input_handler.add_encoder("down", "up", encoder_callback)
            keyboard_input_handler.add_button("enter", {
                ButtonEvent.PRESS: lambda: self.event_queue.put(DeviceEvent(EventType.ENCODER_SELECT))
            })
            input_handlers.append(keyboard_input_handler)

            # LCD Setup
            self.lcd = DisplayFactory.create_display(DisplayType.CONSOLE)
            self.lcd.clear()
        else:
            # GPIO Input Handler Setup
            gpio_input_handler = InputHandlerFactory.create_input_handler(InputHandlerType.GPIO, self.context.data.config)

            def encoder_callback(direction):
                if direction == 1:
                    self.event_queue.put(DeviceEvent(EventType.ENCODER_CW))
                else:
                    self.event_queue.put(DeviceEvent(EventType.ENCODER_CCW))

            gpio_input_handler.add_encoder(clk_pin=18, dt_pin=17, callback=encoder_callback)
            gpio_input_handler.add_button(pin=27, actions={
                ButtonEvent.PRESS: lambda q=self.event_queue: q.put(DeviceEvent(EventType.ENCODER_SELECT))
            })

            default_key_map = {
                Control.BUTTON_1: 6,  # GPIO_06
                Control.BUTTON_2: 13, # GPIO_13
                Control.BUTTON_3: 19, # GPIO_19
                Control.BUTTON_4: 26, # GPIO_26
            }

            for control, button in default_key_map.items():
                gpio_input_handler.add_button(pin=button, actions={
                    ButtonEvent.PRESS: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.PRESS].execute()),
                    ButtonEvent.RELEASE: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.RELEASE].execute()),
                    ButtonEvent.TAP: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.TAP].execute()),
                    ButtonEvent.DOUBLE_TAP: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.DOUBLE_TAP].execute()),
                    ButtonEvent.TRIPLE_TAP: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.TRIPLE_TAP].execute()),
                    ButtonEvent.LONG_PRESS: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.LONG_PRESS].execute()),
                    ButtonEvent.LONG_PRESS_RELEASE: (lambda c=control, controls=self.context.data.preset.controls: controls[c].actions[ButtonEvent.LONG_PRESS_RELEASE].execute()),
                })
            gpio_input_handler.setup_gpio() # Setup GPIO after all pins are added
            input_handlers.append(gpio_input_handler)

            # ADS1115 Input Handler Setup
            if self.context.data.config.ads1115_enabled:
                ads1115_input_handler = InputHandlerFactory.create_input_handler(InputHandlerType.ADS1115, self.context.data.config)
                
                ads1115_input_handler.add_potentiometer("EXP_PEDAL_1", 0, 
                    self.context.data.preset.controls[Control.EXP_PEDAL_1].actions)
                ads1115_input_handler.add_potentiometer("EXP_PEDAL_2", 1,
                    self.context.data.preset.controls[Control.EXP_PEDAL_2].actions)
                input_handlers.append(ads1115_input_handler)

            # LCD Setup
            self.lcd = DisplayFactory.create_display(DisplayType.LCD2004)
            self.lcd.clear()

        # Input Manager now takes a list of handlers
        self.input_thread = InputManager(self.event_queue, self.shutdown_event, input_handlers=input_handlers, config=self.context.data.config)
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

                logging.info(f"Processing event: {event}")

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
