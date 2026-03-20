import logging
from core import MidiNodeDevice


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')
    logging.basicConfig(level=logging.ERROR, format='%(threadName)s: %(message)s')

    device = MidiNodeDevice()
    device.start()