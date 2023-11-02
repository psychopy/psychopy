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
    """Base class for device interfaces."""
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
