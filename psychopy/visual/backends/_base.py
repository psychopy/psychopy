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
import weakref

from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class BaseBackend(object):

    def __init__(self):
        """In init we need to set up the window
        """
        pass

    def swapBuffers(self):
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @attributeSetter
    def gamma(self, gamma):
        """Set the gamma table for the graphics card

        :param gamma:
        """
        self.__dict__['gamma'] = gamma
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @property
    def shadersSupported(self):
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    def setMouseVisibility(self, visibility):
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

    # Helper methods that don't need converting

    @property
    def win(self):
        """win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        ref = self.__dict__['win']
        return ref()

    @win.setter
    def win(self, win):
        self.__dict__['win'] = weakref.ref(win)
