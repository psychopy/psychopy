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

import os
import sys
import pygame
from ._base import BaseBackend
import psychopy
from psychopy import core, platform_specific
from psychopy.tools.attributetools import attributeSetter

try:
    import pyglet
    GL = pyglet.gl
except ImportError:
    import OpenGL
    GL = OpenGL


class PygameBackend(BaseBackend):
    """The pygame backend is built on SDL for cross-platform controls
    """
    GL = GL

    def __init__(self, win, *args, **kwargs):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPygame()

        :param: win is a PsychoPy Window (usually not fully created yet)
        """
        BaseBackend.__init__(self, win)  # sets up self.win=win as weakref

        # pygame.mixer.pre_init(22050,16,2)  # set the values to initialise
        # sound system if it gets used
        pygame.init()
        if win.allowStencil:
            pygame.display.gl_set_attribute(pygame.locals.GL_STENCIL_SIZE, 8)

        try:  # to load an icon for the window
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pygame.image.load(iconFile)
            pygame.display.set_icon(icon)
        except Exception:
            pass  # doesn't matter
        win.useRetina = False
        # these are ints stored in pygame.locals
        winSettings = pygame.OPENGL | pygame.DOUBLEBUF
        if win._isFullScr:
            winSettings = winSettings | pygame.FULLSCREEN
            # check screen size if full screen
            scrInfo = pygame.display.Info()
            win._checkMatchingSizes(win.size, [scrInfo.current_w,
                                                 scrInfo.current_h])
        elif not win.pos:
            # centre video
            os.environ['SDL_VIDEO_CENTERED'] = "1"
        else:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (win.pos[0],
                                                            win.pos[1])
        if sys.platform == 'win32':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        if not win.allowGUI:
            winSettings = winSettings | pygame.NOFRAME
            self.setMouseVisibility(False)
            pygame.display.set_caption('PsychoPy (NB use with allowGUI=False '
                                       'when running properly)')
        else:
            self.setMouseVisibility(True)
            pygame.display.set_caption('PsychoPy')
        self.winHandle = pygame.display.set_mode(win.size.astype('i'),
                                                 winSettings)
        pygame.display.set_gamma(1.0)  # this will be set appropriately later
        # This is causing segfault although it used to be for pyglet only anyway
        # pygame under mac is not syncing to refresh although docs say it should
        # if sys.platform == 'darwin':
        #     platform_specific.syncSwapBuffers(2)

    def swapBuffers(self, flipThisFrame=True):
        """Do the actual flipping of the buffers (Window will take care of
        additional things like timestamping. Keep this methods as short as poss

        :param flipThisFrame: has no effect on this backend
        """
        if pygame.display.get_init():
            if flipThisFrame:
                pygame.display.flip()
            # keeps us in synch with system event queue
            self.dispatchEvents()
        else:
            core.quit()  # we've unitialised pygame so quit

    def close(self):
        """Close the window and uninitialize the resources
        """
        pygame.display.quit()

    @property
    def shadersSupported(self):
        """This is a read-only property indicating whether or not this backend
        supports OpenGL shaders"""
        return False

    def setMouseVisibility(self, visibility):
        """Set visibility of the mouse to True or False"""
        pygame.mouse.set_visible(visibility)

    # Optional, depending on backend needs

    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        pygame.event.pump()

    def onResize(self, width, height):
        """This does nothing; not supported by our pygame backend at the moment
        """
        pass  # the pygame window doesn't currently support resizing

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        # use pygame's own function for this
        pygame.display.set_gamma(gamma[0], gamma[1], gamma[2])

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        # use pygame's own function for this
        pygame.display.set_gamma_ramp(
                gammaRamp[:, 0], gammaRamp[:, 1], gammaRamp[:, 2])

    def setFullScr(self, value):
        """Sets the window to/from full-screen mode"""
        raise NotImplementedError("Toggling fullscreen mode is not currently "
                             "supported on pygame windows")
