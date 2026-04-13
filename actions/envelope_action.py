import logging
from enum import Enum
from threading import Event, Lock, Thread, Timer
import time
from typing import Dict, Optional

from actions.action import ActionParam
from actions.midi_action import MIDIAction
from midi.midi_output_type import MidiOutputType


class EnvelopeActionType(Enum):
    START = "Start"
    STOP = "Stop"
    ONE_SHOT = "One Shot"


class EnvelopeFilter(Thread):
    """
    Per-slot envelope thread.
    Runs Attack -> Max Hold -> Decay -> Sustain(until stop) -> Release -> Exit.
    """

    def __init__(
        self,
        context: "DeviceContext",
        *,
        slot: int,
        cc: int,
        min_value: int,
        max_value: int,
        sustain_value: int,
        attack_time: int,
        max_time: int,
        decay_time: int,
        release_time: int,
        output: MidiOutputType,
        port_name: str,
        channel: int,
        tick_ms: int = 10,
    ):
        super().__init__()
        self.context = context
        self.slot = slot
        self.cc = int(cc)
        self.min_value = int(min_value)
        self.max_value = int(max_value)
        self.sustain_value = int(sustain_value)
        self.attack_time = int(attack_time)
        self.max_time = int(max_time)
        self.decay_time = int(decay_time)
        self.release_time = int(release_time)
        self.output = output
        self.port_name = port_name
        self.channel = int(channel)
        self.tick_ms = max(1, int(tick_ms))

        self._stop_event = Event()
        self._current_value: float = float(self.min_value)
        self.daemon = True

    def stop(self):
        self._stop_event.set()

    def _send_cc(self, value: float):
        midi_value = max(0, min(127, int(round(value))))
        self.context.send_cc(self.output, self.port_name, self.channel, self.cc, midi_value)

    def _ramp(self, start: float, end: float, duration_ms: int) -> bool:
        """
        Returns True if finished normally, False if interrupted by stop.
        """
        duration_ms = max(0, int(duration_ms))
        if duration_ms == 0:
            self._current_value = float(end)
            self._send_cc(self._current_value)
            return not self._stop_event.is_set()

        start_time = time.time()
        duration_s = duration_ms / 1000.0
        while True:
            if self._stop_event.is_set():
                return False

            elapsed = time.time() - start_time
            t = min(1.0, elapsed / duration_s) if duration_s > 0 else 1.0
            self._current_value = start + (end - start) * t
            self._send_cc(self._current_value)

            if t >= 1.0:
                return True

            self._stop_event.wait(self.tick_ms / 1000.0)

    def _hold(self, duration_ms: int) -> bool:
        duration_ms = max(0, int(duration_ms))
        if duration_ms == 0:
            return not self._stop_event.is_set()
        return not self._stop_event.wait(duration_ms / 1000.0)

    def run(self):
        try:
            # Always begin at min
            self._current_value = float(self.min_value)
            self._send_cc(self._current_value)

            # Attack: min -> max
            if not self._ramp(float(self.min_value), float(self.max_value), self.attack_time):
                self._release()
                return

            # Hold max
            self._current_value = float(self.max_value)
            self._send_cc(self._current_value)
            if not self._hold(self.max_time):
                self._release()
                return

            # Decay: max -> sustain
            if not self._ramp(float(self.max_value), float(self.sustain_value), self.decay_time):
                self._release()
                return

            # Sustain: hold at sustain until stop
            self._current_value = float(self.sustain_value)
            self._send_cc(self._current_value)
            self._stop_event.wait()

            self._release()
        except Exception:
            logging.exception("EnvelopeFilter slot %s crashed", self.slot)

    def _release(self):
        # Release: current -> min (even if we were stopped mid-attack/decay)
        current = float(self._current_value)
        self._ramp(current, float(self.min_value), self.release_time)
        self._current_value = float(self.min_value)
        self._send_cc(self._current_value)


class EnvelopeAction(MIDIAction):
    TYPE = "envelope"
    TITLE = "Envelope Action"

    _filters: Dict[int, EnvelopeFilter] = {}
    _timers: Dict[int, Timer] = {}
    _lock: Lock = Lock()

    def __init__(
        self,
        context: "DeviceContext",
        action_type: EnvelopeActionType = EnvelopeActionType.START,
        slot: int = 0,
        cc: int = 0,
        min_value: int = 0,
        max_value: int = 127,
        sustain_value: int = 64,
        attack_time: int = 200,
        max_time: int = 0,
        decay_time: int = 500,
        release_time: int = 200,
        output: MidiOutputType = MidiOutputType.UART,
        port_name: str = "/dev/serial0",
        channel: int = 1,
        **kwargs,
    ):
        super().__init__(context=context, output=output, port_name=port_name, channel=channel, **kwargs)

        if isinstance(action_type, str):
            action_type = EnvelopeActionType[action_type]
        if isinstance(output, str):
            output = MidiOutputType[output]

        self.params["action_type"] = ActionParam(
            "action_type",
            EnvelopeActionType,
            action_type,
            default=EnvelopeActionType.START,
            options={"header": "Envelope Action", "enum_options": [e.value for e in EnvelopeActionType]},
        )
        self.params["slot"] = ActionParam("slot", int, slot, default=0, options={"min_value": 0, "max_value": 99, "header": "Envelope Slot"})
        self.params["cc"] = ActionParam("cc", int, cc, default=0, options={"min_value": 0, "max_value": 127, "header": "MIDI CC"})

        self.params["min_value"] = ActionParam("min_value", int, min_value, default=0, options={"min_value": 0, "max_value": 127, "header": "Min Value"})
        self.params["max_value"] = ActionParam("max_value", int, max_value, default=127, options={"min_value": 0, "max_value": 127, "header": "Max Value"})
        self.params["sustain_value"] = ActionParam("sustain_value", int, sustain_value, default=64, options={"min_value": 0, "max_value": 127, "header": "Sustain Value"})

        self.params["attack_time"] = ActionParam("attack_time", int, attack_time, default=200, options={"min_value": 0, "max_value": 60000, "step": 10, "header": "Attack (ms)"})
        self.params["max_time"] = ActionParam("max_time", int, max_time, default=0, options={"min_value": 0, "max_value": 60000, "step": 10, "header": "Max Hold (ms)"})
        self.params["decay_time"] = ActionParam("decay_time", int, decay_time, default=500, options={"min_value": 0, "max_value": 60000, "step": 10, "header": "Decay (ms)"})
        self.params["release_time"] = ActionParam("release_time", int, release_time, default=200, options={"min_value": 0, "max_value": 60000, "step": 10, "header": "Release (ms)"})

    @classmethod
    def _stop_slot_locked(cls, slot: int):
        timer = cls._timers.pop(slot, None)
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass

        filt = cls._filters.get(slot)
        if filt and filt.is_alive():
            filt.stop()

    @classmethod
    def _join_and_cleanup_locked(cls, slot: int):
        filt = cls._filters.get(slot)
        if filt and filt.is_alive():
            filt.join()
        cls._filters.pop(slot, None)

    def _start_filter(self) -> EnvelopeFilter:
        slot: int = self.params["slot"].value
        cc: int = self.params["cc"].value
        min_value: int = self.params["min_value"].value
        max_value: int = self.params["max_value"].value
        sustain_value: int = self.params["sustain_value"].value
        attack_time: int = self.params["attack_time"].value
        max_time: int = self.params["max_time"].value
        decay_time: int = self.params["decay_time"].value
        release_time: int = self.params["release_time"].value

        output: MidiOutputType = self.params["output"].value
        port_name: str = self.params["port_name"].value
        channel: int = self.params["channel"].value

        with EnvelopeAction._lock:
            # Stop any existing filter in this slot first
            EnvelopeAction._stop_slot_locked(slot)
            EnvelopeAction._join_and_cleanup_locked(slot)

            logging.info("Starting EnvelopeFilter slot %s (CC %s)", slot, cc)
            filt = EnvelopeFilter(
                context=self.context,
                slot=slot,
                cc=cc,
                min_value=min_value,
                max_value=max_value,
                sustain_value=sustain_value,
                attack_time=attack_time,
                max_time=max_time,
                decay_time=decay_time,
                release_time=release_time,
                output=output,
                port_name=port_name,
                channel=channel,
            )
            EnvelopeAction._filters[slot] = filt
            filt.start()
            return filt

    def _stop_filter(self):
        slot: int = self.params["slot"].value
        with EnvelopeAction._lock:
            if slot not in EnvelopeAction._filters:
                logging.warning("No active EnvelopeFilter found in slot %s to stop.", slot)
                return
            logging.info("Stopping EnvelopeFilter slot %s", slot)
            EnvelopeAction._stop_slot_locked(slot)
            EnvelopeAction._join_and_cleanup_locked(slot)

    def execute(self, **kwargs):
        action_type: EnvelopeActionType = self.params["action_type"].value

        if action_type == EnvelopeActionType.START:
            self._start_filter()
        elif action_type == EnvelopeActionType.STOP:
            self._stop_filter()
        elif action_type == EnvelopeActionType.ONE_SHOT:
            # Start now; schedule STOP right after decay stage completes (attack + max_hold + decay)
            slot: int = self.params["slot"].value
            attack_time: int = max(0, int(self.params["attack_time"].value))
            max_time: int = max(0, int(self.params["max_time"].value))
            decay_time: int = max(0, int(self.params["decay_time"].value))
            stop_after_ms = attack_time + max_time + decay_time

            self._start_filter()

            def _delayed_stop():
                # Build a minimal stop action using current instance state
                try:
                    self._stop_filter()
                except Exception:
                    logging.exception("Delayed stop failed for EnvelopeFilter slot %s", slot)

            with EnvelopeAction._lock:
                existing = EnvelopeAction._timers.get(slot)
                if existing:
                    try:
                        existing.cancel()
                    except Exception:
                        pass
                t = Timer(stop_after_ms / 1000.0, _delayed_stop)
                t.daemon = True
                EnvelopeAction._timers[slot] = t
                t.start()
        else:
            raise ValueError(f"Unknown EnvelopeActionType: {action_type}")

