#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
# Contributor: maqadri - mqadri@holycross.edu

"""
    Interface to Phidgets for relay control
"""

#Future - add analog input, digital input, digital output (5V) via 8/8/8 Interfacekit

from psychopy import prefs, logging
from psychopy import core

all_phidgets = {}

class phidgetOutputComponent:
    def __init__(self, channelList=None, serialNumber=-1, reversedRelay=False):
        """

        Parameters
        ----------
        channelList : list
            The channels controlled by this component
            
        serialNumber : int
            The serial number for the phidget you want to control

        reversedRelay : bool
            The starting state for the relay - open (0) or closed (1)
        """

        if channelList is None:
            channelList = [0]

        import Phidget22.Devices.DigitalOutput as DigitalOutput
        import Phidget22.PhidgetException

        self.phidget_outputs = []
        if reversedRelay:
            self.default_state = 1
        else:
            self.default_state = 0
        self.status = ''

        for channel in channelList:
            all_phidgets_code = '{:}-{:}'.format(int(serialNumber),channel)
            if all_phidgets_code not in all_phidgets.keys():
                digitalOutput = DigitalOutput.DigitalOutput()
                digitalOutput.setDeviceSerialNumber(int(serialNumber))
                digitalOutput.setChannel(channel)
                digitalOutput.openWaitForAttachment(100)
                all_phidgets[all_phidgets_code] = digitalOutput
            else:
                digitalOutput = all_phidgets[all_phidgets_code]

            self.phidget_outputs.append(digitalOutput)

    def __del__(self):
        self.openRelay()

    def closeRelay(self):
        [ch.setState(1-self.default_state) for ch in self.phidget_outputs]
        # for ch in self.phidget_outputs:
        #     if self.default_state == 1:
        #         ch.setState(0)
        #     else:
        #         ch.setState(1)

    def openRelay(self):
        [ch.setState(self.default_state) for ch in self.phidget_outputs]
        # for ch in self.phidget_outputs:
        #     ch.setState(self.default_state)

    #Currently not being used
    def toggleRelay(self):
        [ch.setState(1-ch.getState()) for ch in self.phidget_outputs]
        # for ch in self.phidget_outputs:
        #     if ch.getState() == 1:
        #         ch.setState(0)
        #     else:
        #         ch.setState(1)
        


