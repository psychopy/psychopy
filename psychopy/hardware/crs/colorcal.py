#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    This code was mostly written by Jon Peirce.
#    CRS Ltd provided support as needed.

# Acknowledgements
#    This code was written by Jon Peirce

from __future__ import absolute_import, division, print_function

from builtins import bytes
from builtins import range
from builtins import object
import sys
try:
    import serial
except Exception:
    serial = False
import numpy

__docformat__ = "restructuredtext en"

# try to use psychopy logging but revert to system logging
try:
    from psychopy import logging  # from 1.73 onwards
except ImportError:
    import logging  # use the standard python logging
eol = "\n\r"  # unusual for a serial port?!


class ColorCAL(object):
    """A class to handle the CRS Ltd ColorCAL device
    """

    # PsychoPy uses these two variables for matching classes to photometers
    longName = "CRS ColorCAL"
    driverFor = ["colorcal"]

    def __init__(self, port=None, maxAttempts=2):
        """Open serial port connection with Colorcal II device

        :Usage:

            cc = ColorCAL(port, maxAttempts)

       If no port is provided then the following defaults will be tried:
           - /dev/cu.usbmodem0001 (OSX)
           - /dev/ttyACM0
           - COM3 (windows)

        """
        super(ColorCAL, self).__init__()

        if not serial:
            raise ImportError('The module serial is needed to connect to '
                              'photometers. On most systems this can be '
                              'installed with\n\t easy_install pyserial')

        # try to deduce port
        if port is None:
            if sys.platform == 'darwin':
                port = '/dev/cu.usbmodem0001'
            elif sys.platform.startswith('linux'):
                port = '/dev/ttyACM0'
            elif sys.platform.startswith('win'):
                port = 3
        if type(port) in (int, float):
            # add one so that port 1=COM1
            self.portNumber = port
            self.portString = 'COM%i' % self.portNumber
        else:
            self.portString = port
            self.portNumber = None

        self.isOpen = 0
        self.lastLum = None
        self.lastCmd = ''
        self.type = 'ColorCAL'
        self.com = False
        self.OK = True  # until we fail
        self.maxAttempts = maxAttempts
        self._zeroCalibrated = False

        # try to open the port
        try:
            self.com = serial.Serial(self.portString)
        except Exception:
            msg = ("Couldn't connect to port %s. Is it being used by "
                   "another program?")
            self._error(msg % self.portString)

        # setup the params for serial port
        if self.OK:
            self.com.close()  # not sure why this helps but on win32 it does!!
            try:
                self.com.setBaudrate(115200)  # actually, any baudrate is fine?
            except:
                self.com.baudrate = 115200  # setBaudrate() remov pyserial v3.0
            try:
                if not self.com.isOpen():
                    self.com.open()
            except Exception:
                msg = "Opened serial port %s, but couldn't connect to ColorCAL"
                self._error(msg % self.portString)
            else:
                self.isOpen = 1

        # check that we can communicate with it
        self.ok, self.serialNum, self.firm, self.firmBuild = self.getInfo()
        self.calibMatrix = self.getCalibMatrix()

    def sendMessage(self, message, timeout=0.1):
        """Send a command to the photometer and wait an alloted
        timeout for a response.
        """
        # flush the read buffer first
        # read as many chars as are in the buffer
        prevOut = self.com.read(self.com.inWaiting())
        if len(prevOut) and prevOut not in ('>' + eol, eol):
            # do not use log messages here
            print('Resp found to prev cmd (%s):%s' % (self.lastCmd, prevOut))
        self.lastCmd = message

        if message[-2:] not in ('\n', '\n\r'):
            message += "\n".encode('ascii')  # append a newline if necess
        # send the message
        self.com.write(message)
        self.com.flush()
        # get reply (within timeout limit)
        self.com.timeout = timeout
        logging.debug('Sent command:%s' % (message[:-1]))  # send complete msg

        # get output lines using self.readline, not self.com.readline
        # colorcal signals the end of a message by giving a command prompt
        lines = []
        thisLine = ''
        nEmpty = 0
        while (thisLine != '>'.encode('ascii')) and (nEmpty <= self.maxAttempts):
            # self.com.readline can't handle custom eol
            thisLine = self.readline(eol=eol)
            if thisLine in (eol.encode('ascii'), '>'.encode('ascii'), ''.encode('ascii')):  # lines we don't care about
                nEmpty += 1
                continue
            else:
                # line without any eol chars
                lines.append(thisLine.rstrip(eol.encode('ascii')))
                nEmpty = 0


        # got all lines and reached '>'
        if len(lines) == 1:
            return lines[0]  # return the string
        else:
            return lines  # a list of lines

    def measure(self):
        """Conduct a measurement and return the X,Y,Z values

        Usage::

            ok, X, Y, Z = colorCal.measure()

        Where:
            ok is True/False
            X, Y, Z are the CIE coordinates (Y is luminance in cd/m**2)

        Following a call to measure, the values ColorCAL.lastLum will also be
        populated with, for compatibility with other devices used by PsychoPy
        (notably the PR650/PR655)

        """
        # use a long timeout for measurement:
        val = self.sendMessage(b'MES', timeout=5)
        valstrip = val.strip(b'\n\r>')
        vals = valstrip.split(b',')
        ok = (vals[0] == 'OK00')
        # transform raw x,y,z by calibration matrix
        xyzRaw = numpy.array([vals[1].strip(), vals[2].strip(), vals[3].strip()], dtype=float)
        X, Y, Z = numpy.dot(self.calibMatrix, xyzRaw)
        self.ok, self.lastLum = ok, Y
        return ok, X, Y, Z

    def getLum(self):
        """Conducts a measurement and returns the measured luminance

        .. note::
            The luminance is always also stored as .lastLum
        """
        self.measure()
        return self.lastLum

    def getInfo(self):
        """Queries the device for information

        usage::
            (ok, serialNumber,
                firmwareVersion, firmwareBuild) = colorCal.getInfo()

        `ok` will be True/False
        Other values will be a string or None.

        """
        val = self.sendMessage(b'IDR')
        valstrip = val.strip(b'\n\r>')
        val = valstrip.split(b',')
        ok = (val[0] == b'OK00')
        if ok:
            firmware = val[2]
            serialNum = val[4]
            firmBuild = val[-1]
        else:
            firmware = 0
            serialNum = 0
            firmBuild = 0
        return ok, serialNum, firmware, firmBuild

    def getNeedsCalibrateZero(self):
        """Check whether the device needs a dark calibration

        In initial versions of CRS ColorCAL mkII the device stored
        its zero calibration in volatile memory and needed to be
        calibrated in darkness each time you connected it to the USB

        This function will check whether your device requires that (based
        on firmware build number and whether you've already done it
        since python connected to the device).

        :returns: True or False
        """

        if self.firmBuild < b'877' and not self._zeroCalibrated:
            return True
        else:
            return False

    def calibrateZero(self):
        """Perform a calibration to zero light.

        For early versions of the ColorCAL this had to be called after
        connecting to the device. For later versions the dark calibration
        was performed at the factory and stored in non-volatile memory.

        You can check if you need to run a calibration with::

            ColorCAL.getNeedsCalibrateZero()
        """
        val = self.sendMessage(b"UZC", timeout=1.0)
        if val == b'OK00':
            pass
        elif val == b'ER11':
            logging.error(
                "Could not calibrate ColorCAL2. Is it properly covered?")
            return False
        else:  # unlikely
            logging.warning(
                "Received surprising result from ColorCAL2: %s" % val)
            return False
        # then take a measurement to see if we are close to zero lum (ie is it
        # covered?)
        self.ok, x, y, z = self.measure()
        if y > 3:
            logging.error('There seems to be some light getting to the '
                          'detector. It should be well-covered for zero '
                          'calibration')
            return False
        self._zeroCalibrated = True
        self.calibMatrix = self.getCalibMatrix()
        return True

    def getCalibMatrix(self):
        """Get the calibration matrix from the device, needed for transforming
        measurements into real-world values.

        This is normally retrieved during __init__ and stored as
        `ColorCal.calibMatrix` so most users don't need to call this function.
        """
        matrix = numpy.zeros((3, 3), dtype=float)
        # alternatively use 'r99' which gets all rows at once, but then more
        # parsing?
        for rowN in range(3):
            rowName = 'r0%i' % (rowN + 1)
            val = self.sendMessage(rowName.encode('ascii'), timeout=1.0)
            valstrip = val.strip(b'\n\r>')
            vals = valstrip.split(b',')  # convert to list of values
            if vals[0] == b'OK00' and len(vals) > 1:
                # convert to numpy array
                rawVals = numpy.array(vals[1:], dtype=int)
                floats = _minolta2float(rawVals)
                matrix[rowN, :] = floats
            else:
                msg = 'ColorCAL got this from command %s: %s'
                print(msg % (rowName, repr(val)))
        return matrix

    def _error(self, msg):
        self.OK = False
        logging.error(msg)

    def readline(self, size=None, eol='\n\r'):
        """This should be used in place of the standard serial.Serial.readline()
        because that doesn't allow us to set the eol character
        """
        # The code here is adapted from
        #    pyserial 2.5: serialutil.FileLike.readline
        # which is released under the python license.
        # Copyright (C) 2001-2010 Chris Liechti
        leneol = len(eol)
        line = bytearray()
        while True:
            # NB timeout is applied here, so to each char read
            c = self.com.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
                if size is not None and len(line) >= size:
                    break
            else:
                break
        return bytes(line)


def _minolta2float(inVal):
    """Takes a number, or numeric array (any shape) and returns the appropriate
    float.

    minolta stores;
        +ve values as val * 10000
        -ve values as -val * 10000 + 50000

    >>> _minolta2Float(50347)  # NB returns a single float
    -0.034700000000000002
    >>> _minolta2Float(10630)
    1.0630999999999999
    >>> _minolta2Float([10635, 50631])  # NB returns a numpy array
    array([ 1.0635, -0.0631])

    """
    # convert  to array if needed
    arr = numpy.asarray(inVal)
    # handle single vals
    if arr.shape == ():
        if inVal < 50000:
            return inVal/10000.0
        else:
            return (-inVal + 50000.0)/10000.0
    # handle arrays
    negs = (arr > 50000)  # find negative values
    out = arr/10000.0  # these are the positive values
    out[negs] = (-arr[negs] + 50000.0)/10000.0
    return out
