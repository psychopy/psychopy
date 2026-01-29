#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for using photometers.

This module serves as the entry point for plugin classes implementing
third-party photometer interfaces. All installed interfaces are discoverable
by calling the :func:`getAllPhotometers()` function.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'addPhotometer',
    'getAllPhotometers',
    'getAllPhotometerClasses'
]

from psychopy.hardware.base import BaseResponseDevice, BaseResponse
from psychopy import layout, logging

from psychopy.plugins import PluginStub


class PhotometerResponse(BaseResponse):
    """
    Response from a photometer device. Value can be a single integer, could represent overall 
    luminance or the value of a single gun.
    """
    pass


class BasePhotometerDevice(BaseResponseDevice):
    responseClass = PhotometerResponse

    def getLum(self):
        """
        Get luminance according to pixel values.
        """
        # dispatch messages and return the most recent
        self.dispatchMessages()
        if self.responses:
            resp = self.responses[-1]
            return resp.value
        else:
            # if no messages, assume no luminance
            return 0


class ScreenBufferPhotometerDevice(BasePhotometerDevice):
    """
    Samples pixel colors from the screen buffer to emulate a photometer. Useful only for teaching, 
    as the output will always behave as if the screen is perfectly calibrated, as there's no 
    physical measurement involved.

    Parameters
    ----------
    win : psychopy.visual.Window
        Window to pull pixel values from
    pos : tuple, list
        Position of the patch of pixels to pretend there is a photometer looking at
    size : tuple, list
        Size of the patch of pixels to pretend there is a photometer looking at
    units : str
        "Spatial units in which to interpret size and position"
    """
    def __init__(self, win, pos=None, size=None, units=None):
        # initialize
        BaseResponseDevice.__init__(self)
            # store win
        self.win = win
        # default rect
        self.rect = None
        # make clock
        from psychopy.core import Clock
        self.clock = Clock()
        # store position params
        self.units = units
        self.pos = pos
        self.size = size
    
    @property
    def pos(self):
        return getattr(self._pos, self.units)
    
    @pos.setter
    def pos(self, value):
        self._pos = layout.Position(value, units=self.units, win=self.win)
    
    @property
    def size(self):
        return getattr(self._size, self.units)
    
    @size.setter
    def size(self, value):
        self._size = layout.Size(value, units=self.units, win=self.win)

    def dispatchMessages(self):
        """
        When called, dispatch a single reading.
        """
        # get rect
        left, bottom = self._pos.pix + self.win.size / 2
        w, h = self._size.pix
        left = int(left - w / 2)
        bottom = int(bottom - h / 2)
        w = int(w)
        h = int(h)
        # read front buffer luminances for specified area
        pixels = self.win._getPixels(
            buffer="front",
            rect=(left, bottom, w, h),
            makeLum=True
        )
        # dispatch a message
        self.receiveMessage(
            self.parseMessage(pixels.mean() / 255)
        )

    def parseMessage(self, message):
        return PhotometerResponse(
            t=self.clock.getTime(),
            value=message,
            device=self
        )

    def isSameDevice(self, other):
        return isinstance(other, ScreenBufferPhotometerDevice)
    
    @staticmethod
    def getAvailableDevices():
        # there's only ever one
        return [{
            'deviceName': "Photometer Emulator",
            'deviceClass': "psychopy.hardware.photometer.ScreenBufferPhotometerDevice",
            'win': "session.win",
        }]


# --- legacy methods ---


def addPhotometer(cls):
    """
    DEPRECATED: Photometer classes are added on import, so this function is no longer needed.

    Parameters
    ----------
    cls : Any
        Class specifying a photometer interface.
    """
    logging.warning(
        "`addPhotometer` is deprecated, photometer classes are added on import so this function "
        "is not needed."
    )


def getAllPhotometers():
    """
    Legacy method to get available photometers. Will return subclasses of BasePhotometerDevice as 
    well as legacy handlers for previously supported devices.

    Returns
    -------
    dict
        Device classes against the names by which to represent them.
    """
    # get photometer classes the new way: by looking for subclasses of BasePhotometerDevice
    found = BasePhotometerDevice.__subclasses__()
    # import classes which used to be in PsychoPy
    from psychopy.hardware.crs.colorcal import ColorCAL
    from psychopy.hardware.crs.optical import OptiCAL
    from psychopy.hardware.pr import PR655, PR650
    from psychopy.hardware.minolta import LS100, CS100A
    from psychopy.hardware.gammasci import S470
    # include any which aren't PluginStub's
    for cls in (
        ColorCAL,
        OptiCAL,
        PR655, 
        PR650,
        LS100, 
        CS100A,
        S470
    ):
        if not issubclass(cls, PluginStub):
            found.append(cls)

    return {
        cls.__name__: cls
        for cls in found
    }


def getAllPhotometerClasses():
    """
    Legacy method to get available photometers. Will return subclasses of BasePhotometerDevice as 
    well as legacy handlers for previously supported devices.

    Returns
    -------
    dict
        Device classes against the names by which to represent them.
    """
    return getAllPhotometers()
