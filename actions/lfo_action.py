import logging
from actions.action import ActionParam
from actions.midi_action import MIDIAction
from midi.midi_output_type import MidiOutputType

from enum import Enum
from threading import Thread, Event
import time
import math
import random
from typing import Dict, Any

# Enums for LFOAction parameters
class LFOActionType(Enum):
    START = "Start"
    STOP = "Stop"

class LFOActionStartDirection(Enum):
    UP = "Up"
    DOWN = "Down"

class LFOActionWaveform(Enum):
    SINE = "Sine"
    TOOTH = "Tooth"
    SQUARE = "Square"
    TRIANGLE = "Triangle"
    RANDOM = "Random"

# Helper class for LFO generation
class LFOGenerator(Thread):
    def __init__(self, context: 'DeviceContext', slot: int, cc: int, min_value: int, max_value: int,
                 start_value: int, start_direction: LFOActionStartDirection, waveform: LFOActionWaveform,
                 lfo_rate: float, cc_rate: int, output: MidiOutputType, port_name: str, channel: int):
        super().__init__()
        self.context = context
        self.slot = slot
        self.cc = cc
        self.min_value = min_value
        self.max_value = max_value
        self.start_value = start_value
        self.start_direction = start_direction
        self.waveform = waveform
        self.lfo_rate = lfo_rate # Hz
        self.cc_rate = cc_rate # Milliseconds
        self.output = output
        self.port_name = port_name
        self.channel = channel

        self._stop_event = Event()
        self._current_value = start_value
        self.daemon = True # Allow program to exit even if thread is running

    def stop(self):
        self._stop_event.set()

    def run(self):
        start_time = time.time()
        # Initial send
        self.context.send_cc(self.output, self.port_name, self.channel, self.cc, int(self._current_value))

        while not self._stop_event.is_set():
            elapsed_time = time.time() - start_time
            period = 1.0 / self.lfo_rate
            phase = (elapsed_time % period) / period

            if self.start_direction == LFOActionStartDirection.DOWN:
                phase = 1.0 - phase

            value_range = self.max_value - self.min_value

            if self.waveform == LFOActionWaveform.SINE:
                # Sine wave from -1 to 1, then scale and offset
                lfo_output = math.sin(2 * math.pi * phase)
                self._current_value = self.min_value + (lfo_output + 1) / 2 * value_range
            elif self.waveform == LFOActionWaveform.TOOTH:
                # Sawtooth wave (rising ramp)
                lfo_output = phase # 0 to 1
                self._current_value = self.min_value + lfo_output * value_range
            elif self.waveform == LFOActionWaveform.SQUARE:
                # Square wave: 0 for first half, 1 for second half
                lfo_output = 1.0 if phase >= 0.5 else 0.0
                self._current_value = self.min_value + lfo_output * value_range
            elif self.waveform == LFOActionWaveform.TRIANGLE:
                # Triangle wave: rises then falls
                if phase < 0.5:
                    lfo_output = phase * 2 # 0 to 1
                else:
                    lfo_output = 1 - (phase - 0.5) * 2 # 1 to 0
                self._current_value = self.min_value + lfo_output * value_range
            elif self.waveform == LFOActionWaveform.RANDOM:
                self._current_value = random.randint(self.min_value, self.max_value)
            
            # Clamp value to MIDI range (0-127) and send
            midi_value = max(0, min(127, int(self._current_value)))
            self.context.send_cc(self.output, self.port_name, self.channel, self.cc, midi_value)
            # self.context.show_info(f"LFO CC {self.cc}:{midi_value}")

            # Wait for next interval
            self._stop_event.wait(self.cc_rate / 1000.0)


class LFOAction(MIDIAction):
    TYPE = "lfo"
    TITLE = "LFO Action"

    _lfo_generators: Dict[int, LFOGenerator] = {} # Global storage for active LFOs

    def __init__(self, context: 'DeviceContext',
                 action_type: LFOActionType = LFOActionType.START,
                 slot: int = 0,
                 cc: int = 0,
                 min_value: int = 0,
                 max_value: int = 127,
                 start_value: int = 64,
                 stop_value: int = 0,
                 start_direction: LFOActionStartDirection = LFOActionStartDirection.UP,
                 waveform: LFOActionWaveform = LFOActionWaveform.SINE,
                 lfo_rate: float = 1.0, # in Hz
                 cc_rate: int = 100, # in milliseconds
                 output: MidiOutputType = MidiOutputType.UART,
                 port_name: str = "/dev/serial0",
                 channel: int = 1,
                 **kwargs):

        super().__init__(context=context, output=output, port_name=port_name, channel=channel, **kwargs)

        if isinstance(action_type, str):
            action_type = LFOActionType[action_type]
        if isinstance(start_direction, str):
            start_direction = LFOActionStartDirection[start_direction]
        if isinstance(waveform, str):
            waveform = LFOActionWaveform[waveform]
        if isinstance(output, str):
            output = MidiOutputType[output]

        self.params["action_type"] = ActionParam("action_type", LFOActionType, action_type, default=LFOActionType.START, options={"header":"LFO Action", "enum_options": [e.value for e in LFOActionType]})
        self.params["slot"] = ActionParam("slot", int, slot, default=0, options={"min_value":0, "max_value":99, "header":"LFO Slot"})
        self.params["cc"] = ActionParam("cc", int, cc, default=0, options={"min_value":0, "max_value":127, "header":"MIDI CC"})
        self.params["min_value"] = ActionParam("min_value", int, min_value, default=0, options={"min_value":0, "max_value":127, "header":"Min Value"})
        self.params["max_value"] = ActionParam("max_value", int, max_value, default=127, options={"min_value":0, "max_value":127, "header":"Max Value"})
        self.params["start_value"] = ActionParam("start_value", int, start_value, default=64, options={"min_value":0, "max_value":127, "header":"Start Value"})
        self.params["stop_value"] = ActionParam("stop_value", int, stop_value, default=0, options={"min_value":0, "max_value":127, "header":"Stop Value"})
        self.params["start_direction"] = ActionParam("start_direction", LFOActionStartDirection, start_direction, default=LFOActionStartDirection.UP, options={"header":"Start Direction", "enum_options": [e.value for e in LFOActionStartDirection]})
        self.params["waveform"] = ActionParam("waveform", LFOActionWaveform, waveform, default=LFOActionWaveform.SINE, options={"header":"Waveform", "enum_options": [e.value for e in LFOActionWaveform]})
        self.params["lfo_rate"] = ActionParam("lfo_rate", float, lfo_rate, default=1.0, options={"min_value":0.1, "max_value":20.0, "step":0.1, "header":"LFO Rate (Hz)"})
        self.params["cc_rate"] = ActionParam("cc_rate", int, cc_rate, default=100, options={"min_value":10, "max_value":1000, "step":10, "header":"CC Rate (ms)"})

    def execute(self, **kwargs):

        action_type: LFOActionType = self.params["action_type"].value
        slot: int = self.params["slot"].value
        cc: int = self.params["cc"].value
        min_value: int = self.params["min_value"].value
        max_value: int = self.params["max_value"].value
        start_value: int = self.params["start_value"].value
        stop_value: int = self.params["stop_value"].value
        start_direction: LFOActionStartDirection = self.params["start_direction"].value
        waveform: LFOActionWaveform = self.params["waveform"].value
        lfo_rate: float = self.params["lfo_rate"].value
        cc_rate: int = self.params["cc_rate"].value

        # MIDIAction parameters
        output: MidiOutputType = self.params["output"].value
        port_name: str = self.params["port_name"].value
        channel: int = self.params["channel"].value

        if action_type == LFOActionType.START:
            # Stop any existing LFO in this slot first
            if slot in LFOAction._lfo_generators and LFOAction._lfo_generators[slot].is_alive():
                LFOAction._lfo_generators[slot].stop()
                LFOAction._lfo_generators[slot].join() # Wait for thread to finish
                del LFOAction._lfo_generators[slot]

            logging.info(f"Starting LFO in slot {slot} (CC: {cc}, Rate: {lfo_rate}Hz, Waveform: {waveform.value})")
            generator = LFOGenerator(
                context=self.context,
                slot=slot,
                cc=cc,
                min_value=min_value,
                max_value=max_value,
                start_value=start_value,
                start_direction=start_direction,
                waveform=waveform,
                lfo_rate=lfo_rate,
                cc_rate=cc_rate,
                output=output,
                port_name=port_name,
                channel=channel
            )
            LFOAction._lfo_generators[slot] = generator
            generator.start()
        elif action_type == LFOActionType.STOP:
            if slot in LFOAction._lfo_generators:
                logging.info(f"Stopping LFO in slot {slot}")
                LFOAction._lfo_generators[slot].stop()
                LFOAction._lfo_generators[slot].join() # TODO: Should I wait for thread to finish?
                
                # Send the stop value
                self.context.send_cc(output, port_name, channel, cc, stop_value)
                del LFOAction._lfo_generators[slot]
            else:
                logging.warning(f"No active LFO found in slot {slot} to stop.")
                # Even if no LFO is running, send the stop value as a failsafe
                self.context.send_cc(output, port_name, channel, cc, stop_value)
