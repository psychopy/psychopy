#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['MovieStim']

import os
import sys
import threading
import ctypes
import weakref

from psychopy import core, logging
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import numpy
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl


PREFERRED_VIDEO_LIB = 'ffpyplayer'


class MovieStim(BaseVisualStim, ContainerMixin):
    """Class for presenting movie clips as stimuli.

    Parameters
    ----------
    videoLib : str or None
        Library to use for video decoding. By default, the 'preferred' library
        by PsychoPy developers is used. Default is `'ffpyplayer'`.

    """
    def __init__(self, win,
                 filename="",
                 videoLib='ffpyplayer',
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),  # remove?
                 colorSpace='rgb',
                 opacity=1.0,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 interpolate=True,
                 autoStart=True):

        self.win = win


