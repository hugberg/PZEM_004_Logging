#!/usr/bin/python

# This code is mostly based on code from Adafruit
# Google Spreadsheet DHT Sensor Data-logging Example
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# AND
# Code belonging to Massi posted on rasberry pi forum
#https://www.raspberrypi.org/forums/viewtopic.php?p=838694#p838103

# Depends on the 'gspread' and 'oauth2client' package being installed.  If you
# have pip installed execute:
#   sudo pip install gspread oauth2client

# Also it's _very important_ on the Raspberry Pi to install the python-openssl
# package because the version of Python is a bit old and can fail with Google's
# new OAuth2 based authentication.  Run the following command to install the
# the package:
#   sudo apt-get update
#   sudo apt-get install python-openssl

# I found these dependensies missing from new rasberry pi
# sudo apt-get update
# sudo apt-get install python-pip
# sudo pip install gspread oauth2client
# sudo apt-get install python-openssl
# sudo pip install pyasn1
# sudo pip install pyasn1-modules

import json
import sys
import time
import datetime
import serial
import struct

##import Adafruit_DHT
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class BTPOWER:

	setAddrBytes 		=	[0xB4,0xC0,0xA8,0x01,0x01,0x00,0x1E]
	readVoltageBytes 	= 	[0xB0,0xC0,0xA8,0x01,0x01,0x00,0x1A]
	readCurrentBytes 	= 	[0XB1,0xC0,0xA8,0x01,0x01,0x00,0x1B]
	readPowerBytes 		= 	[0XB2,0xC0,0xA8,0x01,0x01,0x00,0x1C]
	readRegPowerBytes 	= 	[0XB3,0xC0,0xA8,0x01,0x01,0x00,0x1D]

	def __init__(self, com="/dev/ttyUSB0", timeout=10.0):
		self.ser = serial.Serial(
			port=com,
			baudrate=9600,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout = timeout
		)
		if self.ser.isOpen():
			self.ser.close()
		self.ser.open()

	def checkChecksum(self, _tuple):
		_list = list(_tuple)
		_checksum = _list[-1]
		_list.pop()
		_sum = sum(_list)
		if _checksum == _sum%256:
			return True
		else:
			raise Exception("Wrong checksum")
			
	def isReady(self):
		self.ser.write(serial.to_bytes(self.setAddrBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				return True
		else:
			raise serial.SerialTimeoutException("Timeout setting address")

	def readVoltage(self):
		self.ser.write(serial.to_bytes(self.readVoltageBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				tension = unpacked[2]+unpacked[3]/10.0
				return tension
		else:
			raise serial.SerialTimeoutException("Timeout reading tension")

	def readCurrent(self):
		self.ser.write(serial.to_bytes(self.readCurrentBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				current = unpacked[2]+unpacked[3]/100.0
				return current
		else:
			raise serial.SerialTimeoutException("Timeout reading current")

	def readPower(self):
		self.ser.write(serial.to_bytes(self.readPowerBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				power = unpacked[1]*256+unpacked[2]
				return power
		else:
			raise serial.SerialTimeoutException("Timeout reading power")

	def readRegPower(self):
		self.ser.write(serial.to_bytes(self.readRegPowerBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				regPower = unpacked[1]*256*256+unpacked[2]*256+unpacked[3]
				return regPower
		else:
			raise serial.SerialTimeoutException("Timeout reading registered power")

	def readAll(self):
		if(self.isReady()):
			return(self.readVoltage(),self.readCurrent(),self.readPower(),self.readRegPower())

	def close(self):
		self.ser.close()

# More information can be found in google_spreadsheet.py
GDOCS_OAUTH_JSON       = 'client_secret.json'

# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 'EnergyMonitoring'

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 300


def login_open_sheet(oauth_key_file, spreadsheet):
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
##        scope =  ['https://spreadsheets.google.com/feeds']
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print('Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)


print('Logging sensor measurements to {0} every {1} seconds.'.format(GDOCS_SPREADSHEET_NAME, FREQUENCY_SECONDS))
print('Press Ctrl-C to quit.')
worksheet = None
sensor = BTPOWER()

while True:
    # Login if necessary.
    if worksheet is None:
        worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

    # Attempt to get sensor reading.
##    humidity, temp = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
    voltage = sensor.readVoltage()
    # temp = 23

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    # if humidity is None or temp is None:
        # time.sleep(2)
        # continue

    # print('Temperature: {0:0.1f} C'.format(temp))
    # print('Humidity:    {0:0.1f} %'.format(humidity))
    print('Voltage:    {0:0.1f} V'.format(voltage))
	

    # Append the data in the spreadsheet, including a timestamp
    try:
##        print(worksheet.cell(1, 1))
##        worksheet.update_cell(1, 1, '42')
        date = str(datetime.datetime.now())
        worksheet.append_row([date,voltage])
        
    
        # print(type(date))
        
##        worksheet.append_row([datetime.datetime.now(), temp, humidity])
    except:
        # Error appending data, most likely because credentials are stale.
        # Null out the worksheet so a login is performed at the top of the loop.
        print('Append error, logging in again')
        worksheet = None
        time.sleep(FREQUENCY_SECONDS)
        continue

    # Wait 30 seconds before continuing
    print('Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME))
    # sys.exit(1)
    time.sleep(FREQUENCY_SECONDS)