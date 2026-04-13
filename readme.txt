#TODO
- Delayed action
- Tremolo/Slicer action
- WiFi settings (connect/disconnect)
- Bluetooth MIDI
- Network MIDI
- Receive MIDI and route
- TAP tempo
- sync to external tempo
- Python script action
- Pass context in Action.execute() not in constructor
- Move Base classes/interfaces to Core
- 


# enable I2C in config
sudo raspi-config

# create env
python3 -m venv test-env
source test-env/bin/activate

# install deps
pip3 install RPLCD smbus2 gpiozero gpiod rpi-lgpio pyserial mido adafruit-circuitpython-ads1x15


sudo apt install python3-smbus i2c-tools -y
sudo apt install pigpio python3-pigpio -y
sudo apt install gpiod libgpiod-dev -y
sudo apt install swig -y
sudo apt install liblgpio-dev


# check I2C devices
sudo i2cdetect -y 1


# FTP server run
python -m pyftpdlib -w --user=u --password=p



# setup environmnet variables. Add /etc/profile
export MIDI_NODE_MODE="LIVE"


# --------- MIDI IN/Out module ---------------

A02 - GND
A03 - To MicroController UART_TX (D9 - AltSerial(ArduinoNano)/GPOI14 - RPI Zero 2W)
A04 - To MIDI External Device UART_RX 
A05 - +5V

K03 - GND
K04 - To MIDI External Device UART_RX
K05 - +5V

---------------------

B02 - GND
B04 - To MicroController RX
B05 - +5V

N03 - MIDI IN
N04 - MIDI IN

---------------------

MIDI TRS (Type A)
Tip - Data (Sink, MIDI Pin 5)
Ring - VCC (Source, MIDI Pin 4)
Sleeve - GND (Shield, MIDI Pin 2)

