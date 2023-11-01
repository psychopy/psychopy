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
