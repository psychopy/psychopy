#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

from __future__ import absolute_import, print_function
from builtins import object
import weakref

from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class BaseBackend(object):
    """The backend class provides all the core low-level functions required by
    a Window class, such as the ability to create an OpenGL context and flip
    the window.

    Users simply call visual.Window(..., winType='pyglet') and the winType is
    then used by backends.getBackend(winType) which will locate the appropriate
    class and initialize an instance using the attributes of the Window.
    """
    # define GL here as a class attribute that includes all the opengl funcs
    # e.g. GL = pyglet.gl

    def __init__(self, win):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPyglet()

        :param: win is a PsychoPy Window (usually not fully created yet)
        """
        self.win = win  # this will use the @property to make/use a weakref
        pass

    def swapBuffers(self):
        """Set the gamma table for the graphics card

        """
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @attributeSetter
    def gamma(self, gamma):
        """Set the gamma table for the graphics card

        :param gamma: a single value or a triplet for separate RGB gamma values
        """
        self.__dict__['gamma'] = gamma
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @property
    def shadersSupported(self):
        """This is a read-only property indicating whether or not this backend
        supports OpenGL shaders"""
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    def setMouseVisibility(self, visibility):
        """Set visibility of the mouse to True or False"""
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    # Optional, depending on backend needs

    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. Is it needed?"
                        .format(self.win.winType)
                        )

    def onResize(self, width, height):
        """A method that will be called if the window detects a resize event
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. Is it needed?"
                        .format(self.win.winType)
                        )

    def setCurrent(self):
        """Sets this window to be the current rendering target (for backends
        where 2 windows are permitted, e.g. not pygame)
        """
        pass

    # Helper methods that don't need converting

    @property
    def win(self):
        """The PsychoPy Window that this backend is supporting, which provides
        various important variables (like size, units, color etc).

        NB win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        ref = self.__dict__['win']
        return ref()

    @win.setter
    def win(self, win):
        """The PsychoPy Window that this backend is supporting, which provides
        various important variables (like size, units, color etc).

        NB win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        self.__dict__['win'] = weakref.ref(win)

    @property
    def autoLog(self):
        """If the window has logging turned on then backend should too"""
        return self.win.autoLog

    @property
    def name(self):
        """Name of the backend is only used for logging purposes"""
        return "{}_backend".format(self.win.name)
