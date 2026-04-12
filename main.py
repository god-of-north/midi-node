import logging
from core import MidiNodeDevice
from storage.app_config import AppMode
from config import APP_MODE


if __name__ == "__main__":
    if APP_MODE == AppMode.SIMULATION:
        logging.basicConfig(level=logging.ERROR, format='%(threadName)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')

    device = MidiNodeDevice()
    device.start()