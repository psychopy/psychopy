#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

from __future__ import absolute_import, print_function
from builtins import object

import pygame
from ._base import BaseBackend
from psychopy import core
from psychopy.tools.attributetools import attributeSetter


class PygameBackend(BaseBackend):
    """Backends provide the underlying functionality of the window. They need to
    be able to provide an OpenGL rendering context and the ability to swap
    buffers and set gamma etc. Backend classes are not usually used directly by
    users. The Window class provides all the key functionality that you need.

    To create a new backend subclass this and override (at least) all the
    methods that are marked with NotImplemented errors

    Use an attribute self.winHandle to point to the actual window in your
    underlying lib

    """

    def __init__(self):
        """Create the window here
        """
        pass

    def swapBuffers(self, flipThisFrame=True):
        """Do the actual flipping of the buffers (Window will take care of
        additional things like timestamping. Keep this methods as short as poss

        :param flipThisFrame: has no effect on this backend
        """
        if pygame.display.get_init():
            if flipThisFrame:
                pygame.display.flip()
            # keeps us in synch with system event queue
            pygame.event.pump()
        else:
            core.quit()  # we've unitialised pygame so quit

    @attributeSetter
    def gamma(self, gamma):
        """Set the gamma table for the graphics card

        :param gamma:
        """
        self.__dict__['gamma'] = gamma
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")

    @property
    def shadersSupported(self):
        """A method to determine
        """
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")
        # return False  # or True! duh!

    def setMouseVisibility(self, visibility):
        """Set the visibility of hte mouse to the new value

        :param visibility: True/False or 1/0
        """
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        self.winHandle.set_gamma(gamma[0], gamma[1], gamma[2])

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        self.winHandle.set_gamma_ramp(
                gammaRamp[:, 0], gammaRamp[:, 1], gammaRamp[:, 2])
