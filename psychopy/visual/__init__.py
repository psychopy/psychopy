#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Container for all visual-related functions and classes'''

from psychopy import logging

# needed for backwards-compatibility
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED,
                                FINISHED, PRESSED, RELEASED, FOREVER)

# window, should always be loaded first
from .window import Window, getMsPerFrame, openWindows

# non-private helpers
from .helpers import pointInPolygon, polygonsOverlap

# absolute essentials (nearly all experiments will need these)
from .basevisual import BaseVisualStim
from .image import ImageStim
from .text import TextStim

from psychopy.visual import gamma  # done in window anyway
from psychopy.visual import filters  

# need absolute imports within lazyImports

lazyImports = """
# stimuli derived from object or MinimalStim
from psychopy.visual.aperture import Aperture  # uses BaseShapeStim or ImageStim
from psychopy.visual.custommouse import CustomMouse
from psychopy.visual.elementarray import ElementArrayStim
from psychopy.visual.ratingscale import RatingScale
from psychopy.visual.simpleimage import SimpleImageStim

# stimuli derived from BaseVisualStim
from psychopy.visual.dot import DotStim
from psychopy.visual.grating import GratingStim
from psychopy.visual.secondorder import EnvelopeGrating
from psychopy.visual.movie import MovieStim
from psychopy.visual.movie2 import MovieStim2
from psychopy.visual.movie3 import MovieStim3
from psychopy.visual.shape import BaseShapeStim

# stimuli derived from GratingStim
from psychopy.visual.bufferimage import BufferImageStim
from psychopy.visual.patch import PatchStim
from psychopy.visual.radial import RadialStim

# stimuli derived from BaseShapeStim
from psychopy.visual.shape import ShapeStim

# stimuli derived from ShapeStim
from psychopy.visual.line import Line
from psychopy.visual.polygon import Polygon
from psychopy.visual.rect import Rect

# stimuli derived from Polygon
from psychopy.visual.circle import Circle

from psychopy.visual.textbox import TextBox
"""
try:
    from psychopy.contrib.lazy_import import lazy_import
    lazy_import(globals(), lazyImports)
except:
    exec(lazyImports)
