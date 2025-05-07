#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trigger interface for the parallel port.

This module provides a simple trigger interface using the computer's parallel 
port. 

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'ParallelPortTrigger',
    'getOpenParallelPorts',
    'closeAllParallelPorts'
]

from .base import BaseTriggerBox

# used to keep track of open parallel ports to avoid multiple objects accessing
# the same port
_openParallelPorts = {}

# parallel port addresses on Windows
WIN_PPORT_ADDRESSES = {
    'LPT1': 0x0378,
    'LPT2': 0x0278,
    'LPT3': 0x0278
}


class ParallelPortTrigger(BaseTriggerBox):
    """Class for using the computer's parallel port as a trigger interface.

    Parameters
    ----------
    portAddress : int
        Address of the parallel port.

    """
    _deviceName = u"Parallel Port"
    _deviceVendor = u"Open Science Tools Ltd."

    def __init__(self, portAddress=0x378, **kwargs):
        """Initialize the parallel port trigger interface.

        Parameters
        ----------
        portAddress : int or None
            Address of the parallel port. Specify `None` if you plan to open 
            the port later using :func:`open`.

        """
        super().__init__(**kwargs)
        self._portAddress = portAddress
        self._parallelPort = None  # raw interface to parallel port

        if portAddress is not None:
            self.open()

    @staticmethod
    def _setupPort():
        """Setup the parallel port interface.

        This method will attempt to find a usable driver depending on your
        platform. If the parallel port is already open, this method will do
        nothing.

        Returns
        -------
        object
            Parallel port interface object.

        """
        parallelPort = None
        if sys.platform.startswith('linux'):
            try:
                from ._linux import PParallelLinux
            except ImportError:
                raise RuntimeError(
                    "The parallel port driver for Linux is not available. "
                    "Please install the parallel port driver interface "
                    "library `PParallelLinux` to use this feature.")

            parallelPort = PParallelLinux
        elif sys.platform == 'win32':
            drivers = dict(
                inpout32=('_inpout', 'PParallelInpOut'),
                inpoutx64=('_inpout', 'PParallelInpOut'),
                dlportio=('_dlportio', 'PParallelDLPortIO'))

            from ctypes import windll
            from importlib import import_module

            for key, val in drivers.items():
                driver_name, class_name = val
                try:
                    hasattr(windll, key)
                    parallelPort = getattr(
                        import_module('.' + driver_name, __name__), class_name)
                    break
                except (OSError, KeyError, NameError):
                    continue

            if parallelPort is None:
                logging.warning(
                    "psychopy.parallel has been imported but no parallel port "
                    "driver found. Install either inpout32, inpoutx64 or dlportio")
        else:
            logging.warning("psychopy.parallel has been imported on a Mac "
                            "(which doesn't have a parallel port?)")
        
        return parallelPort

    @staticmethod
    def closeAllParallelPorts():
        """Close all open parallel ports.

        This function will close all open parallel ports and remove them from the
        list of open ports. Any objects that were using the closed ports will
        raise an exception if they attempt to use the port.

        This function can be registered as an `atexit` handler to ensure that all
        parallel ports are closed when the program exits.

        """
        for port in _openParallelPorts.values():
            port.close()
        _openParallelPorts.clear()
    
    @staticmethod
    def getOpenParallelPorts():
        """Get a list of open parallel port addresses.

        Returns
        -------
        list

        """
        return list(_openParallelPorts.keys())

    def __hash__(self):
        """Get the hash value of the parallel port trigger interface.

        Returns
        -------
        int
            Hash value of the parallel port trigger interface.

        """
        return hash(self.portAddress)
    
    @staticmethod
    def isSupported():
        """Check if platform support parallel ports.

        This doesn't check if the parallel port is available, just if the
        interface is supported on this platform.

        Returns
        -------
        bool
            True if the parallel port trigger interface is supported, False
            otherwise.

        """
        return sys.platform != 'darwin'  # macs don't have parallel ports

    def setPortAddress(self, portAddress):
        """Set the address of the parallel port.

        If the desired adress is not in use by another object, the port will be
        closed and the address will be changed. Otherwise a `RuntimeError` will
        be raised.

        Common port addresses on Windows::

            LPT1 = 0x0378 or 0x03BC
            LPT2 = 0x0278 or 0x0378
            LPT3 = 0x0278

        on Linux ports are specifed as files in `/dev`::

            /dev/parport0

        Parameters
        ----------
        portAddress : int
            Address of the parallel port.

        """
        if self.isOpen:
            raise RuntimeError(
                "Cannot change the port address while the port is open.")

        # convert u"0x0378" into 0x0378
        if isinstance(address, str) and address.startswith('0x'):
            address = int(address, 16)

        self._portAddress = portAddress

    @property
    def portAddress(self):
        """Get the address of the parallel port.

        Returns
        -------
        int
            Address of the parallel port.

        """
        return self._portAddress

    def open(self):
        """Open the parallel port.

        This method will attempt to find a usable driver depending on your
        platform. If the parallel port is already open, this method will do
        nothing. You must set the port address using :func:`setPortAddress`
        or the constructor before opening the port.
        
        """
        if self._parallelPort is None:
            self._parallelPort = _openParallelPorts.get(self.portAddress, None)
            if self._parallelPort is None:
                parallelInterface = ParallelPortTrigger._setupPort()
                self._parallelPort = parallelInterface(self.portAddress)
                _openParallelPorts[self.portAddress] = self._parallelPort
        
    def close(self):
        """Close the parallel port.
        """
        if self._port is not None:
            del _openParallelPorts[self.portAddress]
            self._port = None

    @property
    def isOpen(self):
        """Check if the parallel port is open.

        Returns
        -------
        bool
            True if the parallel port is open, False otherwise.

        """
        return self._port is not None

    def setData(self, data):
        """Set the data to be presented on the parallel port (one ubyte).

        Alternatively you can set the value of each pin (data pins are pins 2-9 
        inclusive) using :func:`~psychopy.parallel.setPin`

        Examples
        --------
        Writing data to the port::

            parallel.setData(0)  # sets all pins low
            parallel.setData(255)  # sets all pins high
            parallel.setData(2)  # sets just pin 3 high (remember that pin2=bit0)
            parallel.setData(3)  # sets just pins 2 and 3 high

        You can also convert base 2 to int very easily in Python::

            parallel.setData(int("00000011", 2))  # pins 2 and 3 high
            parallel.setData(int("00000101", 2))  # pins 2 and 4 high

        """
        if not self.isOpen:
            raise RuntimeError("The parallel port is not open.")
        self._parallelPort.setData(data)

    def clearData(self):
        """Clear the data to be presented on the parallel port.

        This method will set all pins to low.

        """
        if not self.isOpen:
            raise RuntimeError("The parallel port is not open.")

        self._parallelPort.setData(0)

    def setPin(self, pinNumber, state):
        """Set a desired pin to be high (1) or low (0).

        Only pins 2-9 (incl) are normally used for data output::

            parallel.setPin(3, 1)  # sets pin 3 high
            parallel.setPin(3, 0)  # sets pin 3 low

        """
        if not self.isOpen:
            raise RuntimeError("The parallel port is not open.")
        self._parallelPort.setPin(pinNumber, state)

    def readPin(self, pinNumber):
        """Determine whether a desired (input) pin is high(1) or low(0).

        Returns
        -------
        int
            Pin state (1 or 0).

        """
        if not self.isOpen:
            raise RuntimeError("The parallel port is not open.")

        return self._parallelPort.readPin(pinNumber)

    def getPin(self, pinNumber):
        """Determine whether a desired (input) pin is high(1) or low(0).

        Returns
        -------
        int
            Pin state (1 or 0).

        """
        return self.readPin(pinNumber)

    def __del__(self):
        """Delete the parallel port trigger interface.
        """
        self.close()


# ------------------------------------------------------------------------------
# Utility functions for serial ports
#


def getOpenParallelPorts():
    """Get a list of open parallel port addresses.

    Returns
    -------
    list

    """
    return ParallelPortTrigger.getOpenParallelPorts()


def closeAllParallelPorts():
    """Close all open parallel ports.

    This function will close all open parallel ports and remove them from the
    list of open ports. Any objects that were using the closed ports will
    raise an exception if they attempt to use the port.

    This function can be registered as an `atexit` handler to ensure that all
    parallel ports are closed when the program exits.

    """
    ParallelPortTrigger.closeAllParallelPorts()

    
if __name__ == "__main__":
    pass
