#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import glob
from itertools import chain
from psychopy import logging
from . import eyetracker, listener
from .manager import DeviceManager, deviceManager
from .base import BaseDevice, BaseResponse, BaseResponseDevice
from .exceptions import DeviceNotConnectedError

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

__all__ = [
    'forp',
    'cedrus',
    'minolta',
    'gammasci',
    'pr',
    'crs',
    'iolab',
    'eyetracker',
    'deviceManager',
    'listener'
]


def getSerialPorts():
    """Finds the names of all (virtual) serial ports present on the system

    Returns
    -------
    list
        Iterable with all the serial ports.

    """
    if sys.platform == "darwin":
        ports = [
            '/dev/tty.USA*',  # keyspan twin adapter is usually USA28X13P1.1
            '/dev/tty.Key*',  # some are Keyspan.1 or Keyserial.1
            '/dev/tty.modem*',
            '/dev/cu.usbmodem*',  # for PR650
            '/dev/tty.usbserial*',  # for the 'Plugable' converter,
                                    # according to Tushar Chauhan
        ]
    elif sys.platform.startswith("linux"):
        ports = [
            "/dev/ttyACM?",  # USB CDC devices (virtual serial ports)
            "/dev/ttyUSB?",  # USB to serial adapters using the
                             # usb-serial kernel module
            "/dev/ttyS?",   # genuine serial ports usually
                            # /dev/ttyS0 or /dev/ttyS1
        ]
    elif sys.platform == "cygwin":
        # I don't think anyone has actually tried this
        # Cygwin maps the windows serial ports like this
        ports = ["/dev/ttyS?", ]
    elif sys.platform == "win32":
        # While PsychoPy does support using numeric values to specify
        # which serial port to use, it is better in this case to
        # provide a cannoncial name.
        return map("COM{0}".format, range(11))  # COM0-10
    else:
        logging.error("We don't support serial ports on {0} yet!"
                      .format(sys.platform))
        return []

    # This creates an iterator for each glob expression. The glob
    # expressions are then chained together. This is more efficient
    # because it means we don't perform the lookups before we actually
    # need to.
    return chain.from_iterable(map(glob.iglob, ports))


def getAllPhotometers():
    """Gets all available photometers.

    The returned photometers may vary depending on which drivers are installed.
    Standalone PsychoPy ships with libraries for all supported photometers.

    Returns
    -------
    list
        A list of all photometer classes.

    """
    from .photometer import getAllPhotometerClasses

    # need values returned as a list for now
    return getAllPhotometerClasses()


def getPhotometerByName(name):
    """Gets a Photometer class by name.

    You can use either short names like 'pr650' or a long name like 'CRS
    ColorCAL'.

    Parameters
    ----------
    name : str
        The name of the device.

    Returns
    -------
    object
        Returns the photometer matching the passed in device name or `None` if
        we were unable to find it.

    """
    for photom in getAllPhotometers():
        # longName is used from the GUI and driverFor is for coders
        if name.lower() in photom.driverFor or name == photom.longName:
            return photom


def findPhotometer(ports=None, device=None):
    """Try to find a connected photometer/photospectrometer!

    PsychoPy will sweep a series of serial ports trying to open them.
    If a port successfully opens then it will try to issue a command to
    the device. If it responds with one of the expected values then it
    is assumed to be the appropriate device.

    Parameters
    ----------
    ports : list
        A list of ports to search. Each port can be a string (e.g. 'COM1',
        '/dev/tty.Keyspan1.1') or a number (for win32 comports only). If `None`
        is provided then PsychoPy will sweep COM0-10 on Win32 and search known
        likely port names on MacOS and Linux.
    device : str
        String giving expected device (e.g. 'PR650', 'PR655', 'CS100A', 'LS100',
        'LS110', 'S470'). If this is not given then an attempt will be made to
        find a device of any type, but this often fails.

    Returns
    -------
    object or None
        An object representing the first photometer found, `None` if the ports
        didn't yield a valid response. `None` if there were not even any valid
        ports (suggesting a driver not being installed.)

    Examples
    --------
    Sweeps ports 0 to 10 searching for a PR655::

        photom = findPhotometer(device='PR655')
        print(photom.getLum())
        if hasattr(photom, 'getSpectrum'):
            # can retrieve spectrum (e.g. a PR650)
            print(photom.getSpectrum())

    """
    if isinstance(device, str):
        photometers = [getPhotometerByName(device)]
    elif isinstance(device, Iterable):
        # if we find a string assume it is a name, otherwise treat it like a
        # photometer
        photometers = [getPhotometerByName(d)
                       if isinstance(d, str) else d
                       for d in device]
    else:
        photometers = getAllPhotometers()

    # determine candidate ports
    if ports is None:
        ports = getSerialPorts()
    elif type(ports) in (int, float, str):
        ports = [ports]  # so that we can iterate

    # go through each port in turn
    photom = None
    logging.info('scanning serial ports...')
    logging.flush()
    for thisPort in ports:
        logging.info('...{}'.format(thisPort))
        logging.flush()
        for Photometer in photometers:
            # Looks like we got an invalid photometer, carry on
            if Photometer is None:
                continue
            try:
                photom = Photometer(port=thisPort)
            except Exception as ex:
                msg = "Couldn't initialize photometer {0}: {1}"
                logging.error(msg.format(Photometer.__name__, ex))
                # We threw an exception so we should just skip ahead
                continue
            if photom.OK:
                logging.info(' ...found a %s\n' % (photom.type))
                logging.flush()
                # we're now sure that this is the correct device and that
                # it's configured now increase the number of attempts made
                # to communicate for temperamental devices!
                if hasattr(photom, 'setMaxAttempts'):
                    photom.setMaxAttempts(10)
                # we found one so stop looking
                return photom
            else:
                if photom.com and photom.com.isOpen:
                    logging.info('closing port')
                    photom.com.close()

        # If we got here we didn't find one
        logging.info('...nope!\n\t')
        logging.flush()

    return None


if __name__ == "__main__":
    pass
