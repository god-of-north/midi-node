import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


# Create the I2C bus interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADS object with the default I2C address (0x48)
ads = ADS.ADS1115(i2c, address=0x48)

# Configure the gain (PGA). A gain of 1 allows readings from 0V to 4.096V.
# See the datasheet for other gain options to measure different voltage ranges.
# ads.gain = 1  # This is the default setting
ads.gain = 1

# Define the analog input channel (single-ended mode).
# Connect your analog signal to the AIN0 pin (P0).
chan = AnalogIn(ads, 0)

# Continuously print the values
print("{:>5}\t{:>5}".format('Raw Value', 'Voltage'))
while True:
    print("{:>5}\t{:>5.3f} V".format(chan.value, chan.voltage))
    time.sleep(1)
