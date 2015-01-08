#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Container for all visual-related functions and classes'''

from psychopy import logging

# needed for backwards-compatibility
from psychopy.constants import *

# window, should always be loaded first
from psychopy.visual.window import Window, getMsPerFrame, openWindows

# non-private helpers
from psychopy.visual.helpers import pointInPolygon, polygonsOverlap

# stimuli derived from object or MinimalStim
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.aperture import Aperture
from psychopy.visual.custommouse import CustomMouse
from psychopy.visual.elementarray import ElementArrayStim
from psychopy.visual.ratingscale import RatingScale
from psychopy.visual.simpleimage import SimpleImageStim

# stimuli derived from BaseVisualStim
from psychopy.visual.dot import DotStim
from psychopy.visual.grating import GratingStim
from psychopy.visual.image import ImageStim
from psychopy.visual.movie import MovieStim

try:
    from psychopy.visual.movie2 import MovieStim2
except:
    logging.warn("Movie2 stim could not be imported and won't be available")

from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim

# stimuli derived from GratingStim
from psychopy.visual.bufferimage import BufferImageStim
from psychopy.visual.patch import PatchStim
from psychopy.visual.radial import RadialStim

# stimuli derived from ShapeStim
from psychopy.visual.line import Line
from psychopy.visual.polygon import Polygon
from psychopy.visual.rect import Rect

# stimuli derived from Polygon
from psychopy.visual.circle import Circle

# TextBox alternative to TextStim
try:    
    # Ensure monospace Fonts are available ....
    font_names = []
    import textbox
    from textbox import getFontManager
    fm=getFontManager()
    font_names = fm.getFontFamilyNames()
    assert len(font_names) > 0
    from textbox import TextBox
except Exception, e:
    logging.warn("TextBox stim could not be imported and won't be available.")
    if len(font_names) == 0:
        logging.warn("TextBox Font Manager Found No Fonts.")
