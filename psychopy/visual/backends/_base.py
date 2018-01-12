#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
"""

from __future__ import absolute_import, print_function
from builtins import object
import weakref

from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class _BaseBackend(object):

    def __init__(self):
        """In init we need to set up the window
        """
        pass

    def swapBuffers(self):
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")

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
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")

    def setMouseVisibility(self, visibility):
        raise NotImplementedError(
                "Backend is has failed to override a necessary method")

    ## Optional depending on backend needs
    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. It may not be needed but check")

    ## Helper methods that don't need converting

    @property
    def win(self):
        """win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        ref = self.__dict__['win']
        return ref()

    @win.setter
    def win.setter(self, win):
        self.__dict__['win'] = weakref.ref(win)
