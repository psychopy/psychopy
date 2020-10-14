#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2014 Allen Institute for Brain Science

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License Version 3
as published by the Free Software Foundation on 29 June 2007.
This program is distributed WITHOUT WARRANTY OF MERCHANTABILITY OR FITNESS
FOR A PARTICULAR PURPOSE OR ANY OTHER WARRANTY, EXPRESSED OR IMPLIED.
See the GNU General Public License Version 3 for more details.
You should have received a copy of the GNU General Public License along
with this program. If not, see http://www.gnu.org/licenses/
"""
from __future__ import absolute_import, division, print_function

from builtins import object
from past.utils import old_div
import pyglet
GL = pyglet.gl


class ProjectorFramePacker(object):
    """Class which packs 3 monochrome images per RGB frame.

    Allowing 180Hz stimuli with DLP projectors such as TI LightCrafter 4500.

    The class overrides methods of the visual.Window class to pack a
    monochrome image into each RGB channel. PsychoPy is running at 180Hz.
    The display device is running at 60Hz.  The output projector is producing
    images at 180Hz.

    Frame packing can work with any projector which can operate in
    'structured light mode' where each RGB channel is presented
    sequentially as a monochrome image.  Most home and office projectors
    cannot operate in this mode, but projectors designed for machine
    vision applications typically will offer this feature.

    Example usage to use ProjectorFramePacker::

        from psychopy.visual.windowframepack import ProjectorFramePacker
        win = Window(monitor='testMonitor', screen=1,
                     fullscr=True, useFBO = True)
        framePacker = ProjectorFramePacker (win)
    """

    def __init__(self, win):
        """
        :Parameters:

            win : Handle to the window.

        """
        super(ProjectorFramePacker, self).__init__()
        self.win = win
        # monkey patch window
        win._startOfFlip = self.startOfFlip
        win._endOfFlip = self.endOfFlip

        # This part is increasingly ugly.  Add a function to set these values?
        win._monitorFrameRate = 180.0
        win.monitorFramePeriod = old_div(1.0, win._monitorFrameRate)
        win.refreshThreshold = (old_div(1.0, win._monitorFrameRate)) * 1.2

        # enable Blue initially, since projector output sequence is BGR
        GL.glColorMask(False, False, True, True)
        self.flipCounter = 0

    def startOfFlip(self):
        """Return True if all channels of the RGB frame have been filled
        with monochrome images, and the associated window should perform
        a hardware flip"""
        return self.flipCounter % 3 == 2

    def endOfFlip(self, clearBuffer):
        """Mask RGB cyclically after each flip.
        We ignore clearBuffer and just auto-clear after each hardware flip.
        """
        if self.flipCounter % 3 == 2:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        self.flipCounter += 1
        if self.flipCounter % 3 == 0:
            GL.glColorMask(False, True, False, True)  # enable green
        elif self.flipCounter % 3 == 1:
            GL.glColorMask(True, False, False, True)  # enable red
        elif self.flipCounter % 3 == 2:
            GL.glColorMask(False, False, True, True)  # enable blue
