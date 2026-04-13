from enum import Enum


class MidiMessageType(Enum):
    NOTE_ON = 'note_on'
    NOTE_OFF = 'note_off'
    CONTROL_CHANGE = 'control_change'
    PROGRAM_CHANGE = 'program_change'
    