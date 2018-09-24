#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""PhotoResearch spectrophotometers
See http://www.photoresearch.com/

--------
"""
from __future__ import absolute_import, print_function

from builtins import str
from builtins import range
from builtins import object
from psychopy import logging
import struct
import sys
import time
import numpy

try:
    import serial
except ImportError:
    serial = False


class PR650(object):
    """An interface to the PR650 via the serial port.

    (Added in version 1.63.02)

    example usage::

        from psychopy.hardware.pr import PR650
        myPR650 = PR650(port)
        myPR650.getLum()  # make a measurement
        nm, power = myPR650.getLastSpectrum()  # get a power spectrum for the
                    last measurement

    NB :func:`psychopy.hardware.findPhotometer()` will locate and return
    any supported device for you so you can also do::

        from psychopy import hardware
        phot = hardware.findPhotometer()
        print(phot.getLum())

    :troubleshooting:

        Various messages are printed to the log regarding the function of
        this device, but to see them you need to set the printing of the
        log to the correct level::

            from psychopy import logging
            logging.console.setLevel(logging.ERROR)  # error messages only
            logging.console.setLevel(logging.INFO)  # will give more info
            logging.console.setLevel(logging.DEBUG)  # log all communications

        If you're using a keyspan adapter (at least on macOS) be aware that
        it needs a driver installed. Otherwise no ports will be found.

        Also note that the attempt to connect to the PR650 must occur within
        the first few seconds after turning it on.
    """
    longName = "PR650"
    driverFor = ["pr650"]

    def __init__(self, port, verbose=None):
        super(PR650, self).__init__()
        if type(port) in (int, float):
            # add one so that port 1=COM1
            self.portNumber = port
            self.portString = 'COM%i' % self.portNumber
        else:
            self.portString = port
            self.portNumber = None
        self.isOpen = 0
        self.lastQual = 0
        self.type = 'PR650'
        self.com = False
        self.OK = True  # until we fail

        self.codes = {'OK': '000\r\n',  # this is returned after measure
                      '18': 'Light Low',  # returned at beginning of data
                      '10': 'Light Low',
                      '00': 'OK'}

        # try to open the port
        _linux = sys.platform.startswith('linux')
        if sys.platform in ('darwin', 'win32') or _linux:
            try:
                self.com = serial.Serial(self.portString)
            except Exception:
                msg = ("Couldn't connect to port %s. Is it being used by"
                       " another program?")
                self._error(msg % self.portString)
        else:
            msg = "I don't know how to handle serial ports on %s"
            self._error(msg % sys.platform)
        # setup the params for PR650 comms
        if self.OK:
            self.com.baudrate = 9600
            self.com.parity = 'N'  # none
            self.com.stopbits = 1
            try:
                # Pyserial >=2.6 throws an exception when trying to open a
                # serial port that is already open. Catching that exception
                # is not an option here because PySerial only defines a
                # single exception type (SerialException)
                if not self.com.isOpen():
                    self.com.open()
            except Exception:
                msg = "Opened serial port %s, but couldn't connect to PR650"
                self._error(msg % self.portString)
            else:
                self.isOpen = 1
        if self.OK:
            logging.info("Successfully opened %s" % self.portString)
            time.sleep(0.1)  # wait while establish connection
            # turn on the backlight as feedback
            reply = self.sendMessage(b'b1\n')
            if reply != self.codes['OK']:
                self._error("PR650 isn't communicating")

        if self.OK:
            # set command to make sure using right units etc...
            reply = self.sendMessage(b's01,,,,,,01,1')

    def _error(self, msg):
        self.OK = False
        logging.error(msg)

    def sendMessage(self, message, timeout=0.5, DEBUG=False):
        """Send a command to the photometer and wait an allotted
        timeout for a response (Timeout should be long for low
        light measurements)
        """
        if message[-1] != '\n':
            message += '\n'  # append a newline if necess

        # flush the read buffer first
        # read as many chars as are in the buffer
        self.com.read(self.com.inWaiting())

        # send the message
        self.com.write(message)
        self.com.flush()
        # time.sleep(0.1)  # PR650 gets upset if hurried!

        # get feedback (within timeout limit)
        self.com.timeout = timeout
        logging.debug(message)  # send complete message
        if message in ('d5', 'd5\n'):
            # we need a spectrum which will have multiple lines
            return self.com.readlines()
        else:
            return self.com.readline()

    def measure(self, timeOut=30.0):
        """Make a measurement with the device. For a PR650 the device is
        instructed to make a measurement and then subsequent commands are
        issued to retrieve info about that measurement.
        """
        t1 = time.clock()
        reply = self.sendMessage(b'm0\n', timeOut)  # measure and hold data
        # using the hold data method the PR650 we can get interogate it
        # several times for a single measurement

        if reply == self.codes['OK']:
            raw = self.sendMessage(b'd2')
            xyz = raw.split(',')  # parse into words
            self.lastQual = str(xyz[0])
            if self.codes[self.lastQual] == 'OK':
                self.lastLum = float(xyz[3])
            else:
                self.lastLum = 0.0
        else:
            logging.warning("Didn't collect any data (extend timeout?)")

    def getLum(self):
        """Makes a measurement and returns the luminance value
        """
        self.measure()
        return self.getLastLum()

    def getSpectrum(self, parse=True):
        """Makes a measurement and returns the current power spectrum

        If ``parse=True`` (default):
            The format is a num array with 100 rows [nm, power]

        If ``parse=False`` (default):
            The output will be the raw string from the PR650 and should then
            be passed to ``.parseSpectrumOutput()``. It's slightly more
            efficient to parse R,G,B strings at once than each individually.
        """
        self.measure()
        return self.getLastSpectrum(parse=parse)

    def getLastLum(self):
        """This retrieves the luminance (in cd/m**2) from the last call to
        ``.measure()``
        """
        return self.lastLum

    def getLastSpectrum(self, parse=True):
        """This retrieves the spectrum from the last call to ``.measure()``

        If ``parse=True`` (default):
        The format is a num array with 100 rows [nm, power]

        otherwise:
        The output will be the raw string from the PR650 and should then
        be passed to ``.parseSpectrumOutput()``. It's more efficient to
        parse R,G,B strings at once than each individually.
        """
        raw = self.sendMessage(b'd5')  # returns a list where each list
        if parse:
            # skip the first 2 entries (info)
            return self.parseSpectrumOutput(raw[2:])
        else:
            return raw

    def parseSpectrumOutput(self, rawStr):
        """Parses the strings from the PR650 as received after sending
        the command 'd5'.
        The input argument "rawStr" can be the output from a single
        phosphor spectrum measurement or a list of 3 such measurements
        [rawR, rawG, rawB].
        """

        if len(rawStr) == 3:
            RGB = True
            rawR = rawStr[0][2:]
            rawG = rawStr[1][2:]
            rawB = rawStr[2][2:]
            nPoints = len(rawR)
        else:
            RGB = False
            nPoints = len(rawStr)
            raw = rawStr[2:]

        nm = []
        if RGB:
            power = [[], [], []]
            for n in range(nPoints):
                # each entry in list is a string like this:
                thisNm, thisR = rawR[n].split(',')
                thisR = thisR.replace('\r\n', '')
                thisNm, thisG = rawG[n].split(',')
                thisG = thisG.replace('\r\n', '')
                thisNm, thisB = rawB[n].split(',')
                thisB = thisB.replace('\r\n', '')
                exec('nm.append(%s)' % thisNm)
                exec('power[0].append(%s)' % thisR)
                exec('power[1].append(%s)' % thisG)
                exec('power[2].append(%s)' % thisB)
        else:
            power = []
            for n, point in enumerate(rawStr):
                # each entry in list is a string like this:
                thisNm, thisPower = point.split(',')
                nm.append(thisNm)
                power.append(thisPower.replace('\r\n', ''))
            if progDlg:
                progDlg.Update(n)
        return numpy.asarray(nm), numpy.asarray(power)


class PR655(PR650):
    """An interface to the PR655/PR670 via the serial port.

    example usage::

        from psychopy.hardware.pr import PR655
        myPR655 = PR655(port)
        myPR655.getLum()  # make a measurement
        nm, power = myPR655.getLastSpectrum()  # get a power spectrum for the
                    last measurement

    NB :func:`psychopy.hardware.findPhotometer()` will locate and return
    any supported device for you so you can also do::

        from psychopy import hardware
        phot = hardware.findPhotometer()
        print(phot.getLum())

    :troubleshooting:

        If the device isn't responding try turning it off and turning it
        on again, and/or disconnecting/reconnecting the USB cable. It may
        be that the port has become controlled by some other program.

    """
    longName = "PR655/PR670"
    driverFor = ["pr655", "pr670"]

    def __init__(self, port):
        self.type = None  # get this from the device later
        self.com = False
        self.OK = True  # until we fail
        if type(port) in (int, float):
            # add one so that port 1=COM1
            self.portNumber = port
            self.portString = 'COM%i' % self.portNumber
        else:
            self.portString = port
            self.portNumber = None

        self.codes = {'OK': '000\r\n',  # this is returned after measure
                      '18': 'Light Low',  # returned at beginning of data
                      '10': 'Light Low',
                      '00': 'OK'}

        # try to open the port
        try:
            self.com = serial.Serial(self.portString)
        except Exception:
            msg = ("Couldn't connect to port %s. Is it being used by "
                   "another program?")
            self._error(msg % self.portString)
        # setup the params for PR650 comms
        if self.OK:
            self.com.baudrate = 9600
            self.com.parity = 'N'  # none
            self.com.stopbits = 1
            try:
                self.com.close()  # attempt to close if it's currently open
                self.com.open()
                self.isOpen = 1
            except Exception:
                msg = ("Found a device on serial port %s, but couldn't "
                       "open that port")
                self._error(msg % self.portString)
            # this should be large when making measurements
            self.com.timeout = 0.1
            self.startRemoteMode()
            self.type = self.getDeviceType()
            if self.type:
                msg = "Successfully opened %s on %s"
                logging.info(msg % (self.type, self.portString))
            else:
                self._error("PR655/PR670 isn't communicating")

    def __del__(self):
        try:
            self.endRemoteMode()
            time.sleep(0.1)
            self.com.close()
            logging.debug('Closed PR655 port')
        except Exception:
            pass

    def startRemoteMode(self):
        """Sets the Colorimeter into remote mode
        """
        reply = self.sendMessage(b'PHOTO', timeout=10.0)

    def getDeviceType(self):
        """Return the device type (e.g. 'PR-655' or 'PR-670')
        """
        reply = self.sendMessage(b'D111')  # returns errCode,
        return _stripLineEnds(reply.split(',')[-1])  # last element

    def getDeviceSN(self):
        """Return the device serial number
        """
        reply = self.sendMessage(b'D110')  # returns errCode,
        return _stripLineEnds(reply.split(',')[-1])  # last element

    def sendMessage(self, message, timeout=0.5, DEBUG=False):
        """Send a command to the photometer and wait an allotted
        timeout for a response (Timeout should be long for low
        light measurements)
        """
        # send complete message
        msg = "Sending command '%s' to %s"
        logging.debug(msg % (message, self.portString))
        if message[-1] != '\n':
            message += '\n'  # append a newline if necess

        # flush the read buffer first
        # read as many chars as are in the buffer
        self.com.read(self.com.inWaiting())

        # send the message
        for letter in message:
            # for PR655 have to send individual chars ! :-/
            self.com.write(letter)
            self.com.flush()

        time.sleep(0.2)  # PR655 can get cranky if rushed

        # get feedback (within timeout)
        self.com.timeout = timeout
        if message in ('d5\n', 'D5\n'):
            # we need a spectrum which will have multiple lines
            return self.com.readlines()
        else:
            return self.com.readline()

    def endRemoteMode(self):
        """Puts the colorimeter back into normal mode
        """
        self.com.write('Q')

    def getLastTristim(self):
        """Fetches (from the device) the last CIE 1931 Tristimulus values

        :returns:
            list: status, units, Tristimulus Values

        :see also:
            :func:`~PR655.measure` automatically populates pr655.lastTristim
            with just the tristimulus coordinates
        """
        result = self.sendMessage(b'D2')
        return result.split(',')

    def getLastUV(self):
        """Fetches (from the device) the last CIE 1976 u,v coords

        :returns:
            list: status, units, Photometric brightness, u, v

        :see also:
            :func:`~PR655.measure` automatically populates pr655.lastUV
            with [u,v]
        """
        result = self.sendMessage(b'D3')
        return result.split(',')

    def getLastXY(self):
        """Fetches (from the device) the last CIE 1931 x,y coords


        :returns:
            list: status, units, Photometric brightness, x,y

        :see also:
            :func:`~PR655.measure` automatically populates pr655.lastXY
            with [x,y]
        """
        result = self.sendMessage(b'D1')
        return result.split(',')

    def getLastSpectrum(self, parse=True):
        """This retrieves the spectrum from the last call to
        :func:`~PR655.measure`

        If `parse=True` (default):

            The format is a num array with 100 rows [nm, power]

        otherwise:

            The output will be the raw string from the PR650 and should then
            be passed to :func:`~PR655.parseSpectrumOutput`. It's more
            efficient to parse R,G,B strings at once than each individually.
        """
        raw = self.sendMessage(b'D5')  # returns a list where each list
        if parse:
            # skip the first 2 entries (info)
            return self.parseSpectrumOutput(raw[2:])
        else:
            return raw

    def getLastColorTemp(self):
        """Fetches (from the device) the color temperature (K) of the
        last measurement

        :returns:
            list: status, units, exponent, correlated color temp (Kelvins),
            CIE 1960 deviation

        :see also:
            :func:`~PR655.measure` automatically populates
            pr655.lastColorTemp with the color temp in Kelvins
        """
        result = self.sendMessage(b'D4')
        return result.split(',')

    def measure(self, timeOut=30.0):
        """Make a measurement with the device.

        This automatically populates:

            - ``.lastLum``
            - ``.lastSpectrum``
            - `.lastCIExy`
            - `.lastCIEuv`
        """
        reply = self.sendMessage(b'M0', timeout=30)
        self.measured = True
        CIEuv = self.getLastUV()
        CIExy = self.getLastXY()
        CIEtristim = self.getLastTristim()
        self.lastLum = float(CIEuv[2])
        self.lastUV = [float(CIEuv[3]), float(CIEuv[4])]
        self.lastXY = [float(CIExy[3]), float(CIExy[4])]
        self.lastTristim = [float(CIEtristim[2]), float(
            CIEtristim[3]), float(CIEtristim[4])]
        self.lastSpectrum = self.getLastSpectrum(parse=True)
        self.lastColorTemp = int(self.getLastColorTemp()[3])

    def parseSpectrumOutput(self, rawStr):
        """Parses the strings from the PR650 as received after sending
        the command 'D5'.
        The input argument "rawStr" can be the output from a single
        phosphor spectrum measurement or a list of 3 such measurements
        [rawR, rawG, rawB].
        """

        if len(rawStr) == 3:
            RGB = True
            rawR = rawStr[0][2:]
            rawG = rawStr[1][2:]
            rawB = rawStr[2][2:]
            nPoints = len(rawR)
        else:
            RGB = False
            nPoints = len(rawStr)
            raw = rawStr[2:]

        nm = []
        if RGB:
            power = [[], [], []]
            for n in range(nPoints):
                # each entry in list is a string like this:
                thisNm, thisR = rawR[n].split(',')
                thisR = thisR.replace('\r\n', '')
                thisNm, thisG = rawG[n].split(',')
                thisG = thisG.replace('\r\n', '')
                thisNm, thisB = rawB[n].split(',')
                thisB = thisB.replace('\r\n', '')
                exec('nm.append(%s)' % thisNm)
                exec('power[0].append(%s)' % thisR)
                exec('power[1].append(%s)' % thisG)
                exec('power[2].append(%s)' % thisB)
        else:
            power = []
            for n, point in enumerate(rawStr):
                # each entry in list is a string like this:
                thisNm, thisPower = point.split(',')
                nm.append(float(thisNm))
                power.append(float(thisPower.replace('\r\n', '')))
        return numpy.asarray(nm), numpy.asarray(power)


def _stripLineEnds(s):
    return s.replace('\r', '').replace('\n', '')
