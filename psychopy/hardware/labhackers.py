#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2019 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides basic LabHackers (www.labhackers.com) device classes.
"""

import serial
import os
import json


def getSerialPorts():
    available = []
    if os.name == 'nt':  # Windows
        for i in range(1, 512):
            try:
                sport = 'COM' + str(i)
                s = serial.Serial(sport, baudrate=128000)
                available.append(sport)
                s.close()
            except (serial.SerialException, ValueError):
                pass
    else:  # Mac / Linux
        from serial.tools import list_ports
        available = [port[0] for port in list_ports.comports()]
    return available

def getDevices():
    devices = []
    available = getSerialPorts()
    for p in available:
        try:
            sport = serial.Serial(p, baudrate=128000, timeout=1.0)
            sport.write(b"GET CONFIG\n")
            rx_data = sport.readline()
            if rx_data:
                rx_data = rx_data[:-1].strip()
                try:
                    lhd_conf = json.loads(rx_data)
                    lhd_conf['port'] = p
                    devices.append(lhd_conf)
                except:
                    raise RuntimeError("ERROR: {}".format(rx_data))
            sport.close()
        except:
            pass
    return devices

def getUSB2TTL8s():
    devices = []
    for lhd_conf in getDevices(): 
        if lhd_conf.get("model_name","") == "USB2TTL8":
            devices.append(lhd_conf)
    return devices

class USB2TTL8:
    _sport = None
    _instance_count = 0
    def __init__(self):
        if self._sport is None:
            configs = getUSB2TTL8s()
            if len(configs) == 0:
                raise RuntimeError("No USB2TTL8 devices detected.")        
            dconf = configs[0]
        
            # Create Serial interface with USB2TTL8
            USB2TTL8._sport = serial.Serial(dconf['port'], baudrate=128000, timeout = 0.1)
        
            # Set device to write mode.
            USB2TTL8._sport.write(b"SET DATA_MODE WRITE\n")
            while USB2TTL8._sport.readline():
                pass
        USB2TTL8._instance_count += 1
    
    @staticmethod
    def setData(val):
        """Write 1 byte of data to the USB2TTL8. 

        parameters:
            - val: the value to write (must be an integer 0:255)
        """
        if USB2TTL8._sport is not None:
            USB2TTL8._sport.write(b"WRITE %d\n"%(val))
        else:
            raise RuntimeWarning("Warning: No USB2TTL8 Serial Port Connection, setData Failed.")

    def __del__(self):
        USB2TTL8._instance_count -= 1
        if USB2TTL8._instance_count <= 0 and USB2TTL8._sport is not None:
            USB2TTL8._sport.close()
            USB2TTL8._sport = None
