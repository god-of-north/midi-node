#TODO
- MIDI input [forwarding (fanout, direct, route channels)]
- MIDI input [mute, filter]
- MIDI input [external button (press, release)]
- MIDI input [map to action]
- Delayed action
- Tremolo/Slicer action
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
pip3 install RPLCD smbus2 gpiozero gpiod rpi-lgpio pyserial mido adafruit-circuitpython-ads1x15 python-rtmidi


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



# --------- SERVICE -----------

sudo systemctl daemon-reload
sudo systemctl enable midi-node.service
sudo systemctl start midi-node.service

sudo systemctl daemon-reload
sudo systemctl restart midi-node.service

systemctl status midi-node.service


# ----------- MIDI TRS (Type A) -------------
Tip - Data (Sink, MIDI Pin 5)
Ring - VCC (Source, MIDI Pin 4)
Sleeve - GND (Shield, MIDI Pin 2)

