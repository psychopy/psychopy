#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base classes for trigger box interfaces.

Trigger boxes are used to send electrical signals to external devices. They are
typically used to synchronize the presentation of stimuli with the recording of
physiological data. This module provides a common interface for accessing
trigger boxes from within PsychoPy.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['BaseTriggerBox']


class BaseTriggerBox:
    """Base class for trigger box interfaces.

    This class defines the minimal interface for trigger box implementations. 
    All trigger box implementations should inherit from this class and override
    its methods.

    """
    _deviceName = u""  # name of the trigger box, shows up in menus
    _deviceVendor = u""  # name of the manufacturer

    def __init__(self, *args, **kwargs):
        """Initialize the trigger box interface.
        """
        pass

    @property
    def deviceName(self):
        """Get the name of the trigger box.

        Returns
        -------
        str
            Name of the trigger box.

        """
        return self._deviceName

    @property
    def deviceVendor(self):
        """Get the name of the manufacturer.

        Returns
        -------
        str
            Name of the manufacturer.

        """
        return self._deviceVendor

    def getCapabilities(self, **kwargs):
        """Get the capabilities of the trigger box.

        The returned dictionary contains information about the capabilities of
        the trigger box. The strutcture of the dictionary may vary between
        trigger box implementations, so it is recommended to check if a key 
        exists before accessing it.

        Returns
        -------
        dict
            Capabilities of the trigger box. The names of the capabilities are
            the keys of the dictionary. The values are information realted to
            the specified capability.

        Examples
        --------
        Check what the required baudrate of the device is:

            useBaudrate = getCapabilities()['baudrate']

        """
        return {}

    def open(self, **kwargs):
        """Open a connection to the trigger box."""
        pass

    def close(self, **kwargs):
        """Close the trigger box."""
        pass

    @property
    def isOpen(self):
        """Check if the trigger box connection is open.

        Returns
        -------
        bool
            True if the trigger box is open, False otherwise.

        """
        return False

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        self.close()

    def setData(self, data, **kwargs):
        """Set the data to be sent.

        Parameters
        ----------
        data : int
            Data to be sent.

        """
        pass

    def getData(self, **kwargs):
        """Get the data to be sent.

        Returns
        -------
        int
            Data to be sent.

        """
        pass

    def setPin(self, pin, value, **kwargs):
        """Set the value of a pin.

        Parameters
        ----------
        pin : int
            Pin number.
        value : int
            Value to be set.

        """
        pass

    def getPin(self, pin, **kwargs):
        """Read the value of a pin.

        Parameters
        ----------
        pin : int
            Pin number.

        Returns
        -------
        int
            Value of the pin.

        """
        pass

    def __del__(self):
        """Clean up the trigger box."""
        pass


if __name__ == "__main__":
    pass
