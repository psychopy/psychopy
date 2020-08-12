#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides class BaseVisualStim and mixins; subclass to get visual stimuli
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import object
from past.builtins import basestring
from pathlib import Path

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+

import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

try:
    from PIL import Image
except ImportError:
    from . import Image

import copy
import sys
import os
import re
from math import floor, fsum

from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import (attributeSetter, logAttrib,
                                           setAttribute)
from psychopy.tools.monitorunittools import (cm2pix, deg2pix, pix2cm,
                                             pix2deg, convertToPix)
from psychopy.visual.helpers import (pointInPolygon, polygonsOverlap,
                                     setColor, findImageFile)
from psychopy.tools.typetools import float_uint8
from psychopy.tools.arraytools import makeRadialMatrix
from . import globalVars

import numpy
from numpy import pi

from psychopy.constants import NOT_STARTED, STARTED, STOPPED

reportNImageResizes = 5  # permitted number of resizes

"""
There are several base and mix-in visual classes for multiple inheritance:
  - MinimalStim:       non-visual house-keeping code common to all visual stim
        RatingScale inherits only from MinimalStim.
  - WindowMixin:       attributes/methods about the stim relative to
        a visual.Window.
  - LegacyVisualMixin: deprecated visual methods (eg, setRGB) added
        to BaseVisualStim
  - ColorMixin:        for Stim that need color methods (most, not Movie)
        color-related methods and attribs
  - ContainerMixin:    for stim that need polygon .contains() methods.
        Most need this, but not Text. .contains(), .overlaps()
  - TextureMixin:      for texture methods namely _createTexture
        (Grating, not Text)
        seems to work; caveat: There were issues in earlier (non-MI) versions
        of using _createTexture so it was pulled out of classes.
        Now it's inside classes again. Should be watched.
  - BaseVisualStim:    = Minimal + Window + Legacy. Furthermore adds c
        ommon attributes like orientation, opacity, contrast etc.

Typically subclass BaseVisualStim to create new visual stim classes, and add
mixin(s) as needed to add functionality.
"""


class MinimalStim(object):
    """Non-visual methods and attributes for BaseVisualStim and RatingScale.

    Includes: name, autoDraw, autoLog, status, __str__
    """

    def __init__(self, name=None, autoLog=None):
        if name not in (None, ''):
            self.__dict__['name'] = name
        else:
            self.__dict__['name'] = 'unnamed %s' % self.__class__.__name__
        self.status = NOT_STARTED
        self.autoLog = autoLog
        super(MinimalStim, self).__init__()
        if self.autoLog:
            msg = ("%s is calling MinimalStim.__init__() with autolog=True. "
                   "Set autoLog to True only at the end of __init__())")
            logging.warning(msg % self.__class__.__name__)

    def __str__(self, complete=False):
        """
        """
        if hasattr(self, '_initParams'):
            className = self.__class__.__name__
            paramStrings = []
            for param in self._initParams:
                if hasattr(self, param):
                    val = getattr(self, param)
                    valStr = repr(getattr(self, param))
                    if len(repr(valStr)) > 50 and not complete:
                        if val.__class__.__name__ == 'attributeSetter':
                            _name = val.__getattribute__.__class__.__name__
                        else:
                            _name = val.__class__.__name__
                        valStr = "%s(...)" % _name
                else:
                    valStr = 'UNKNOWN'
                paramStrings.append("%s=%s" % (param, valStr))
            # this could be used if all params are known to exist:
            # paramStrings = ["%s=%s" %(param, getattr(self, param))
            #     for param in self._initParams]
            params = ", ".join(paramStrings)
            s = "%s(%s)" % (className, params)
        else:
            s = object.__repr__(self)
        return s

    # Might seem simple at first, but this ensures that "name" attribute
    # appears in docs and that name setting and updating is logged.
    @attributeSetter
    def name(self, value):
        """String or None. The name of the object to be using during
        logged messages about this stim. If you have multiple stimuli
        in your experiment this really helps to make sense of log files!

        If name = None your stimulus will be called "unnamed <type>", e.g.
        visual.TextStim(win) will be called "unnamed TextStim" in the logs.
        """
        self.__dict__['name'] = value

    @attributeSetter
    def autoDraw(self, value):
        """Determines whether the stimulus should be automatically drawn
        on every frame flip.

        Value should be: `True` or `False`. You do NOT need to set this
        on every frame flip!
        """
        self.__dict__['autoDraw'] = value
        toDraw = self.win._toDraw
        toDrawDepths = self.win._toDrawDepths
        beingDrawn = (self in toDraw)
        if value == beingDrawn:
            return  # nothing to do
        elif value:
            # work out where to insert the object in the autodraw list
            depthArray = numpy.array(toDrawDepths)
            # all indices where true:
            iis = numpy.where(depthArray < self.depth)[0]
            if len(iis):  # we featured somewhere before the end of the list
                toDraw.insert(iis[0], self)
                toDrawDepths.insert(iis[0], self.depth)
            else:
                toDraw.append(self)
                toDrawDepths.append(self.depth)
            self.status = STARTED
        elif value == False:
            # remove from autodraw lists
            toDrawDepths.pop(toDraw.index(self))  # remove from depths
            toDraw.remove(self)  # remove from draw list
            self.status = STOPPED

    def setAutoDraw(self, value, log=None):
        """Sets autoDraw. Usually you can use 'stim.attribute = value'
        syntax instead, but use this method to suppress the log message.
        """
        setAttribute(self, 'autoDraw', value, log)

    @attributeSetter
    def autoLog(self, value):
        """Whether every change in this stimulus should be auto logged.

        Value should be: `True` or `False`. Set to `False` if your
        stimulus is updating frequently (e.g. updating its position every
         frame) and you want to avoid swamping the log file with
        messages that aren't likely to be useful.
        """
        self.__dict__['autoLog'] = value

    def setAutoLog(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'autoLog', value, log)


class LegacyVisualMixin(object):
    """Class to hold deprecated visual methods and attributes.

    Intended only for use as a mixin class for BaseVisualStim, to maintain
    backwards compatibility while reducing clutter in class BaseVisualStim.
    """
    # def __init__(self):
    #    super(LegacyVisualMixin, self).__init__()

    def _calcSizeRendered(self):
        """DEPRECATED in 1.80.00. This functionality is now handled
        by _updateVertices() and verticesPix
        """
        # raise DeprecationWarning, "_calcSizeRendered() was deprecated in
        # 1.80.00. This functionality is now handled by _updateVertices()
        # and verticesPix"
        if self.units in ['norm', 'pix', 'height']:
            self._sizeRendered = copy.copy(self.size)
        elif self.units in ['deg', 'degs']:
            self._sizeRendered = deg2pix(self.size, self.win.monitor)
        elif self.units == 'cm':
            self._sizeRendered = cm2pix(self.size, self.win.monitor)
        else:
            logging.error("Stimulus units should be 'height', 'norm', "
                          "'deg', 'cm' or 'pix', not '%s'" % self.units)

    def _calcPosRendered(self):
        """DEPRECATED in 1.80.00. This functionality is now handled
        by _updateVertices() and verticesPix.
        """
        # raise DeprecationWarning, "_calcSizeRendered() was deprecated
        #  in 1.80.00. This functionality is now handled by
        # _updateVertices() and verticesPix"
        if self.units in ['norm', 'pix', 'height']:
            self._posRendered = copy.copy(self.pos)
        elif self.units in ['deg', 'degs']:
            self._posRendered = deg2pix(self.pos, self.win.monitor)
        elif self.units == 'cm':
            self._posRendered = cm2pix(self.pos, self.win.monitor)

    def _getPolyAsRendered(self):
        """DEPRECATED. Return a list of vertices as rendered.
        """
        oriRadians = numpy.radians(self.ori)
        sinOri = numpy.sin(-oriRadians)
        cosOri = numpy.cos(-oriRadians)
        x = (self._verticesRendered[:, 0] * cosOri -
             self._verticesRendered[:, 1] * sinOri)
        y = (self._verticesRendered[:, 0] * sinOri +
             self._verticesRendered[:, 1] * cosOri)
        return numpy.column_stack((x, y)) + self._posRendered

    def setDKL(self, newDKL, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self._set('dkl', val=newDKL, op=operation)
        self.setRGB(dkl2rgb(self.dkl, self.win.dkl_rgb))

    def setLMS(self, newLMS, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self._set('lms', value=newLMS, op=operation)
        self.setRGB(lms2rgb(self.lms, self.win.lms_rgb))

    def setRGB(self, newRGB, operation='', log=None):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        from psychopy.visual.helpers import setTexIfNoShaders
        self._set('rgb', newRGB, operation)
        setTexIfNoShaders(self)
        if self.__class__.__name__ == 'TextStim' and not self.useShaders:
            self._needSetText = True

    @attributeSetter
    def depth(self, value):
        """DEPRECATED. Depth is now controlled simply by drawing order.
        """
        self.__dict__['depth'] = value

# Dict of examples of Psychopy Red at 12% opacity in different formats
color_examples = {
    'invis': None,
    'named': 'crimson',
    'hex': '#F2545B',
    'hexa': '#F2545B1E',
    'rgb': (0.89, -0.35, -0.28),
    'rgba': (0.89, -0.35, -0.28, -0.76),
    'rgb1': (0.95, 0.32, 0.36),
    'rgba1': (0.95, 0.32, 0.36, 0.12),
    'rgb255': (242, 84, 91),
    'rgba255': (357, 65, 95, 30),
    'hsv': (357, 65, 95),
    'hsva': (357, 65, 95, 12),
}
# Dict of named colours
color_names = {
        "aliceblue": (0.882352941176471, 0.945098039215686, 1, 1.0),
        "antiquewhite": (0.96078431372549, 0.843137254901961, 0.686274509803922, 1.0),
        "aqua": (-1, 1, 1, 1.0),
        "aquamarine": (-0.00392156862745097, 1, 0.662745098039216, 1.0),
        "azure": (0.882352941176471, 1, 1, 1.0),
        "beige": (0.92156862745098, 0.92156862745098, 0.725490196078431, 1.0),
        "bisque": (1, 0.788235294117647, 0.537254901960784, 1.0),
        "black": (-1, -1, -1, 1.0),
        "blanchedalmond": (1, 0.843137254901961, 0.607843137254902, 1.0),
        "blue": (-1, -1, 1, 1.0),
        "blueviolet": (0.0823529411764705, -0.662745098039216, 0.772549019607843, 1.0),
        "brown": (0.294117647058824, -0.670588235294118, -0.670588235294118, 1.0),
        "burlywood": (0.741176470588235, 0.443137254901961, 0.0588235294117647, 1.0),
        "cadetblue": (-0.254901960784314, 0.23921568627451, 0.254901960784314, 1.0),
        "chartreuse": (-0.00392156862745097, 1, -1, 1.0),
        "chocolate": (0.647058823529412, -0.176470588235294, -0.764705882352941, 1.0),
        "coral": (1, -0.00392156862745097, -0.372549019607843, 1.0),
        "cornflowerblue": (-0.215686274509804, 0.168627450980392, 0.858823529411765, 1.0),
        "cornsilk": (1, 0.945098039215686, 0.725490196078431, 1.0),
        "crimson": (0.725490196078431, -0.843137254901961, -0.529411764705882, 1.0),
        "cyan": (-1, 1, 1, 1.0),
        "darkblue": (-1, -1, 0.0901960784313725, 1.0),
        "darkcyan": (-1, 0.0901960784313725, 0.0901960784313725, 1.0),
        "darkgoldenrod": (0.443137254901961, 0.0509803921568628, -0.913725490196078, 1.0),
        "darkgray": (0.325490196078431, 0.325490196078431, 0.325490196078431, 1.0),
        "darkgreen": (-1, -0.215686274509804, -1, 1.0),
        "darkgrey": (0.325490196078431, 0.325490196078431, 0.325490196078431, 1.0),
        "darkkhaki": (0.482352941176471, 0.435294117647059, -0.16078431372549, 1.0),
        "darkmagenta": (0.0901960784313725, -1, 0.0901960784313725, 1.0),
        "darkolivegreen": (-0.333333333333333, -0.16078431372549, -0.631372549019608, 1.0),
        "darkorange": (1, 0.0980392156862746, -1, 1.0),
        "darkorchid": (0.2, -0.607843137254902, 0.6, 1.0),
        "darkred": (0.0901960784313725, -1, -1, 1.0),
        "darksalmon": (0.827450980392157, 0.176470588235294, -0.0431372549019607, 1.0),
        "darkseagreen": (0.12156862745098, 0.474509803921569, 0.12156862745098, 1.0),
        "darkslateblue": (-0.435294117647059, -0.52156862745098, 0.0901960784313725, 1.0),
        "darkslategray": (-0.631372549019608, -0.380392156862745, -0.380392156862745, 1.0),
        "darkslategrey": (-0.631372549019608, -0.380392156862745, -0.380392156862745, 1.0),
        "darkturquoise": (-1, 0.615686274509804, 0.63921568627451, 1.0),
        "darkviolet": (0.16078431372549, -1, 0.654901960784314, 1.0),
        "deeppink": (1, -0.843137254901961, 0.152941176470588, 1.0),
        "deepskyblue": (-1, 0.498039215686275, 1, 1.0),
        "dimgray": (-0.176470588235294, -0.176470588235294, -0.176470588235294, 1.0),
        "dimgrey": (-0.176470588235294, -0.176470588235294, -0.176470588235294, 1.0),
        "dodgerblue": (-0.764705882352941, 0.129411764705882, 1, 1.0),
        "firebrick": (0.396078431372549, -0.733333333333333, -0.733333333333333, 1.0),
        "floralwhite": (1, 0.96078431372549, 0.882352941176471, 1.0),
        "forestgreen": (-0.733333333333333, 0.0901960784313725, -0.733333333333333, 1.0),
        "fuchsia": (1, -1, 1, 1.0),
        "gainsboro": (0.725490196078431, 0.725490196078431, 0.725490196078431, 1.0),
        "ghostwhite": (0.945098039215686, 0.945098039215686, 1, 1.0),
        "gold": (1, 0.686274509803922, -1, 1.0),
        "goldenrod": (0.709803921568627, 0.294117647058824, -0.749019607843137, 1.0),
        "gray": (0.00392156862745097, 0.00392156862745097, 0.00392156862745097, 1.0),
        "grey": (0.00392156862745097, 0.00392156862745097, 0.00392156862745097, 1.0),
        "green": (-1, 0.00392156862745097, -1, 1.0),
        "greenyellow": (0.356862745098039, 1, -0.631372549019608, 1.0),
        "honeydew": (0.882352941176471, 1, 0.882352941176471, 1.0),
        "hotpink": (1, -0.176470588235294, 0.411764705882353, 1.0),
        "indianred": (0.607843137254902, -0.27843137254902, -0.27843137254902, 1.0),
        "indigo": (-0.411764705882353, -1, 0.0196078431372548, 1.0),
        "ivory": (1, 1, 0.882352941176471, 1.0),
        "khaki": (0.882352941176471, 0.803921568627451, 0.0980392156862746, 1.0),
        "lavender": (0.803921568627451, 0.803921568627451, 0.96078431372549, 1.0),
        "lavenderblush": (1, 0.882352941176471, 0.92156862745098, 1.0),
        "lawngreen": (-0.0274509803921569, 0.976470588235294, -1, 1.0),
        "lemonchiffon": (1, 0.96078431372549, 0.607843137254902, 1.0),
        "lightblue": (0.356862745098039, 0.694117647058824, 0.803921568627451, 1.0),
        "lightcoral": (0.882352941176471, 0.00392156862745097, 0.00392156862745097, 1.0),
        "lightcyan": (0.756862745098039, 1, 1, 1.0),
        "lightgoldenrodyellow": (0.96078431372549, 0.96078431372549, 0.647058823529412, 1.0),
        "lightgray": (0.654901960784314, 0.654901960784314, 0.654901960784314, 1.0),
        "lightgreen": (0.129411764705882, 0.866666666666667, 0.129411764705882, 1.0),
        "lightgrey": (0.654901960784314, 0.654901960784314, 0.654901960784314, 1.0),
        "lightpink": (1, 0.427450980392157, 0.513725490196078, 1.0),
        "lightsalmon": (1, 0.254901960784314, -0.0431372549019607, 1.0),
        "lightseagreen": (-0.749019607843137, 0.396078431372549, 0.333333333333333, 1.0),
        "lightskyblue": (0.0588235294117647, 0.615686274509804, 0.96078431372549, 1.0),
        "lightslategray": (-0.0666666666666667, 0.0666666666666667, 0.2, 1.0),
        "lightslategrey": (-0.0666666666666667, 0.0666666666666667, 0.2, 1.0),
        "lightsteelblue": (0.380392156862745, 0.537254901960784, 0.741176470588235, 1.0),
        "lightyellow": (1, 1, 0.756862745098039, 1.0),
        "lime": (-1, 1, -1, 1.0),
        "limegreen": (-0.607843137254902, 0.607843137254902, -0.607843137254902, 1.0),
        "linen": (0.96078431372549, 0.882352941176471, 0.803921568627451, 1.0),
        "magenta": (1, -1, 1, 1.0),
        "maroon": (0.00392156862745097, -1, -1, 1.0),
        "mediumaquamarine": (-0.2, 0.607843137254902, 0.333333333333333, 1.0),
        "mediumblue": (-1, -1, 0.607843137254902, 1.0),
        "mediumorchid": (0.458823529411765, -0.333333333333333, 0.654901960784314, 1.0),
        "mediumpurple": (0.152941176470588, -0.12156862745098, 0.717647058823529, 1.0),
        "mediumseagreen": (-0.529411764705882, 0.403921568627451, -0.113725490196078, 1.0),
        "mediumslateblue": (-0.0352941176470588, -0.184313725490196, 0.866666666666667, 1.0),
        "mediumspringgreen": (-1, 0.96078431372549, 0.207843137254902, 1.0),
        "mediumturquoise": (-0.435294117647059, 0.63921568627451, 0.6, 1.0),
        "mediumvioletred": (0.56078431372549, -0.835294117647059, 0.0431372549019609, 1.0),
        "midnightblue": (-0.803921568627451, -0.803921568627451, -0.12156862745098, 1.0),
        "mintcream": (0.92156862745098, 1, 0.96078431372549, 1.0),
        "mistyrose": (1, 0.788235294117647, 0.764705882352941, 1.0),
        "moccasin": (1, 0.788235294117647, 0.419607843137255, 1.0),
        "navajowhite": (1, 0.741176470588235, 0.356862745098039, 1.0),
        "navy": (-1, -1, 0.00392156862745097, 1.0),
        "oldlace": (0.984313725490196, 0.92156862745098, 0.803921568627451, 1.0),
        "olive": (0.00392156862745097, 0.00392156862745097, -1, 1.0),
        "olivedrab": (-0.16078431372549, 0.113725490196078, -0.725490196078431, 1.0),
        "orange": (1, 0.294117647058824, -1, 1.0),
        "orangered": (1, -0.458823529411765, -1, 1.0),
        "orchid": (0.709803921568627, -0.12156862745098, 0.67843137254902, 1.0),
        "palegoldenrod": (0.866666666666667, 0.819607843137255, 0.333333333333333, 1.0),
        "palegreen": (0.192156862745098, 0.968627450980392, 0.192156862745098, 1.0),
        "paleturquoise": (0.372549019607843, 0.866666666666667, 0.866666666666667, 1.0),
        "palevioletred": (0.717647058823529, -0.12156862745098, 0.152941176470588, 1.0),
        "papayawhip": (1, 0.874509803921569, 0.670588235294118, 1.0),
        "peachpuff": (1, 0.709803921568627, 0.450980392156863, 1.0),
        "peru": (0.607843137254902, 0.0431372549019609, -0.505882352941176, 1.0),
        "pink": (1, 0.505882352941176, 0.592156862745098, 1.0),
        "plum": (0.733333333333333, 0.254901960784314, 0.733333333333333, 1.0),
        "powderblue": (0.380392156862745, 0.756862745098039, 0.803921568627451, 1.0),
        "purple": (0.00392156862745097, -1, 0.00392156862745097, 1.0),
        "red": (1, -1, -1, 1.0),
        "rosybrown": (0.474509803921569, 0.12156862745098, 0.12156862745098, 1.0),
        "royalblue": (-0.490196078431373, -0.176470588235294, 0.764705882352941, 1.0),
        "saddlebrown": (0.0901960784313725, -0.458823529411765, -0.850980392156863, 1.0),
        "salmon": (0.96078431372549, 0.00392156862745097, -0.105882352941176, 1.0),
        "sandybrown": (0.913725490196079, 0.286274509803922, -0.247058823529412, 1.0),
        "seagreen": (-0.63921568627451, 0.0901960784313725, -0.317647058823529, 1.0),
        "seashell": (1, 0.92156862745098, 0.866666666666667, 1.0),
        "sienna": (0.254901960784314, -0.356862745098039, -0.647058823529412, 1.0),
        "silver": (0.505882352941176, 0.505882352941176, 0.505882352941176, 1.0),
        "skyblue": (0.0588235294117647, 0.615686274509804, 0.843137254901961, 1.0),
        "slateblue": (-0.168627450980392, -0.294117647058823, 0.607843137254902, 1.0),
        "slategray": (-0.12156862745098, 0.00392156862745097, 0.129411764705882, 1.0),
        "slategrey": (-0.12156862745098, 0.00392156862745097, 0.129411764705882, 1.0),
        "snow": (1, 0.96078431372549, 0.96078431372549, 1.0),
        "springgreen": (-1, 1, -0.00392156862745097, 1.0),
        "steelblue": (-0.450980392156863, 0.0196078431372548, 0.411764705882353, 1.0),
        "tan": (0.647058823529412, 0.411764705882353, 0.0980392156862746, 1.0),
        "teal": (-1, 0.00392156862745097, 0.00392156862745097, 1.0),
        "thistle": (0.694117647058824, 0.498039215686275, 0.694117647058824, 1.0),
        "tomato": (1, -0.223529411764706, -0.443137254901961, 1.0),
        "turquoise": (-0.498039215686275, 0.756862745098039, 0.631372549019608, 1.0),
        "violet": (0.866666666666667, 0.0196078431372548, 0.866666666666667, 1.0),
        "wheat": (0.92156862745098, 0.741176470588235, 0.403921568627451, 1.0),
        "white": (1, 1, 1, 1.0),
        "whitesmoke": (0.92156862745098, 0.92156862745098, 0.92156862745098, 1.0),
        "yellow": (1, 1, -1, 1.0),
        "yellowgreen": (0.207843137254902, 0.607843137254902, -0.607843137254902, 1.0)
    }
# Shorthand for common regexpressions
_255 = '(\d|\d\d|1\d\d|2[0-4]\d|25[0-5])'
_360 = '(\d|\d\d|[12]\d\d|3[0-5]\d|360)'
_100 = '(\d|\d\d|100)'
_1 = '(0|1|1.0*|0\.\d*)'
_lbr = '[\[\(]\s*'
_rbr = '\s*[\]\)]'
# Dict of regexpressions for different formats
color_spaces = {
    'invis': re.compile('None'), # Fully transparent
    'named': re.compile("|".join(list(color_names))), # A named colour space
    'hex': re.compile('#[\dabcdefABCDEF]{6}'), # Hex
    'hexa': re.compile('#[\dabcdefABCDEF]{8}'), # Hex + alpha
    'rgb': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+_rbr), # RGB from -1 to 1
    'rgba': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+_rbr),  # RGB + alpha from -1 to 1
    'rgb1': re.compile(_lbr+_1+',\s*'+_1+',\s*'+_1+_rbr),  # RGB from 0 to 1
    'rgba1': re.compile(_lbr+_1+',\s*'+_1+',\s*'+_1+',\s*'+_1+_rbr),  # RGB + alpha from 0 to 1
    'rgb255': re.compile(_lbr+_255+',\s*'+_255+',\s*'+_255+_rbr), # RGB from 0 to 255
    'rgba255': re.compile(_lbr+_255+',\s*'+_255+',\s*'+_255+',\s*'+_255+_rbr), # RGB + alpha from 0 to 255
    'hsv': re.compile(_lbr+_360+'\°?'+',\s*'+_1+',\s*'+_1+_rbr), # HSV with hue from 0 to 260 and saturation/vibrancy from 0 to 100
    'hsva': re.compile(_lbr+_360+'\°?'+',\s*'+_1+',\s*'+_1+',\s*'+_1+_rbr), # HSV with hue from 0 to 260 and saturation/vibrancy from 0 to 100 + alpha from 0 to 100
    'lms': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+_rbr), # LMS from -1 to 1
    'lmsa': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+_rbr), # LMS + alpha from -1 to 1
}


class Color(object):
    """A class to store colour details, knows what colour space it's in and can supply colours in any space"""

    def __init__(self, color=None, space=None, conematrix=None):
        # If input is a Color object, duplicate all settings
        if isinstance(color, Color):
            self._requested = color._requested
            self._requestedSpace = color._requestedSpace
            self.conematrix = color.conematrix
            self.rgba = color.rgba
            return
        # Store requested colour and space (or defaults, if none given)
        self._requested = color if color else None
        self._requestedSpace = space if space else self.getSpace(self._requested)

        # Set matrix for cone conversion
        if conematrix is not None:
            self.conematrix = conematrix
        else:
            # Set _conematrix specifically as undefined, rather than just setting to default
            self._conematrix = None

        # Convert to lingua franca
        if self._requestedSpace:
            setattr(self, self._requestedSpace, self._requested)
        else:
            self.rgba = None

    def __repr__(self):
        """If colour is printed, it will display its class and value"""
        if self.named:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + self.named + ">"
        elif self.rgba:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + str(tuple(round(c,2) for c in self.rgba)) + ">"
        else:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + "Invalid" + ">"

    # ---rich comparisons---
    def __eq__(self, target):
        """== will compare RGBA values, rounded to 2dp"""
        if isinstance(target, Color):
            return (round(c,2) for c in self.rgba) == (round(c,2) for c in target.rgba)
        else:
            return False
    def __ne__(self, target):
        """!= will return the opposite of =="""
        return not self == target
    def __lt__(self, target):
        """< will compare brightness"""
        if isinstance(target, Color):
            return self.brightness < target.brightness
        else:
            return False
    def __le__(self, target):
        """<= will compare brightness"""
        if isinstance(target, Color):
            return self.brightness <= target.brightness
        else:
            return False
    def __gt__(self, target):
        """> will compare brightness"""
        if isinstance(target, Color):
            return self.brightness > target.brightness
        else:
            return False
    def __ge__(self, target):
        """>= will compare brightness"""
        if isinstance(target, Color):
            return self.brightness >= target.brightness
        else:
            return False

    def copy(self):
        """Return a duplicate of this colour"""
        return self.__class__(self._requested, self._requestedSpace, self.conematrix)

    @staticmethod
    def getSpace(color, debug=False):
        """Find what colour space a colour is from"""
        if isinstance(color, Color):
            return color._requestedSpace
        possible = [space for space in color_spaces
                    if color_spaces[space].fullmatch(str(color))]
        if len(possible) == 1:
            return possible[0]
        elif debug:
            return possible
        # Preferred values in cases of conflict
        priority = [
            'rgba',
            'rgb',
            'rgba255',
            'rgba255',
            'hexa'
        ]
        for space in priority:
            if space in possible:
                return space
        # If all else fails, return None
        return None

    @staticmethod
    def hue2rgb255(hue):
        # Work out what segment of the colour wheel we're in
        seg = floor(hue / 60)
        seg = seg if seg % 6 else 0
        # Define values for when a value is decreasing / increasing in a segment
        _up = (hue % 60) * (255 / 60)
        _down = 255 - _up
        _mov = _down if seg%2 else _up # Even segments are down, odd are up
        # Calculate rgb according to segment
        if seg == 0:
            return (255, _mov, 0,)
        if seg == 1:
            return (_mov, 255, 0,)
        if seg == 2:
            return (0, 255, _mov,)
        if seg == 3:
            return (0, _mov, 255,)
        if seg == 4:
            return (_mov, 0, 255,)
        if seg == 5:
            return (255, 0, _mov,)

    def set(self, color=None, space=None, conematrix=None):
        """Set the colour of this object - essentially the same as what happens on creation, but without
        having to initialise a new object"""
        # If input is a Color object, duplicate all settings
        if isinstance(color, Color):
            self._requested = color._requested
            self._requestedSpace = color._requestedSpace
            self.conematrix = color.conematrix
            self.rgba = color.rgba
            return
        # Store requested colour and space (or defaults, if none given)
        self._requested = color if color else None
        self._requestedSpace = space if space else self.getSpace(self._requested)

        # Set matrix for cone conversion
        if conematrix:
            self.conematrix = conematrix
        else:
            # Set _conematrix specifically as undefined, rather than just setting to default
            self._conematrix = None

        # Convert to lingua franca
        if self._requestedSpace:
            setattr(self, self._requestedSpace, self._requested)
        else:
            self.rgba = None
    # ---adjusters---
    @property
    def contrast(self):
        '''Distance from mid grey in rgb (-1 to 1)'''
        return sum(self.rgb)/3
    @contrast.setter
    def contrast(self, value):
        norm = tuple(c/self.contrast for c in self.rgb)
        self.rgba = tuple(max(min(c*value,1),-1) for c in norm) + (self.alpha,)

    @property
    def saturation(self):
        '''Saturation in hsv (0 to 1)'''
        return self.hsv[1]
    @contrast.setter
    def saturation(self, value):
        h,s,v,a = self.hsva
        s += value
        s = min(s, 1)
        s = max(s, 0)
        self.hsva = (h, s, v, a)

    @property
    def brightness(self):
        return sum(self.rgb1)/3
    @brightness.setter
    def brightness(self, value):
        adj = value-self.brightness
        self.rgba1 = tuple(
            max(min(c+adj, 1),0)
            for c in self.rgb1
        ) + (self.alpha,)

    @property
    def alpha(self):
        return self.rgba[-1]
    @alpha.setter
    def alpha(self, value):
        value = min(value,1)
        value = max(value,0)
        self.rgba = self.rgb + (value,)

    #---spaces---
    # Lingua franca is rgba
    @property
    def rgba(self):
        if hasattr(self, '_franca'):
            return self._franca
    @rgba.setter
    def rgba(self, color):
        # Validate
        if not Color.getSpace(color) in ['rgba', 'rgb']:
            self._franca = None
            return
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        if isinstance(color, list):
            color = tuple(color)
        # Append alpha, if not present
        if len(color) == 4:
            self._franca = color
        elif len(color) == 3:
            self._franca = color + (1,)
        else:
            self._franca = None

    @property
    def rgb(self):
        if self.rgba:
            return self.rgba[:-1]
    @rgb.setter
    def rgb(self, color):
        self.rgba = color

    @property
    def rgba255(self):
        # Iterate through values and do conversion
        if self.rgba:
            return tuple(int(255*(val+1)/2) for val in self.rgba)
    @rgba255.setter
    def rgba255(self, color):
        # Validate
        if not Color.getSpace(color) in ['rgb255', 'rgba255']:
            self.rgba = None
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        # Iterate through values and do conversion
        self.rgba = tuple(2 * (val / 255 - 0.5) for val in color)

    @property
    def rgb255(self):
        if self.rgba255:
            return self.rgba255[:-1]
    @rgb255.setter
    def rgb255(self, color):
        self.rgba255 = color

    @property
    def rgba1(self):
        # Iterate through values and do conversion
        if self.rgba:
            return tuple((val + 1) / 2 for val in self.rgba)
    @rgba1.setter
    def rgba1(self, color):
        # Validate
        if not Color.getSpace(color) in ['rgb', 'rgba', 'rgb1', 'rgba1']:
            return None
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        # Iterate through values and do conversion
        self.rgba = tuple(2 * (val - 0.5) for val in color)

    @property
    def rgb1(self):
        if self.rgba1:
            return self.rgba1[:-1]
    @rgb1.setter
    def rgb1(self, color):
        self.rgba1 = tuple(2 * (val - 0.5) for val in color)

    @property
    def hexa(self):
        if not self.rgba255:
            return None
        # Map rgb255 values to corresponding letters in hex
        hexmap = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
        # Iterate and do conversion
        flatList = ['#']
        for val in self.rgba255:
            dig1 = int(floor(val / 16))
            flatList.append(
                str(dig1) if dig1 <= 9 else hexmap[dig1]
            )
            dig2 = int(val % 16)
            flatList.append(
                str(dig2) if dig2 <= 9 else hexmap[dig2]
            )
        return "".join(flatList)
    @hexa.setter
    def hexa(self, color):
        # Convert strings to list
        if Color.getSpace(color) in ['hexa']:
            colorList = [color[i - 2:i] for i in [3, 5, 7, 9]]
        elif Color.getSpace(color) in ['hex']:
            colorList = [color[i-2:i] for i in [3,5,7]]
        else:
            # Validate
            self.rgba = None
            return
        # Map hex letters to corresponding values in rgb255
        hexmap = {'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}
        # Create adjustment for different digits
        adj = {0:16, 1:1}
        flatList = []
        for val in colorList:
            # Iterate through individual values
            flat = 0
            for i, v in enumerate(val):
                if re.match('\d', str(v)):
                    flat += int(v)*adj[i]
                elif re.match('[abcdef]', str(v).lower()):
                    flat += hexmap[str(v).lower()]*adj[i]
            flatList.append(flat)
        self.rgba255 = flatList

    @property
    def hex(self):
        if self.hexa:
            return self.hexa[:-2]
    @hex.setter
    def hex(self, color):
        self.hexa = color

    @property
    def invis(self):
        return None
    @invis.setter
    def invis(self, color):
        # Invisible is always the same value
        self.rgba = (0, 0, 0, -1)

    @property
    def named(self):
        # Round all values to 2 decimal places to find approximate matches
        approxNames = {col: [round(val, 2) for val in color_names[col]]
                       for col in color_names}
        approxColor = [round(val, 2) for val in self.rgba]
        # Get matches
        possible = [nm for nm in approxNames if approxNames[nm] == approxColor]
        # Return the first match
        if possible:
            return possible[0]
    @named.setter
    def named(self, color):
        # Validate
        if str(color).lower() not in color_names:
            self.rgba = None
        else:
            # Retrieve named colour
            self.rgba = color_names[str(color).lower()]

    @property
    def hsva(self):
        # Based on https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
        red, green, blue, alpha = self.rgba1
        cmax = max(red, green, blue)
        cmin = min(red, green, blue)
        delta = cmax - cmin
        # Calculate hue
        if cmax == 0 and cmin == 0:
            return (0, 0, 0, alpha)
        elif delta == 0:
            return (0, 0, sum(self.rgb1)/3, alpha)

        if cmax == red:
            hue = (60 * ((green - blue) / delta) + 360) % 360
        elif cmax == green:
            hue = (60 * ((blue - red) / delta) + 120) % 360
        elif cmax == blue:
            hue = (60 * ((red - green) / delta) + 240) % 360
        # Calculate saturation
        if cmax == 0:
            saturation = 0
        else:
            saturation = (delta / cmax)
        # Calculate vibrancy
        vibrancy = cmax
        return (hue, saturation, vibrancy, alpha)
    @hsva.setter
    def hsva(self, color):
        # based on method in
        # http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB

        # Validate
        if 'hsv' not in Color.getSpace(color, debug=True) and 'hsva' not in Color.getSpace(color, debug=True):
            return None
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        if isinstance(color, list):
            color = tuple(color)
        # Extract values
        if len(color) == 3:
            hue, saturation, vibrancy = color
            alpha255 = None
        if len(color) == 4:
            hue, saturation, vibrancy, alpha = color
            alpha255 = alpha*255
        # Convert hue
        hue255 = Color.hue2rgb255(hue)
        # Get value to move towards as saturation decreases
        vibrancy255 = vibrancy*255
        # Adjust by vibrancy and saturation
        all255 = tuple(h+(vibrancy255-h)*(saturation) for h in hue255)
        # Apply via rgba255
        self.rgba255 = all255 + (alpha255,) if alpha255 else all255 + (255,)
    @property
    def hsv(self):
        if self.hsva:
            return self.hsva[:-1]
    @hsv.setter
    def hsv(self, color):
        self.hsva = color

    @property
    def conematrix(self):
        if self._conematrix is None:
            # If _conematrix has been directly set to None, set to default
            self.conematrix = None
        return self._conematrix
    @conematrix.setter
    def conematrix(self, value):
        # Default matrix
        def default():
            # Set default cone matrix and print warning
            logging.warning('This monitor has not been color-calibrated. '
                            'Using default LMS conversion matrix.')
            return numpy.asarray([
                # L        M        S
                [4.97068857, -4.14354132, 0.17285275],  # R
                [-0.90913894, 2.15671326, -0.24757432],  # G
                [-0.03976551, -0.14253782, 1.18230333]])  # B
        if not isinstance(value, numpy.ndarray):
            self._conematrix = default()
        elif not value.size == 9:
            self._conematrix = default()
        else:
            self._conematrix = value

    @property
    def lmsa(self):
        """Convert from RGB to cone space (LMS).

        Requires a conversion matrix, which will be generated from generic
        Sony Trinitron phosphors if not supplied (note that you will not get
        an accurate representation of the color space unless you supply a
        conversion matrix)
        """
        if self._conematrix is None:
            self.conematrix = None
        # its easier to use in the other orientation!
        rgb_3xN = numpy.transpose(self.rgb)
        rgb_to_cones = numpy.linalg.inv(self.conematrix)
        lms = numpy.dot(rgb_to_cones, rgb_3xN)
        return tuple(numpy.transpose(lms))  # return in the shape we received it
    @lmsa.setter
    def lmsa(self, color):
        """Convert from cone space (Long, Medium, Short) to RGB.

        Requires a conversion matrix, which will be generated from generic
        Sony Trinitron phosphors if not supplied (note that you will not get
        an accurate representation of the color space unless you supply a
        conversion matrix)
        """
        # Validate
        if 'lms' not in Color.getSpace(color, debug=True) and 'lmsa' not in Color.getSpace(color, debug=True):
            return None
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        if isinstance(color, list):
            color = tuple(color)

        # Get alpha
        if len(color) == 4:
            alpha = color[-1]
            color = color[:-1]
        elif len(color) == 3:
            alpha = 1

        # its easier to use in the other orientation!
        lms_3xN = numpy.transpose(color)
        rgb = numpy.dot(self.conematrix, lms_3xN)
        self.rgba = tuple(numpy.transpose(rgb)) + (alpha,)  # return in the shape we received it

    @property
    def lms(self):
        if self.lmsa:
            return self.lmsa[:-1]
    @lms.setter
    def lms(self, color):
        self.lmsa = color

_rec = '(\-4\.5|\-4\.4\d*|\-4\.[0-4]\d*|\-[0-3]\.\d*|\-[0-3]|0|0\.\d*|1|1\.0)' # -4.5 to 1
advanced_spaces = {
    'rec709TF': re.compile(_lbr+_rec+',\s*'+_rec+',\s*'+_rec+_rbr), # rec709TF adjusted RGB from -4.5 to 1 + alpha from 0 to 1
    'rec709TFa': re.compile(_lbr+_rec+',\s*'+_rec+',\s*'+_rec+',\s*'+_1+_rbr), # rec709TF adjusted RGB from -4.5 to 1 + alpha from 0 to 1
    'srgbTF': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+_rbr), # srgbTF from -1 to 1 + alpha from 0 to 1
    'srgbTFa': re.compile(_lbr+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+'\-?'+_1+',\s*'+_1+_rbr), # srgbTF from -1 to 1 + alpha from 0 to 1
}


class AdvancedColor(Color):
    @staticmethod
    def getSpace(color, debug=False):
        """Overrides Color.getSpace, drawing from a much more comprehensive library of colour spaces"""
        if isinstance(color, AdvancedColor):
            return color._requestedSpace
        # Check for advanced colours spaces
        possible = [space for space in advanced_spaces
                    if advanced_spaces[space].fullmatch(str(color))]
        if len(possible) == 1:
            return possible[0]
        # Append basic colour spaces and check again
        basic = Color.getSpace(color, debug=True)
        if isinstance(basic, str):
            basic = [basic]
        possible += basic
        if possible and len(possible) == 1:
            return possible[0]
        # Return full list if in debug mode
        if debug:
            return possible
        # Preferred values in cases of conflict
        priority = [
            'rgba',
            'rgb',
            'rgba255',
            'rgba255',
            'hexa'
        ]
        for space in priority:
            if space in possible:
                return space

    @property
    def rec709TFa(self):
        """Apply the Rec. 709 transfer function (or gamma) to linear RGB values.

            This transfer function is defined in the ITU-R BT.709 (2015) recommendation
            document (http://www.itu.int/rec/R-REC-BT.709-6-201506-I/en) and is
            commonly used with HDTV televisions.
            """
        if self.rgb:
            return tuple(1.099 * c ** 0.45 - 0.099
                         if c >= 0.018
                         else 4.5 * c
                         for c in self.rgb) + (self.rgba1[-1],)
    @rec709TFa.setter
    def rec709TFa(self, color):
        # Validate
        if 'rec709TF' not in AdvancedColor.getSpace(color, debug=True) and 'rec709TFa' not in AdvancedColor.getSpace(color, debug=True):
            self._franca = None
            return
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        if isinstance(color, list):
            color = tuple(color)
        # Check for alpha
        if len(color) == 4:
            alpha = color[-1]
            color = color[:-1]
        elif len(color) == 3:
            alpha = 1
        # Do conversion
        self.rgba = tuple(((c + 0.099)/1.099)**(1/0.45)
                         if c >= 1.099 * 0.018 ** 0.45 - 0.099
                         else c / 4.5
                         for c in color) + (alpha,)

    @property
    def rec709TF(self):
        if self.rec709TFa:
            return self.rec709TFa[:-1]
    @rec709TF.setter
    def rec709TF(self, color):
        self.rec709TFa = color

    @property
    def srgbTFa(self):
        """Apply sRGB transfer function (or gamma) to linear RGB values."""
        # applies the sRGB transfer function (linear RGB -> sRGB)
        return tuple(c * 12.92
                     if c <= 0.0031308
                     else (1.0 + 0.055) * c ** (1.0 / 2.4) - 0.055
                     for c in self.rgb) + (self.rgba1[-1],)
    @srgbTFa.setter
    def srgbTFa(self, color):
        # Validate
        if 'srgbTF' not in AdvancedColor.getSpace(color, debug=True) and 'srgbTFa' not in AdvancedColor.getSpace(color, debug=True):
            self._franca = None
            return
        if isinstance(color, str):
            color = [float(n) for n in color.strip('[]()').split(',')]
        if isinstance(color, list):
            color = tuple(color)
        # Check for alpha
        if len(color) == 4:
            alpha = color[-1]
            color = color[:-1]
        elif len(color) == 3:
            alpha = 1
        # do the inverse (sRGB -> linear RGB)
        self.rgba = tuple(c / 12.92
                     if c <= 0.04045
                     else ((c + 0.055) / 1.055) ** 2.4
                     for c in color) + (alpha,)

    @property
    def srgbTF(self):
        if self.srgbTFa:
            return self.srgbTFa[:-1]
    @srgbTF.setter
    def srgbTF(self, color):
        self.srgbTFa = color


class ColorMixin(object):
    """Mixin class for visual stim that need color and or contrast.
    """
    # def __init__(self):
    #    super(ColorStim, self).__init__()

    @attributeSetter
    def color(self, value):
        """Color of the stimulus

        Value should be one of:
            + string: to specify a :ref:`colorNames`. Any of the standard
              html/X11 `color names
              <http://www.w3schools.com/html/html_colornames.asp>`
              can be used.
            + :ref:`hexColors`
            + numerically: (scalar or triplet) for DKL, RGB or
                other :ref:`colorspaces`. For
                these, :ref:`operations <attrib-operations>` are supported.

        When color is specified using numbers, it is interpreted with
        respect to the stimulus' current colorSpace. If color is given as a
        single value (scalar) then this will be applied to all 3 channels.

        Examples
        --------
        For whatever stim you have::

            stim.color = 'white'
            stim.color = 'RoyalBlue'  # (the case is actually ignored)
            stim.color = '#DDA0DD'  # DDA0DD is hexadecimal for plum
            stim.color = [1.0, -1.0, -1.0]  # if stim.colorSpace='rgb':
                            # a red color in rgb space
            stim.color = [0.0, 45.0, 1.0]  # if stim.colorSpace='dkl':
                            # DKL space with elev=0, azimuth=45
            stim.color = [0, 0, 255]  # if stim.colorSpace='rgb255':
                            # a blue stimulus using rgb255 space
            stim.color = 255  # interpreted as (255, 255, 255)
                              # which is white in rgb255.


        :ref:`Operations <attrib-operations>` work as normal for all numeric
        colorSpaces (e.g. 'rgb', 'hsv' and 'rgb255') but not for strings, like
        named and hex. For example, assuming that colorSpace='rgb'::

            stim.color += [1, 1, 1]  # increment all guns by 1 value
            stim.color *= -1  # multiply the color by -1 (which in this
                                # space inverts the contrast)
            stim.color *= [0.5, 0, 1]  # decrease red, remove green, keep blue

        You can use `setColor` if you want to set color and colorSpace in one
        line. These two are equivalent::

            stim.setColor((0, 128, 255), 'rgb255')
            # ... is equivalent to
            stim.colorSpace = 'rgb255'
            stim.color = (0, 128, 255)
        """
        self.setColor(
            value, log=False)  # logging already done by attributeSettter

    @attributeSetter
    def colorSpace(self, value):
        """The name of the color space currently being used

        Value should be: a string or None

        For strings and hex values this is not needed.
        If None the default colorSpace for the stimulus is
        used (defined during initialisation).

        Please note that changing colorSpace does not change stimulus
        parameters. Thus you usually want to specify colorSpace before
        setting the color. Example::

            # A light green text
            stim = visual.TextStim(win, 'Color me!',
                                   color=(0, 1, 0), colorSpace='rgb')

            # An almost-black text
            stim.colorSpace = 'rgb255'

            # Make it light green again
            stim.color = (128, 255, 128)
        """
        self.__dict__['colorSpace'] = value

    @attributeSetter
    def contrast(self, value):
        """A value that is simply multiplied by the color

        Value should be: a float between -1 (negative) and 1 (unchanged).
            :ref:`Operations <attrib-operations>` supported.

        Set the contrast of the stimulus, i.e. scales how far the stimulus
        deviates from the middle grey. You can also use the stimulus
        `opacity` to control contrast, but that cannot be negative.

        Examples::

            stim.contrast =  1.0  # unchanged contrast
            stim.contrast =  0.5  # decrease contrast
            stim.contrast =  0.0  # uniform, no contrast
            stim.contrast = -0.5  # slightly inverted
            stim.contrast = -1.0  # totally inverted

        Setting contrast outside range -1 to 1 is permitted, but may
        produce strange results if color values exceeds the monitor limits.::

            stim.contrast =  1.2  # increases contrast
            stim.contrast = -1.2  # inverts with increased contrast
        """
        self.__dict__['contrast'] = value

        # If we don't have shaders we need to rebuild the stimulus
        if hasattr(self, 'useShaders'):
            if not self.useShaders:
                # we'll need to update the textures for the stimulus
                # (sometime before drawing but not now)
                if self.__class__.__name__ == 'TextStim':
                    self.text = self.text  # call attributeSetter
                # GratingStim, RadialStim, ImageStim etc
                elif hasattr(self, '_needTextureUpdate'):
                    self._needTextureUpdate = True
                elif (hasattr(self, 'fillColor')  # a derivative of shapestim
                        or self.__class__.__name__ == 'DotStim'):
                    pass  # no need for shaders or rebuilding
                elif self.autoLog:
                    logging.warning('Tried to set contrast while useShaders '
                                    '= False but stimulus was not rebuilt. '
                                    'Contrast might remain unchanged. {}'
                                    .format(self))
        elif self.autoLog:
            logging.warning('Contrast was set on class where useShaders was '
                            'undefined. Contrast might remain unchanged')

    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        and/or set colorSpace simultaneously.
        """
        # NB: the setColor helper function! Not this function itself :-)
        setColor(self, color, colorSpace=colorSpace, operation=operation,
                 rgbAttrib='rgb',  # or 'fillRGB' etc
                 colorAttrib='color')
        if self.__class__.__name__ == 'TextStim' and not self.useShaders:
            self._needSetText = True
        logAttrib(self, log, 'color',
                  value='%s (%s)' % (self.color, self.colorSpace))

    def setContrast(self, newContrast, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'contrast', newContrast, log, operation)

    def _getDesiredRGB(self, rgb, colorSpace, contrast):
        """ Convert color to RGB while adding contrast.
        Requires self.rgb, self.colorSpace and self.contrast
        """
        # Ensure that we work on 0-centered color (to make negative contrast
        # values work)
        if colorSpace not in ['rgb', 'dkl', 'lms', 'hsv']:
            rgb = rgb / 127.5 - 1

        # Convert to RGB in range 0:1 and scaled for contrast
        # NB glColor will clamp it to be 0-1 (whether or not we use FBO)
        desiredRGB = (rgb * contrast + 1) / 2.0
        if not self.win.useFBO:
            # Check that boundaries are not exceeded. If we have an FBO that
            # can handle this
            if numpy.any(desiredRGB > 1.0) or numpy.any(desiredRGB < 0):
                msg = ('Desired color %s (in RGB 0->1 units) falls '
                       'outside the monitor gamut. Drawing blue instead')
                logging.warning(msg % desiredRGB)
                desiredRGB = [0.0, 0.0, 1.0]

        return desiredRGB


class ContainerMixin(object):
    """Mixin class for visual stim that have verticesPix attrib
    and .contains() methods.
    """

    def __init__(self):
        super(ContainerMixin, self).__init__()
        self._verticesBase = numpy.array(
            [[0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5]])  # sqr
        self._borderBase = numpy.array(
            [[0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5]])  # sqr
        self._rotationMatrix = [[1., 0.], [0., 1.]]  # no rotation by default

    @property
    def verticesPix(self):
        """This determines the coordinates of the vertices for the
        current stimulus in pixels, accounting for size, ori, pos and units
        """
        # because this is a property getter we can check /on-access/ if it
        # needs updating :-)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['verticesPix']

    @property
    def _borderPix(self):
        """Allows for a dynamic border that differs from self.vertices, gets
        updated dynamically with identical transformations.
        """
        if not hasattr(self, 'border'):
            msg = "%s._borderPix requested without .border" % self.name
            logging.error(msg)
            raise AttributeError(msg)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['_borderPix']

    def _updateVertices(self):
        """Sets Stim.verticesPix and ._borderPix from pos, size, ori,
        flipVert, flipHoriz
        """
        # check whether stimulus needs flipping in either direction
        flip = numpy.array([1, 1])
        if hasattr(self, 'flipHoriz') and self.flipHoriz:
            flip[0] = -1 # True=(-1), False->(+1)
        if hasattr(self, 'flipVert') and self.flipVert:
            flip[1] = -1 # True=(-1), False->(+1)

        if hasattr(self, '_tesselVertices'):  # Shapes need to render from this
            verts = self._tesselVertices
        elif hasattr(self, 'vertices'):
            verts = self.vertices
        else:
            verts = self._verticesBase

        # set size and orientation, combine with position and convert to pix:
        if hasattr(self, 'fieldSize'):
            # this is probably a DotStim and size is handled differently
            verts = numpy.dot(verts * flip, self._rotationMatrix)
        else:
            verts = numpy.dot(self.size * verts * flip, self._rotationMatrix)
        verts = convertToPix(vertices=verts, pos=self.pos,
                             win=self.win, units=self.units)
        self.__dict__['verticesPix'] = verts

        if hasattr(self, 'border'):
            #border = self.border
            border = numpy.dot(self.size * self.border *
                               flip, self._rotationMatrix)
            border = convertToPix(
                vertices=border, pos=self.pos, win=self.win, units=self.units)
            self.__dict__['_borderPix'] = border

        self._needVertexUpdate = False
        self._needUpdate = True  # but we presumably need to update the list

    def contains(self, x, y=None, units=None):
        """Returns True if a point x,y is inside the stimulus' border.

        Can accept variety of input options:
            + two separate args, x and y
            + one arg (list, tuple or array) containing two vals (x,y)
            + an object with a getPos() method that returns x,y, such
                as a :class:`~psychopy.event.Mouse`.

        Returns `True` if the point is within the area defined either by its
        `border` attribute (if one defined), or its `vertices` attribute if
        there is no .border. This method handles
        complex shapes, including concavities and self-crossings.

        Note that, if your stimulus uses a mask (such as a Gaussian) then
        this is not accounted for by the `contains` method; the extent of the
        stimulus is determined purely by the size, position (pos), and
        orientation (ori) settings (and by the vertices for shape stimuli).

        See Coder demos: shapeContains.py
        See Coder demos: shapeContains.py
        """
        # get the object in pixels
        if hasattr(x, 'border'):
            xy = x._borderPix  # access only once - this is a property
            units = 'pix'  # we can forget about the units
        elif hasattr(x, 'verticesPix'):
            # access only once - this is a property (slower to access)
            xy = x.verticesPix
            units = 'pix'  # we can forget about the units
        elif hasattr(x, 'getPos'):
            xy = x.getPos()
            units = x.units
        elif type(x) in [list, tuple, numpy.ndarray]:
            xy = numpy.array(x)
        else:
            xy = numpy.array((x, y))
        # try to work out what units x,y has
        if units is None:
            if hasattr(xy, 'units'):
                units = xy.units
            else:
                units = self.units
        if units != 'pix':
            xy = convertToPix(xy, pos=(0, 0), units=units, win=self.win)
        # ourself in pixels
        if hasattr(self, 'border'):
            poly = self._borderPix  # e.g., outline vertices
        elif hasattr(self, 'boundingBox'):
            if abs(self.ori) > 0.1:
                raise RuntimeError("TextStim.contains() doesn't currently "
                                   "support rotated text.")
            w, h = self.boundingBox  # e.g., outline vertices
            x, y = self.posPix
            poly = numpy.array([[x+w/2, y-h/2], [x-w/2, y-h/2],
                                [x-w/2, y+h/2], [x+w/2, y+h/2]])
        else:
            poly = self.verticesPix  # e.g., tessellated vertices

        return pointInPolygon(xy[0], xy[1], poly=poly)

    def overlaps(self, polygon):
        """Returns `True` if this stimulus intersects another one.

        If `polygon` is another stimulus instance, then the vertices
        and location of that stimulus will be used as the polygon.
        Overlap detection is typically very good, but it
        can fail with very pointy shapes in a crossed-swords configuration.

        Note that, if your stimulus uses a mask (such as a Gaussian blob)
        then this is not accounted for by the `overlaps` method; the extent
        of the stimulus is determined purely by the size, pos, and
        orientation settings (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        return polygonsOverlap(self, polygon)


class TextureMixin(object):
    """Mixin class for visual stim that have textures.

    Could move visual.helpers.setTexIfNoShaders() into here
    """
    # def __init__(self):
    #    super(TextureMixin, self).__init__()

    def _createTexture(self, tex, id, pixFormat,
                       stim, res=128, maskParams=None,
                       forcePOW2=True, dataType=None,
                       wrapping=True):
        """
        :params:
            id:
                is the texture ID
            pixFormat:
                GL.GL_ALPHA, GL.GL_RGB
            useShaders:
                bool
            interpolate:
                bool (determines whether texture will
                use GL_LINEAR or GL_NEAREST
            res:
                the resolution of the texture (unless
                a bitmap image is used)
            dataType:
                None, GL.GL_UNSIGNED_BYTE, GL_FLOAT.
                Only affects image files (numpy arrays will be float)

        For grating stimuli (anything that needs multiple cycles)
        forcePOW2 should be set to be True. Otherwise the wrapping
        of the texture will not work.
        """

        # Create an intensity texture, ranging -1:1.0
        notSqr = False  # most of the options will be creating a sqr texture
        wasImage = False  # change this if image loading works
        useShaders = stim.useShaders
        interpolate = stim.interpolate
        if dataType is None:
            if useShaders and pixFormat == GL.GL_RGB:
                dataType = GL.GL_FLOAT
            else:
                dataType = GL.GL_UNSIGNED_BYTE

        # Fill out unspecified portions of maskParams with default values
        if maskParams is None:
            maskParams = {}
        # fringeWidth affects the proportion of the stimulus diameter that is
        # devoted to the raised cosine.
        allMaskParams = {'fringeWidth': 0.2, 'sd': 3}
        allMaskParams.update(maskParams)

        sin = numpy.sin
        if type(tex) == numpy.ndarray:
            # handle a numpy array
            # for now this needs to be an NxN intensity array
            intensity = tex.astype(numpy.float32)
            if intensity.max() > 1 or intensity.min() < -1:
                logging.error('numpy arrays used as textures should be in '
                              'the range -1(black):1(white)')
            if len(tex.shape) == 3:
                wasLum = False
            else:
                wasLum = True
            # is it 1D?
            if tex.shape[0] == 1:
                stim._tex1D = True
                res = tex.shape[1]
            elif len(tex.shape) == 1 or tex.shape[1] == 1:
                stim._tex1D = True
                res = tex.shape[0]
            else:
                stim._tex1D = False
                # check if it's a square power of two
                maxDim = max(tex.shape)
                powerOf2 = 2**numpy.ceil(numpy.log2(maxDim))
                if (forcePOW2 and
                        (tex.shape[0] != powerOf2 or
                         tex.shape[1] != powerOf2)):
                    logging.error("Requiring a square power of two (e.g. "
                                  "16 x 16, 256 x 256) texture but didn't "
                                  "receive one")
                res = tex.shape[0]
            if useShaders:
                dataType = GL.GL_FLOAT
        elif tex in (None, "none", "None", "color"):
            # 4x4 (2x2 is SUPPOSED to be fine but generates weird colors!)
            res = 1
            intensity = numpy.ones([res, res], numpy.float32)
            wasLum = True
            wrapping = True  # override any wrapping setting for None
        elif tex == "sin":
            # NB 1j*res is a special mgrid notation
            onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2 * pi:1j * res]
            intensity = numpy.sin(onePeriodY - pi / 2)
            wasLum = True
        elif tex == "sqr":  # square wave (symmetric duty cycle)
            # NB 1j*res is a special mgrid notation
            onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2 * pi:1j * res]
            sinusoid = numpy.sin(onePeriodY - pi / 2)
            intensity = numpy.where(sinusoid > 0, 1, -1)
            wasLum = True
        elif tex == "saw":
            intensity = (numpy.linspace(-1.0, 1.0, res, endpoint=True) *
                         numpy.ones([res, 1]))
            wasLum = True
        elif tex == "tri":
            # -1:3 means the middle is at +1
            intens = numpy.linspace(-1.0, 3.0, res, endpoint=True)
            # remove from 3 to get back down to -1
            intens[res // 2 + 1 :] = 2.0 - intens[res // 2 + 1 :]
            intensity = intens * numpy.ones([res, 1])  # make 2D
            wasLum = True
        elif tex == "sinXsin":
            # NB 1j*res is a special mgrid notation
            onePeriodX, onePeriodY = numpy.mgrid[0:2 * pi:1j * res,
                                                 0:2 * pi:1j * res]
            intensity = sin(onePeriodX - pi / 2) * sin(onePeriodY - pi / 2)
            wasLum = True
        elif tex == "sqrXsqr":
            # NB 1j*res is a special mgrid notation
            onePeriodX, onePeriodY = numpy.mgrid[0:2 * pi:1j * res,
                                                 0:2 * pi:1j * res]
            sinusoid = sin(onePeriodX - pi / 2) * sin(onePeriodY - pi / 2)
            intensity = numpy.where(sinusoid > 0, 1, -1)
            wasLum = True
        elif tex == "circle":
            rad = makeRadialMatrix(res)
            intensity = (rad <= 1) * 2 - 1
            wasLum = True
        elif tex == "gauss":
            rad = makeRadialMatrix(res)
            # 3sd.s by the edge of the stimulus
            invVar = (1.0 / allMaskParams['sd']) ** 2.0
            intensity = numpy.exp( -rad**2.0 / (2.0 * invVar)) * 2 - 1
            wasLum = True
        elif tex == "cross":
            X, Y = numpy.mgrid[-1:1:1j * res, -1:1:1j * res]
            tfNegCross = (((X < -0.2) & (Y < -0.2)) |
                          ((X < -0.2) & (Y > 0.2)) |
                          ((X > 0.2) & (Y < -0.2)) |
                          ((X > 0.2) & (Y > 0.2)))
            # tfNegCross == True at places where the cross is transparent,
            # i.e. the four corners
            intensity = numpy.where(tfNegCross, -1, 1)
            wasLum = True
        elif tex == "radRamp":  # a radial ramp
            rad = makeRadialMatrix(res)
            intensity = 1 - 2 * rad
            # clip off the corners (circular)
            intensity = numpy.where(rad < -1, intensity, -1)
            wasLum = True
        elif tex == "raisedCos":  # A raised cosine
            wasLum = True
            hammingLen = 1000  # affects the 'granularity' of the raised cos

            rad = makeRadialMatrix(res)
            intensity = numpy.zeros_like(rad)
            intensity[numpy.where(rad < 1)] = 1
            frng = allMaskParams['fringeWidth']
            raisedCosIdx = numpy.where(
                [numpy.logical_and(rad <= 1, rad >= 1 - frng)])[1:]

            # Make a raised_cos (half a hamming window):
            raisedCos = numpy.hamming(hammingLen)[ : hammingLen // 2]
            raisedCos -= numpy.min(raisedCos)
            raisedCos /= numpy.max(raisedCos)

            # Measure the distance from the edge - this is your index into the
            # hamming window:
            dFromEdge = numpy.abs(
                (1 - allMaskParams['fringeWidth']) - rad[raisedCosIdx])
            dFromEdge /= numpy.max(dFromEdge)
            dFromEdge *= numpy.round(hammingLen/2)

            # This is the indices into the hamming (larger for small distances
            # from the edge!):
            portionIdx = (-1 * dFromEdge).astype(int)

            # Apply the raised cos to this portion:
            intensity[raisedCosIdx] = raisedCos[portionIdx]

            # Scale it into the interval -1:1:
            intensity = intensity - 0.5
            intensity /= numpy.max(intensity)

            # Sometimes there are some remaining artifacts from this process,
            # get rid of them:
            artifactIdx = numpy.where(numpy.logical_and(intensity == -1,
                                                        rad < 0.99))
            intensity[artifactIdx] = 1
            artifactIdx = numpy.where(numpy.logical_and(intensity == 1,
                                                        rad > 0.99))
            intensity[artifactIdx] = 0

        else:
            if isinstance(tex, (basestring, Path)):
                # maybe tex is the name of a file:
                filename = findImageFile(tex)
                if not filename:
                    msg = "Couldn't find image %s; check path? (tried: %s)"
                    logging.error(msg % (tex, os.path.abspath(tex)))
                    logging.flush()
                    raise IOError(msg % (tex, os.path.abspath(tex)))
                try:
                    im = Image.open(filename)
                    im = im.transpose(Image.FLIP_TOP_BOTTOM)
                except IOError:
                    msg = "Found file '%s', failed to load as an image"
                    logging.error(msg % (filename))
                    logging.flush()
                    msg = "Found file '%s' [= %s], failed to load as an image"
                    raise IOError(msg % (tex, os.path.abspath(tex)))
            else:
                # can't be a file; maybe its an image already in memory?
                try:
                    im = tex.copy().transpose(Image.FLIP_TOP_BOTTOM)
                except AttributeError:  # nope, not an image in memory
                    msg = "Couldn't make sense of requested image."
                    logging.error(msg)
                    logging.flush()
                    raise AttributeError(msg)
            # at this point we have a valid im
            stim._origSize = im.size
            wasImage = True
            # is it 1D?
            if im.size[0] == 1 or im.size[1] == 1:
                logging.error("Only 2D textures are supported at the moment")
            else:
                maxDim = max(im.size)
                powerOf2 = int(2**numpy.ceil(numpy.log2(maxDim)))
                if im.size[0] != powerOf2 or im.size[1] != powerOf2:
                    if not forcePOW2:
                        notSqr = True
                    elif globalVars.nImageResizes < reportNImageResizes:
                        msg = ("Image '%s' was not a square power-of-two ' "
                               "'image. Linearly interpolating to be %ix%i")
                        logging.warning(msg % (tex, powerOf2, powerOf2))
                        globalVars.nImageResizes += 1
                        im = im.resize([powerOf2, powerOf2], Image.BILINEAR)
                    elif globalVars.nImageResizes == reportNImageResizes:
                        logging.warning("Multiple images have needed resizing"
                                        " - I'll stop bothering you!")
                        im = im.resize([powerOf2, powerOf2], Image.BILINEAR)
            # is it Luminance or RGB?
            if pixFormat == GL.GL_ALPHA and im.mode != 'L':
                # we have RGB and need Lum
                wasLum = True
                im = im.convert("L")  # force to intensity (need if was rgb)
            elif im.mode == 'L':  # we have lum and no need to change
                wasLum = True
                if useShaders:
                    dataType = GL.GL_FLOAT
            elif pixFormat == GL.GL_RGB:
                # we want RGB and might need to convert from CMYK or Lm
                # texture = im.tostring("raw", "RGB", 0, -1)
                im = im.convert("RGBA")
                wasLum = False
            if dataType == GL.GL_FLOAT:
                # convert from ubyte to float
                # much faster to avoid division 2/255
                intensity = numpy.array(im).astype(
                    numpy.float32) * 0.0078431372549019607 - 1.0
            else:
                intensity = numpy.array(im)
        if pixFormat == GL.GL_RGB and wasLum and dataType == GL.GL_FLOAT:
            # grating stim on good machine
            # keep as float32 -1:1
            if (sys.platform != 'darwin' and
                    stim.win.glVendor.startswith('nvidia')):
                # nvidia under win/linux might not support 32bit float
                # could use GL_LUMINANCE32F_ARB here but check shader code?
                internalFormat = GL.GL_RGB16F_ARB
            else:
                # we've got a mac or an ATI card and can handle
                # 32bit float textures
                # could use GL_LUMINANCE32F_ARB here but check shader code?
                internalFormat = GL.GL_RGB32F_ARB
            # initialise data array as a float
            data = numpy.ones((intensity.shape[0], intensity.shape[1], 3),
                              numpy.float32)
            data[:, :, 0] = intensity  # R
            data[:, :, 1] = intensity  # G
            data[:, :, 2] = intensity  # B
        elif (pixFormat == GL.GL_RGB and
                wasLum and
                dataType != GL.GL_FLOAT and
                stim.useShaders):
            # was a lum image: stick with ubyte for speed
            internalFormat = GL.GL_RGB
            # initialise data array as a float
            data = numpy.ones((intensity.shape[0], intensity.shape[1], 3),
                              numpy.ubyte)
            data[:, :, 0] = intensity  # R
            data[:, :, 1] = intensity  # G
            data[:, :, 2] = intensity  # B
        # Grating on legacy hardware, or ImageStim with wasLum=True
        elif pixFormat == GL.GL_RGB and wasLum and not stim.useShaders:
            # scale by rgb and convert to ubyte
            internalFormat = GL.GL_RGB
            if stim.colorSpace in ('rgb', 'dkl', 'lms', 'hsv'):
                rgb = stim.rgb
            else:
                # colour is not a float - convert to float to do the scaling
                rgb = (stim.rgb / 127.5) - 1.0
            # if wasImage it will also have ubyte values for the intensity
            if wasImage:
                intensity = (intensity / 127.5) - 1.0
            # scale by rgb
            # initialise data array as a float
            data = numpy.ones((intensity.shape[0], intensity.shape[1], 4),
                              numpy.float32)
            data[:, :, 0] = intensity * rgb[0] + stim.rgbPedestal[0]  # R
            data[:, :, 1] = intensity * rgb[1] + stim.rgbPedestal[1]  # G
            data[:, :, 2] = intensity * rgb[2] + stim.rgbPedestal[2]  # B
            data[:, :, :-1] = data[:, :, :-1] * stim.contrast
            # convert to ubyte
            data = float_uint8(data)
        elif pixFormat == GL.GL_RGB and dataType == GL.GL_FLOAT:
            # probably a custom rgb array or rgb image
            internalFormat = GL.GL_RGB32F_ARB
            data = intensity
        elif pixFormat == GL.GL_RGB:
            # not wasLum, not useShaders  - an RGB bitmap with no shader
            #  optionsintensity.min()
            internalFormat = GL.GL_RGB
            data = intensity  # float_uint8(intensity)
        elif pixFormat == GL.GL_ALPHA:
            internalFormat = GL.GL_ALPHA
            dataType = GL.GL_UNSIGNED_BYTE
            if wasImage:
                data = intensity
            else:
                data = float_uint8(intensity)
        # check for RGBA textures
        if len(data.shape) > 2 and data.shape[2] == 4:
            if pixFormat == GL.GL_RGB:
                pixFormat = GL.GL_RGBA
            if internalFormat == GL.GL_RGB:
                internalFormat = GL.GL_RGBA
            elif internalFormat == GL.GL_RGB32F_ARB:
                internalFormat = GL.GL_RGBA32F_ARB
        texture = data.ctypes  # serialise

        # bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id)  # bind that name to the target
        # makes the texture map wrap (this is actually default anyway)
        if wrapping:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        else:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        # data from PIL/numpy is packed, but default for GL is 4 bytes
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        # important if using bits++ because GL_LINEAR
        # sometimes extrapolates to pixel vals outside range
        if interpolate:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            if useShaders:
                # GL_GENERATE_MIPMAP was only available from OpenGL 1.4
                GL.glTexParameteri(
                    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP,
                                   GL.GL_TRUE)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                                data.shape[1], data.shape[0], 0,
                                pixFormat, dataType, texture)
            else:  # use glu
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                                   GL.GL_LINEAR_MIPMAP_NEAREST)
                GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                                     data.shape[1], data.shape[0],
                                     pixFormat, dataType, texture)
        else:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                            data.shape[1], data.shape[0], 0,
                            pixFormat, dataType, texture)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE,
                     GL.GL_MODULATE)  # ?? do we need this - think not!
        # unbind our texture so that it doesn't affect other rendering
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return wasLum

    def clearTextures(self):
        """Clear all textures associated with the stimulus.

        As of v1.61.00 this is called automatically during garbage collection
        of your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self._texID)
        if hasattr(self, '_maskID'):
            GL.glDeleteTextures(1, self._maskID)

    @attributeSetter
    def mask(self, value):
        """The alpha mask (forming the shape of the image)

        This can be one of various options:
            + 'circle', 'gauss', 'raisedCos', 'cross'
            + **None** (resets to default)
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1
        """
        self.__dict__['mask'] = value
        if self.__class__.__name__ == 'ImageStim':
            dataType = GL.GL_UNSIGNED_BYTE
        else:
            dataType = None
        self._createTexture(
            value, id=self._maskID, pixFormat=GL.GL_ALPHA, dataType=dataType,
            stim=self, res=self.texRes, maskParams=self.maskParams,
            wrapping=False)

    def setMask(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'mask', value, log)

    @attributeSetter
    def texRes(self, value):
        """Power-of-two int. Sets the resolution of the mask and texture.
        texRes is overridden if an array or image is provided as mask.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['texRes'] = value

        # ... now rebuild textures (call attributeSetters without logging).
        if hasattr(self, 'tex'):
            setAttribute(self, 'tex', self.tex, log=False)
        if hasattr(self, 'mask'):
            setAttribute(self, 'mask', self.mask, log=False)

    @attributeSetter
    def maskParams(self, value):
        """Various types of input. Default to None.

        This is used to pass additional parameters to the mask if those are
        needed.

            - For 'gauss' mask, pass dict {'sd': 5} to control
                standard deviation.
            - For the 'raisedCos' mask, pass a dict: {'fringeWidth':0.2},
                where 'fringeWidth' is a parameter (float, 0-1), determining
                the proportion of the patch that will be blurred by the raised
                cosine edge."""
        self.__dict__['maskParams'] = value
        # call attributeSetter without log
        setAttribute(self, 'mask', self.mask, log=False)

    @attributeSetter
    def interpolate(self, value):
        """Whether to interpolate (linearly) the texture in the stimulus

        If set to False then nearest neighbour will be used when needed,
        otherwise some form of interpolation will be used.
        """
        self.__dict__['interpolate'] = value


class WindowMixin(object):
    """Window-related attributes and methods.
    Used by BaseVisualStim, SimpleImageStim and ElementArrayStim."""

    @attributeSetter
    def win(self, value):
        """The :class:`~psychopy.visual.Window` object in which the
        stimulus will be rendered by default. (required)

       Example, drawing same stimulus in two different windows and display
       simultaneously. Assuming that you have two windows and a stimulus
       (win1, win2 and stim)::

           stim.win = win1  # stimulus will be drawn in win1
           stim.draw()  # stimulus is now drawn to win1
           stim.win = win2  # stimulus will be drawn in win2
           stim.draw()  # it is now drawn in win2
           win1.flip(waitBlanking=False)  # do not wait for next
                        # monitor update
           win2.flip()  # wait for vertical blanking.

        Note that this just changes **default** window for stimulus.
        You could also specify window-to-draw-to when drawing::

           stim.draw(win1)
           stim.draw(win2)
        """
        self.__dict__['win'] = value

    @attributeSetter
    def units(self, value):
        """
        None, 'norm', 'cm', 'deg', 'degFlat', 'degFlatPos', or 'pix'

        If None then the current units of the
        :class:`~psychopy.visual.Window` will be used.
        See :ref:`units` for explanation of other options.

        Note that when you change units, you don't change the stimulus
        parameters and it is likely to change appearance. Example::

            # This stimulus is 20% wide and 50% tall with respect to window
            stim = visual.PatchStim(win, units='norm', size=(0.2, 0.5)

            # This stimulus is 0.2 degrees wide and 0.5 degrees tall.
            stim.units = 'deg'
        """
        if value != None and len(value):
            self.__dict__['units'] = value
        else:
            self.__dict__['units'] = self.win.units

        # Update size and position if they are defined (tested as numeric).
        # If not, this is probably
        # during some init and they will be defined later, given the new unit.
        try:
            # quick and dirty way to check that both are numeric. This avoids
            # the heavier attributeSetter calls.
            self.size * self.pos
            self.size = self.size
            self.pos = self.pos
        except Exception:
            pass

    @attributeSetter
    def useShaders(self, value):
        """Should shaders be used to render the stimulus
        (typically leave as `True`)

        If the system support the use of OpenGL shader language then leaving
        this set to True is highly recommended. If shaders cannot be used then
        various operations will be slower (notably, changes to stimulus color
        or contrast)
        """
        if value == True and self.win._haveShaders == False:
            logging.error("Shaders were requested but aren't available. "
                          "Shaders need OpenGL 2.0+ drivers")
        if value != self.useShaders:  # if there's a change...
            self.__dict__['useShaders'] = value
            if hasattr(self, 'tex'):
                self.tex = self.tex  # calling attributeSetter
            elif hasattr(self, 'mask'):
                # calling attributeSetter (does the same as mask)
                self.mask = self.mask
            if hasattr(self, '_imName'):
                self.setImage(self._imName, log=False)
            if self.__class__.__name__ == 'TextStim':
                self._needSetText = True
            self._needUpdate = True

    def setUseShaders(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'useShaders', value, log)  # call attributeSetter

    def draw(self):
        raise NotImplementedError('Stimulus classes must override '
                                  'visual.BaseVisualStim.draw')

    def _selectWindow(self, win):
        """Switch drawing to the specified window. Calls the window's
        _setCurrent() method which handles the switch.
        """
        win._setCurrent()

    def _updateList(self):
        """The user shouldn't need this method since it gets called
        after every call to .set()
        Chooses between using and not using shaders each call.
        """
        if self.useShaders:
            self._updateListShaders()
        else:
            self._updateListNoShaders()


class BaseVisualStim(MinimalStim, WindowMixin, LegacyVisualMixin):
    """A template for a visual stimulus class.

    Actual visual stim like GratingStim, TextStim etc... are based on this.
    Not finished...?

    Methods defined here will override Minimal & Legacy, but best to avoid
    that for simplicity & clarity.
    """

    def __init__(self, win, units=None, name='', autoLog=None):
        self.autoLog = False  # just to start off during init, set at end
        self.win = win
        self.units = units
        self._rotationMatrix = [[1., 0.], [0., 1.]]  # no rotation by default
        # self.autoLog is set at end of MinimalStim.__init__
        super(BaseVisualStim, self).__init__(name=name, autoLog=autoLog)
        if self.autoLog:
            msg = ("%s is calling BaseVisualStim.__init__() with autolog=True"
                   ". Set autoLog to True only at the end of __init__())")
            logging.warning(msg % (self.__class__.__name__))

    @attributeSetter
    def opacity(self, value):
        """Determines how visible the stimulus is relative to background

        The value should be a single float ranging 1.0 (opaque) to 0.0
        (transparent). :ref:`Operations <attrib-operations>` are supported.
        Precisely how this is used depends on the :ref:`blendMode`.
        """
        self.__dict__['opacity'] = value

        if not 0 <= value <= 1 and self.autoLog:
            logging.warning('Setting opacity outside range 0.0 - 1.0'
                            ' has no additional effect')

        # opacity is coded by the texture, if not using shaders
        if hasattr(self, 'useShaders') and not self.useShaders:
            if hasattr(self, 'mask'):
                self.mask = self.mask  # call attributeSetter

    @attributeSetter
    def ori(self, value):
        """The orientation of the stimulus (in degrees).

        Should be a single value (:ref:`scalar <attrib-scalar>`).
        :ref:`Operations <attrib-operations>` are supported.

        Orientation convention is like a clock: 0 is vertical, and positive
        values rotate clockwise. Beyond 360 and below zero values wrap
        appropriately.

        """
        self.__dict__['ori'] = value
        radians = value * 0.017453292519943295
        sin, cos = numpy.sin, numpy.cos
        self._rotationMatrix = numpy.array([[cos(radians), -sin(radians)],
                                            [sin(radians), cos(radians)]])
        self._needVertexUpdate = True  # need to update update vertices
        self._needUpdate = True

    @attributeSetter
    def size(self, value):
        """The size (width, height) of the stimulus in the stimulus
        :ref:`units <units>`

        Value should be :ref:`x,y-pair <attrib-xy>`,
        :ref:`scalar <attrib-scalar>` (applies to both dimensions)
        or None (resets to default). :ref:`Operations <attrib-operations>`
        are supported.

        Sizes can be negative (causing a mirror-image reversal) and can
        extend beyond the window.

        Example::

            stim.size = 0.8  # Set size to (xsize, ysize) = (0.8, 0.8)
            print(stim.size)  # Outputs array([0.8, 0.8])
            stim.size += (0.5, -0.5)  # make wider and flatter: (1.3, 0.3)

        Tip: if you can see the actual pixel range this corresponds to by
        looking at `stim._sizeRendered`
        """
        array = numpy.array
        value = val2array(value)  # Check correct user input
        self._requestedSize = copy.copy(value)  # to track whether we're using a default
        # None --> set to default
        if value is None:
            # Set the size to default (e.g. to the size of the loaded image
            # calculate new size
            if self._origSize is None:  # not an image from a file
                # this was PsychoPy's original default
                value = numpy.array([0.5, 0.5])
            else:
                # we have an image; calculate the size in `units` that matches
                # original pixel size
                # also scale for retina display (virtual pixels are bigger)
                if self.win.useRetina:
                    winSize = self.win.size / 2
                else:
                    winSize = self.win.size
                # then handle main scale
                if self.units == 'pix':
                    value = numpy.array(self._origSize)
                elif self.units in ('deg', 'degFlatPos', 'degFlat'):
                    # NB when no size has been set (assume to use orig size
                    # in pix) this should not be corrected for flat anyway,
                    # so degFlat == degFlatPos
                    value = pix2deg(array(self._origSize, float),
                                    self.win.monitor)
                elif self.units == 'norm':
                    value = 2 * array(self._origSize, float) / winSize
                elif self.units == 'height':
                    value = array(self._origSize, float) / winSize[1]
                elif self.units == 'cm':
                    value = pix2cm(array(self._origSize, float),
                                   self.win.monitor)
                else:
                    msg = ("Failed to create default size for ImageStim. "
                           "Unsupported unit, %s")
                    raise AttributeError(msg % repr(self.units))
        self.__dict__['size'] = value
        self._needVertexUpdate = True
        self._needUpdate = True
        if hasattr(self, '_calcCyclesPerStim'):
            self._calcCyclesPerStim()

    @attributeSetter
    def pos(self, value):
        """The position of the center of the stimulus in the stimulus
        :ref:`units <units>`

        `value` should be an :ref:`x,y-pair <attrib-xy>`.
        :ref:`Operations <attrib-operations>` are also supported.

        Example::

            stim.pos = (0.5, 0)  # Set slightly to the right of center
            stim.pos += (0.5, -1)  # Increment pos rightwards and upwards.
                Is now (1.0, -1.0)
            stim.pos *= 0.2  # Move stim towards the center.
                Is now (0.2, -0.2)

        Tip: If you need the position of stim in pixels, you can obtain
        it like this:

            from psychopy.tools.monitorunittools import posToPix
            posPix = posToPix(stim)
        """
        self.__dict__['pos'] = val2array(value, False, False)
        self._needVertexUpdate = True
        self._needUpdate = True

    def setPos(self, newPos, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'pos', val2array(newPos, False), log, operation)

    def setDepth(self, newDepth, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'depth', newDepth, log, operation)

    def setSize(self, newSize, operation='', units=None, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        if units is None:
            # need to change this to create several units from one
            units = self.units
        setAttribute(self, 'size', val2array(newSize, False), log, operation)

    def setOri(self, newOri, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'ori', newOri, log, operation)

    def setOpacity(self, newOpacity, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'opacity', newOpacity, log, operation)

    def _set(self, attrib, val, op='', log=None):
        """DEPRECATED since 1.80.04 + 1.
        Use setAttribute() and val2array() instead.
        """
        # format the input value as float vectors
        if type(val) in [tuple, list, numpy.ndarray]:
            val = val2array(val)

        # Set attribute with operation and log
        setAttribute(self, attrib, val, log, op)

        # For DotStim
        if attrib in ('nDots', 'coherence'):
            self.coherence = round(self.coherence * self.nDots) / self.nDots
