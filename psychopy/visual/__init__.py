#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Container for all visual-related functions and classes'''

# window, should always be loaded first
from .window import Window, getMsPerFrame

# non-private helpers
from .helpers import createTexture, pointInPolygon, polygonsOverlap

# non-stimulus classes only derived from Object
from .aperture import Aperture
from .custommouse import CustomMouse

# stimuli only derived from Object
from .basevisual import BaseVisualStim
from .elementarray import ElementArrayStim
from .ratingscale import RatingScale
from .simpleimage import SimpleImageStim

# stimuli derived from BaseVisualStim
from .dot import DotStim
from .grating import GratingStim
from .image import ImageStim
from .movie import MovieStim
from .shape import ShapeStim
from .text import TextStim

# stimuli derived from GratingStim
from .bufferimage import BufferImageStim
from .patch import PatchStim
from .radial import RadialStim

# stimuli derived from ShapeStim
from .line import Line
from .polygon import Polygon
from .rect import Rect

# stimuli derived from Polygon
from .circle import Circle
