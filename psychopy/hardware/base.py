#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for hardware device interfaces.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'BaseDevice'
]


class BaseDevice:
    """
    Base class for device interfaces, includes support for DeviceManager and adding listeners.
    """
    listeners = []

    def __init_subclass__(cls, aliases=None):
        from psychopy.hardware.manager import DeviceManager
        import inspect
        # handle no aliases
        if aliases is None:
            aliases = []
        # if given a class, get its class string
        mro = inspect.getmodule(cls).__name__ + "." + cls.__name__
        # register aliases
        for alias in aliases:
            DeviceManager.registerAlias(alias, mro)
        # store class string
        DeviceManager.deviceClasses.append(mro)

        return cls

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch messages.
        """
        from . import listener as lsnr
        # make listener if needed
        if not isinstance(listener, lsnr.BaseListener):
            # if given a string rather than an object handle, make an object of correct type
            if listener == "liaison":
                from psychopy.hardware import DeviceManager
                if DeviceManager.liaison is None:
                    raise AttributeError(
                        "Cannot create a `liaison` listener as no liaison server is connected to DeviceManager."
                    )
                listener = lsnr.LiaisonListener(DeviceManager.liaison)
            if listener == "print":
                listener = lsnr.PrintListener()
            if listener == "log":
                listener = lsnr.LoggingListener()
        # add listener handle
        self.listeners.append(listener)
        # start loop if requested
        if startLoop:
            listener.startLoop(self)

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # stop any dispatch loops
        for listener in self.listeners:
            listener.stopLoop()
        # remove all listeners
        self.listeners = []

        return True

    @staticmethod
    def getAvailableDevices():
        """
        Get all available devices of this type.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `getAvailableDevices`"
        )


if __name__ == "__main__":
    pass
