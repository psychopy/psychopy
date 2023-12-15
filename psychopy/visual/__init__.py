#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Container for all visual-related functions and classes
"""

import sys
if sys.platform == 'win32':
    from pyglet.libs import win32  # pyglet patch for ANACONDA install
    from ctypes import *
    from psychopy import prefs
    win32.PUINT = POINTER(wintypes.UINT)
    # get the preference for high DPI
    if 'highDPI' in prefs.hardware.keys():  # check if we have the option
        enableHighDPI = prefs.hardware['highDPI']
        # check if we have OS support for it
        if enableHighDPI:
            try:
                windll.shcore.SetProcessDpiAwareness(enableHighDPI)
            except OSError:
                pass

from psychopy import event  # import before visual or
from psychopy.visual import filters
from psychopy.visual.backends import gamma
# absolute essentials (nearly all experiments will need these)
from .basevisual import BaseVisualStim
# non-private helpers
from .helpers import pointInPolygon, polygonsOverlap
from .image import ImageStim
from .text import TextStim
from .form import Form
from .brush import Brush
from .textbox2.textbox2 import TextBox2
from .button import ButtonStim
from .roi import ROI
from .target import TargetStim
# window, should always be loaded first
from .window import Window, getMsPerFrame, openWindows

# needed for backwards-compatibility

# need absolute imports within lazyImports

# A newer alternative lib is apipkg but then we have to specify all the vars
# that will be included, not just the lazy ones? Syntax is:
# import apipkg
# apipkg.initpkg(__name__, {
#        'GratingStim': "psychopy.visual.grating:GratingStim",
# })

from psychopy.constants import STOPPED, FINISHED, PLAYING, NOT_STARTED

lazyImports = """
# stimuli derived from object or MinimalStim
from psychopy.visual.aperture import Aperture  # uses BaseShapeStim, ImageStim
from psychopy.visual.custommouse import CustomMouse
from psychopy.visual.elementarray import ElementArrayStim
from psychopy.visual.ratingscale import RatingScale
from psychopy.visual.slider import Slider
from psychopy.visual.progress import Progress
from psychopy.visual.simpleimage import SimpleImageStim

# stimuli derived from BaseVisualStim
from psychopy.visual.dot import DotStim
from psychopy.visual.grating import GratingStim
from psychopy.visual.secondorder import EnvelopeGrating
from psychopy.visual.movies import MovieStim
from psychopy.visual.movie2 import MovieStim2
from psychopy.visual.movie3 import MovieStim3
from psychopy.visual.vlcmoviestim import VlcMovieStim
from psychopy.visual.shape import BaseShapeStim

# stimuli derived from GratingStim
from psychopy.visual.bufferimage import BufferImageStim
from psychopy.visual.patch import PatchStim
from psychopy.visual.radial import RadialStim
from psychopy.visual.noise import NoiseStim

# stimuli derived from BaseShapeStim
from psychopy.visual.shape import ShapeStim

# stimuli derived from ShapeStim
from psychopy.visual.line import Line
from psychopy.visual.polygon import Polygon
from psychopy.visual.rect import Rect
from psychopy.visual.pie import Pie
from psychopy.visual.button import CheckBoxStim

# stimuli derived from Polygon
from psychopy.visual.circle import Circle

# stimuli derived from TextBox
from psychopy.visual.textbox import TextBox
from psychopy.visual.dropdown import DropDownCtrl

# rift support 
from psychopy.visual.rift import Rift

# VisualSystemHD support
from psychopy.visual.nnlvs import VisualSystemHD

# 3D stimuli support
from psychopy.visual.panorama import PanoramicImageStim
from psychopy.visual.stim3d import LightSource
from psychopy.visual.stim3d import SceneSkybox
from psychopy.visual.stim3d import BlinnPhongMaterial
from psychopy.visual.stim3d import RigidBodyPose
from psychopy.visual.stim3d import BoundingBox
from psychopy.visual.stim3d import SphereStim
from psychopy.visual.stim3d import BoxStim
from psychopy.visual.stim3d import PlaneStim
from psychopy.visual.stim3d import ObjMeshStim

"""
try:
    from psychopy.contrib.lazy_import import lazy_import
    lazy_import(globals(), lazyImports)
except Exception:
    exec(lazyImports)
