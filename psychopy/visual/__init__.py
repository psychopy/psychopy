#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Container for all visual-related functions and classes
"""

# When importing this module, aliases are created which reference classes and
# functions in sub-modules. This allows users to access objects spread across
# multiple modules through the `visual` class.
#
# To prevent circular import of `psychopy.visual`. Classes and functions
# included in the base `visual` package must use relative imports when importing
# anything from other `visual` modules. After `visual` is realized, you can use
# the fully-qualified name of `psychopy.visual` in your import statements.
#

from __future__ import absolute_import, print_function

import sys

if sys.platform == 'win32':
    from pyglet.libs import win32  # pyglet patch for ANACONDA install
    from ctypes import *
    win32.PUINT = POINTER(wintypes.UINT)

# ------------------------------------------------------------------------------
# Core Visual Classes
#
# These classes do not have any optional outside dependencies and are unlikely
# to fail when being imported.
#

from psychopy.visual import filters
from psychopy.visual.backends import gamma

# window, should always be loaded first
from .window import Window, getMsPerFrame, openWindows
from . import shaders

# absolute essentials (nearly all experiments will need these)
from .basevisual import BaseVisualStim

# non-private helpers
from .helpers import pointInPolygon, polygonsOverlap
from .image import ImageStim
from .text import TextStim
from .form import Form
from .button import ButtonStim
from .brush import Brush
from .textbox2.textbox2 import TextBox2

# stimuli derived from object or MinimalStim
from .aperture import Aperture  # uses BaseShapeStim, ImageStim
from .custommouse import CustomMouse
from .elementarray import ElementArrayStim
from .ratingscale import RatingScale
from .slider import Slider
from .simpleimage import SimpleImageStim

# stimuli derived from BaseVisualStim
from .shape import BaseShapeStim
from .dot import DotStim
from .grating import GratingStim
from .secondorder import EnvelopeGrating

# stimuli derived from GratingStim
from .bufferimage import BufferImageStim
from .patch import PatchStim
from .radial import RadialStim
from .noise import NoiseStim

# stimuli derived from BaseShapeStim
from .shape import ShapeStim

# stimuli derived from ShapeStim
from .line import Line
from .polygon import Polygon
from .rect import Rect
from .pie import Pie

# stimuli derived from Polygon
from .circle import Circle
from .textbox import TextBox

# 3D stimuli support
from .stim3d import LightSource
from .stim3d import SceneSkybox
from .stim3d import BlinnPhongMaterial
from .stim3d import RigidBodyPose
from .stim3d import BoundingBox
from .stim3d import SphereStim
from .stim3d import BoxStim
from .stim3d import PlaneStim
from .stim3d import ObjMeshStim

# warping and framepacking
from .windowwarp import Warper
from .windowframepack import ProjectorFramePacker

# ------------------------------------------------------------------------------
# Extended Visual Classes
#
# These classes have optional third-party dependencies and may fail to load if
# they are not present or supported on the platform. These modules are lazy
# loaded so they don't crash the import process if they are not available.
#

lazyImports = """
# stimuli derived from BaseVisualStim
from psychopy.visual.dot import DotStim
from psychopy.visual.grating import GratingStim
from psychopy.visual.secondorder import EnvelopeGrating
from psychopy.visual.movie import MovieStim
from psychopy.visual.movie2 import MovieStim2
from psychopy.visual.movie3 import MovieStim3
from psychopy.visual.vlcmoviestim import VlcMovieStim

# rift support
from psychopy.visual.rift import Rift

"""

try:
    from psychopy.contrib.lazy_import import lazy_import
    lazy_import(globals(), lazyImports)
except Exception:
    exec(lazyImports)
