#!/usr/bin/python
# -*- coding: utf-8 -*-

# thermo-fht6020.py

# Simple sniffer script which prints on the screen the serial messages exchanged between a Thermo
# Fisher Scientific FHT 6020 controller and a PC.

# Python modules required: pyserial.
# Tested with Python 2.7.12 and pyserial 3.4.

# Necessary modules

import serial
import sys

# Serial interface, configured as described in the FHT 6020 manual

interface = serial.Serial(port = "/dev/ttyUSB0",
                          baudrate = 19200,
                          bytesize = serial.SEVENBITS,
                          parity = serial.PARITY_EVEN,
                          stopbits = serial.STOPBITS_TWO)

# Loop

while (True):
    new_character = interface.read(1)
    if (new_character == "\x07"):
        sys.stdout.write("<BEL>")
    elif (new_character == "\x03"):
        sys.stdout.write("<ETX>\n")
    elif (new_character == "\x15"):
        sys.stdout.write("<NAK>\n")
    elif (new_character == "\x06"):
        sys.stdout.write("<ACK>\n")
    else:
        sys.stdout.write(new_character)
