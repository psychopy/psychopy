#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides class BaseVisualStim and mixins; subclass to get visual stimuli
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from statistics import mean
from psychopy.colors import Color, colorSpaces
from psychopy.layout import Vector, Position, Size, Vertices, unitTypes

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
import ctypes
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import (attributeSetter, logAttrib,
                                           setAttribute, AttributeGetSetMixin)
from psychopy.tools.monitorunittools import (cm2pix, deg2pix, pix2cm,
                                             pix2deg, convertToPix)
from psychopy.visual.helpers import (pointInPolygon, polygonsOverlap,
                                     setColor, findImageFile)
from psychopy.tools.typetools import float_uint8
from psychopy.tools.arraytools import makeRadialMatrix, createLumPattern
from psychopy.event import Mouse
from psychopy.tools.colorspacetools import dkl2rgb, lms2rgb  # pylint: disable=W0611

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


class MinimalStim(AttributeGetSetMixin):
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
        """The name (`str`) of the object to be using during logged messages
        about this stim. If you have multiple stimuli in your experiment this
        really helps to make sense of log files!

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
            # Add to editable list (if needed)
            self.win.addEditable(self)
            # Mark as started
            self.status = STARTED
        elif value == False:
            # remove from autodraw lists
            toDrawDepths.pop(toDraw.index(self))  # remove from depths
            toDraw.remove(self)  # remove from draw list
            # Remove from editable list (if needed)
            self.win.removeEditable(self)
            # Mark as stopped
            self.status = STOPPED

    def setAutoDraw(self, value, log=None):
        """Sets autoDraw. Usually you can use 'stim.attribute = value'
        syntax instead, but use this method to suppress the log message.
        """
        setAttribute(self, 'autoDraw', value, log)

    @attributeSetter
    def autoLog(self, value):
        """Whether every change in this stimulus should be auto logged.

        Value should be: `True` or `False`. Set to `False` if your stimulus is
        updating frequently (e.g. updating its position every frame) and you
        want to avoid swamping the log file with messages that aren't likely to
        be useful.
        """
        self.__dict__['autoLog'] = value

    def setAutoLog(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'autoLog', value, log)


class LegacyVisualMixin:
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

    @attributeSetter
    def depth(self, value):
        """DEPRECATED, depth is now controlled simply by drawing order.
        """
        self.__dict__['depth'] = value


class LegacyForeColorMixin:
    """
    Mixin class to give an object all of the legacy functions for setting foreground color
    """
    def setDKL(self, color, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self.setForeColor(color, 'dkl', operation)

    def setLMS(self, color, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self.setForeColor(color, 'lms', operation)

    @property
    def foreRGB(self):
        """
        DEPRECATED: Legacy property for setting the foreground color of a stimulus in RGB, instead use `obj._foreColor.rgb`
        """
        return self._foreColor.rgb

    @foreRGB.setter
    def foreRGB(self, value):
        self.foreColor = Color(value, 'rgb')

    @property
    def RGB(self):
        """
        DEPRECATED: Legacy property for setting the foreground color of a stimulus in RGB, instead use `obj._foreColor.rgb`
        """
        return self.foreRGB

    @RGB.setter
    def RGB(self, value):
        self.foreRGB = value

    def setRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for foreground RGB, instead set `obj._foreColor.rgb`
        """
        self.setForeColor(color, 'rgb', operation, log)

    def setForeRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for foreground RGB, instead set `obj._foreColor.rgb`
        """
        self.setForeColor(color, 'rgb', operation, log)

    @property
    def foreColorSpace(self):
        """Deprecated, please use colorSpace to set color space for the entire
        object.
        """
        return self.colorSpace

    @foreColorSpace.setter
    def foreColorSpace(self, value):
        logging.warning(
            "Setting color space by attribute rather than by object is deprecated. Value of foreColorSpace has been assigned to colorSpace.")
        self.colorSpace = value


class LegacyFillColorMixin:
    """
    Mixin class to give an object all of the legacy functions for setting fill color
    """
    @property
    def fillRGB(self):
        """
        DEPRECATED: Legacy property for setting the fill color of a stimulus in RGB, instead use `obj._fillColor.rgb`
        """
        return self._fillColor.rgb

    @fillRGB.setter
    def fillRGB(self, value):
        self.fillColor = Color(value, 'rgb')

    @property
    def backRGB(self):
        """
        DEPRECATED: Legacy property for setting the fill color of a stimulus in RGB, instead use `obj._fillColor.rgb`
        """
        return self.fillRGB

    @backRGB.setter
    def backRGB(self, value):
        self.fillRGB = value

    def setFillRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for fill RGB, instead set `obj._fillColor.rgb`
        """
        self.setFillColor(color, 'rgb', operation, log)

    def setBackRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for fill RGB, instead set `obj._fillColor.rgb`
        """
        self.setFillColor(color, 'rgb', operation, log)

    @property
    def fillColorSpace(self):
        """Deprecated, please use colorSpace to set color space for the entire
        object.
        """
        return self.colorSpace

    @fillColorSpace.setter
    def fillColorSpace(self, value):
        logging.warning("Setting color space by attribute rather than by object is deprecated. Value of fillColorSpace has been assigned to colorSpace.")
        self.colorSpace = value

    @property
    def backColorSpace(self):
        """Deprecated, please use colorSpace to set color space for the entire
        object.
        """
        return self.colorSpace

    @backColorSpace.setter
    def backColorSpace(self, value):
        logging.warning(
            "Setting color space by attribute rather than by object is deprecated. Value of backColorSpace has been assigned to colorSpace.")
        self.colorSpace = value


class LegacyBorderColorMixin:
    """
    Mixin class to give an object all of the legacy functions for setting border color
    """
    @property
    def borderRGB(self):
        """
        DEPRECATED: Legacy property for setting the border color of a stimulus in RGB, instead use `obj._borderColor.rgb`
        """
        return self._borderColor.rgb

    @borderRGB.setter
    def borderRGB(self, value):
        self.borderColor = Color(value, 'rgb')

    @property
    def lineRGB(self):
        """
        DEPRECATED: Legacy property for setting the border color of a stimulus in RGB, instead use `obj._borderColor.rgb`
        """
        return self.borderRGB

    @lineRGB.setter
    def lineRGB(self, value):
        self.borderRGB = value

    def setBorderRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for border RGB, instead set `obj._borderColor.rgb`
        """
        self.setBorderColor(color, 'rgb', operation, log)

    def setLineRGB(self, color, operation='', log=None):
        """
        DEPRECATED: Legacy setter for border RGB, instead set `obj._borderColor.rgb`
        """
        self.setBorderColor(color, 'rgb', operation, log)

    @property
    def borderColorSpace(self):
        """Deprecated, please use colorSpace to set color space for the entire
        object
        """
        return self.colorSpace

    @borderColorSpace.setter
    def borderColorSpace(self, value):
        logging.warning(
            "Setting color space by attribute rather than by object is deprecated. Value of borderColorSpace has been assigned to colorSpace.")
        self.colorSpace = value

    @property
    def lineColorSpace(self):
        """Deprecated, please use colorSpace to set color space for the entire
        object
        """
        return self.colorSpace

    @lineColorSpace.setter
    def lineColorSpace(self, value):
        logging.warning(
            "Setting color space by attribute rather than by object is deprecated. Value of lineColorSpace has been assigned to colorSpace.")
        self.colorSpace = value


class LegacyColorMixin(LegacyForeColorMixin, LegacyFillColorMixin, LegacyBorderColorMixin):
    """
    Mixin class to give an object all of the legacy functions for setting all colors (fore, fill and border
    """


class BaseColorMixin:
    """
    Mixin class giving base color methods (e.g. colorSpace) which are needed for any color stuff.
    """
    @property
    def colorSpace(self):
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
        if hasattr(self, '_colorSpace'):
            return self._colorSpace
        else:
            return 'rgba'

    @colorSpace.setter
    def colorSpace(self, value):
        if value in colorSpaces:
            self._colorSpace = value
        else:
            logging.error(f"'{value}' is not a valid color space")

    @property
    def contrast(self):
        """A value that is simply multiplied by the color.

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
        if hasattr(self, '_foreColor'):
            return self._foreColor.contrast

    @contrast.setter
    def contrast(self, value):
        if hasattr(self, '_foreColor'):
            self._foreColor.contrast = value
        if hasattr(self, '_fillColor'):
            self._fillColor.contrast = value
        if hasattr(self, '_borderColor'):
            self._borderColor.contrast = value

    def setContrast(self, newContrast, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        if newContrast is not None:
            self.contrast = newContrast
        if operation in ['', '=']:
            self.contrast = newContrast
        elif operation in ['+']:
            self.contrast += newContrast
        elif operation in ['-']:
            self.contrast -= newContrast
        else:
            logging.error(f"Operation '{operation}' not recognised.")

    def _getDesiredRGB(self, rgb, colorSpace, contrast):
        """ Convert color to RGB while adding contrast.
        Requires self.rgb, self.colorSpace and self.contrast
        """
        col = Color(rgb, colorSpace)
        col.contrast *= contrast or 0
        return col.render('rgb')

    def updateColors(self):
        """Placeholder method to update colours when set externally, for example updating the `pallette` attribute of
        a textbox"""
        return


class ForeColorMixin(BaseColorMixin, LegacyForeColorMixin):
    """
    Mixin class for visual stim that need fore color.
    """
    @property
    def foreColor(self):
        """Foreground color of the stimulus

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
        if hasattr(self, '_foreColor'):
            return self._foreColor.render(self.colorSpace)

    @foreColor.setter
    def foreColor(self, value):
        if isinstance(value, Color):
            # If supplied with a Color object, set as that
            self._foreColor = value
        else:
            # Otherwise, make a new Color object
            self._foreColor = Color(value, self.colorSpace, contrast=self.contrast)
        if not self._foreColor:
            self._foreColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")
        # Handle logging
        logAttrib(self, log=None, attrib="foreColor", value=value)

    @property
    def color(self):
        """Alternative way of setting `foreColor`."""
        return self.foreColor

    @color.setter
    def color(self, value):
        self.foreColor = value

    @property
    def fontColor(self):
        """Alternative way of setting `foreColor`."""
        return self.foreColor

    @fontColor.setter
    def fontColor(self, value):
        self.foreColor = value

    def setForeColor(self, color, colorSpace=None, operation='', log=None):
        """Hard setter for foreColor, allows suppression of the log message,
        simultaneous colorSpace setting and calls update methods.
        """
        setColor(obj=self, colorAttrib="foreColor", color=color, colorSpace=colorSpace or self.colorSpace, operation=operation, log=log)
        # Trigger color update for components like Textbox which have different behaviours for a hard setter
        self.updateColors()

    def setColor(self, color, colorSpace=None, operation='', log=None):
        self.setForeColor(color, colorSpace=colorSpace, operation=operation, log=log)

    def setFontColor(self, color, colorSpace=None, operation='', log=None):
        self.setForeColor(color, colorSpace=colorSpace, operation=operation, log=log)


class FillColorMixin(BaseColorMixin, LegacyFillColorMixin):
    """
    Mixin class for visual stim that need fill color.
    """

    @property
    def fillColor(self):
        """Set the fill color for the shape."""
        if hasattr(self, '_fillColor'):
            return getattr(self._fillColor, self.colorSpace)  # return self._fillColor.render(self.colorSpace)

    @fillColor.setter
    def fillColor(self, value):
        if isinstance(value, Color):
            # If supplied with a color object, set as that
            self._fillColor = value
        else:
            # Otherwise, make a new Color object
            self._fillColor = Color(value, self.colorSpace, contrast=self.contrast)
        if not self._fillColor:
            # If given an invalid color, set as transparent and log error
            self._fillColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")
        # Handle logging
        logAttrib(self, log=None, attrib="fillColor", value=value)

    @property
    def backColor(self):
        """Alternative way of setting fillColor"""
        return self.fillColor

    @backColor.setter
    def backColor(self, value):
        self.fillColor = value

    @property
    def backgroundColor(self):
        """Alternative way of setting fillColor"""
        return self.fillColor

    @backgroundColor.setter
    def backgroundColor(self, value):
        self.fillColor = value

    def setFillColor(self, color, colorSpace=None, operation='', log=None):
        """Hard setter for fillColor, allows suppression of the log message,
        simultaneous colorSpace setting and calls update methods.
        """
        setColor(obj=self, colorAttrib="fillColor", color=color, colorSpace=colorSpace or self.colorSpace, operation=operation, log=log)
        # Trigger color update for components like Textbox which have different behaviours for a hard setter
        self.updateColors()

    def setBackColor(self, color, colorSpace=None, operation='', log=None):
        self.setFillColor(color, colorSpace=colorSpace, operation=operation, log=log)

    def setBackgroundColor(self, color, colorSpace=None, operation='', log=None):
        self.setFillColor(color, colorSpace=colorSpace, operation=operation, log=log)


class BorderColorMixin(BaseColorMixin, LegacyBorderColorMixin):
    @property
    def borderColor(self):
        if hasattr(self, '_borderColor'):
            return self._borderColor.render(self.colorSpace)

    @borderColor.setter
    def borderColor(self, value):
        if isinstance(value, Color):
            # If supplied with a color object, set as that
            self._borderColor = value
        else:
            # If supplied with a valid color, use it to make a color object
            self._borderColor = Color(value, self.colorSpace, contrast=self.contrast)
        if not self._borderColor:
            # If given an invalid color, set as transparent and log error
            self._borderColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        # Handle logging
        logAttrib(self, log=None, attrib="borderColor", value=value)

    @property
    def lineColor(self):
        """Alternative way of setting `borderColor`."""
        return self.borderColor

    @lineColor.setter
    def lineColor(self, value):
        self.borderColor = value

    def setBorderColor(self, color, colorSpace=None, operation='', log=None):
        """Hard setter for `fillColor`, allows suppression of the log message,
        simultaneous colorSpace setting and calls update methods.
        """
        setColor(obj=self, colorAttrib="borderColor", color=color, colorSpace=colorSpace or self.colorSpace, operation=operation, log=log)
        # Trigger color update for components like Textbox which have different behaviours for a hard setter
        self.updateColors()

    def setLineColor(self, color, colorSpace=None, operation='', log=None):
        self.setBorderColor(color, colorSpace=None, operation='', log=None)


class ColorMixin(ForeColorMixin, FillColorMixin, BorderColorMixin):
    """
    Mixin class for visual stim that need fill, fore and border color.
    """


class ContainerMixin:
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
        # Get vertices from available attribs
        if hasattr(self, '_tesselVertices'):
            # Shapes need to render from this
            verts = self._tesselVertices
        elif hasattr(self, "_vertices"):
            # Non-shapes should use base vertices object
            verts = self._vertices
        else:
            # We'll settle for base verts array
            verts = self.vertices

        # Convert to a vertices object if not already
        if not isinstance(verts, Vertices):
            verts = Vertices(verts, obj=self)

        # If needed, sub in missing values for flip and anchor
        if hasattr(self, "flip"):
            verts.flip = self.flip
        if hasattr(self, "anchor"):
            verts.anchor = self.anchor
        # Supply current object's pos and size objects
        verts._size = self._size
        verts._pos = self._pos
        # Apply rotation
        verts = (verts.pix - self._pos.pix).dot(self._rotationMatrix) + self._pos.pix
        if hasattr(self, "_vertices"):
            borderVerts = (self._vertices.pix - self._pos.pix).dot(self._rotationMatrix) + self._pos.pix
        else:
            borderVerts = verts
        # Set values
        self.__dict__['verticesPix'] = verts
        self.__dict__['_borderPix'] = borderVerts
        # Mark as updated
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


class TextureMixin:
    """Mixin class for visual stim that have textures.

    Could move visual.helpers.setTexIfNoShaders() into here.

    """
    def _createTexture(self, tex, id, pixFormat, stim, res=128, maskParams=None,
                       forcePOW2=True, dataType=None, wrapping=True):
        """Create a new OpenGL 2D image texture.

        Parameters
        ----------
        tex : Any
            Texture data. Value can be anything that resembles image data.
        id : int or :class:`~pyglet.gl.GLint`
            Texture ID.
        pixFormat : :class:`~pyglet.gl.GLenum` or int
            Pixel format to use, values can be `GL_ALPHA` or `GL_RGB`.
        stim : Any
            Stimulus object using the texture.
        res : int
            The resolution of the texture (unless a bitmap image is used).
        maskParams : dict or None
            Additional parameters to configure the mask used with this texture.
        forcePOW2 : bool
            Force the texture to be stored in a square memory area. For grating
            stimuli (anything that needs multiple cycles) `forcePOW2` should be
            set to be `True`. Otherwise the wrapping of the texture will not
            work.
        dataType : class:`~pyglet.gl.GLenum`, int or None
            None, `GL_UNSIGNED_BYTE`, `GL_FLOAT`. Only affects image files
            (numpy arrays will be float).
        wrapping : bool
            Enable wrapping of the texture. A texture will be set to repeat (or
            tile).
        """

        # transform all variants of `None` to that, simplifies conditions below
        if isinstance(tex, str) and tex in ["none", "None", "color"]:
            tex = None

        # Create an intensity texture, ranging -1:1.0
        notSqr = False  # most of the options will be creating a sqr texture
        wasImage = False  # change this if image loading works
        interpolate = stim.interpolate
        if dataType is None:
            if pixFormat == GL.GL_RGB:
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
                powerOf2 = 2 ** numpy.ceil(numpy.log2(maxDim))
                if (forcePOW2 and
                        (tex.shape[0] != powerOf2 or
                         tex.shape[1] != powerOf2)):
                    logging.error("Requiring a square power of two (e.g. "
                                  "16 x 16, 256 x 256) texture but didn't "
                                  "receive one")
                res = tex.shape[0]

            dataType = GL.GL_FLOAT
        elif tex in ("sin", "sqr", "saw", "tri", "sinXsin", "sqrXsqr", "circle",
                     "gauss", "cross", "radRamp", "raisedCos", None):
            if tex is None:
                res = 1
                wrapping = True  # override any wrapping setting for None

            # compute array of intensity value for desired pattern
            intensity = createLumPattern(tex, res, None, allMaskParams)
            wasLum = True
        else:
            if isinstance(tex, (str, Path)):
                # maybe tex is the name of a file:
                filename = findImageFile(tex, checkResources=True)
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
            elif hasattr(tex, 'getVideoFrame'):  # camera or movie textures
                # get an image to configure the initial texture store
                if hasattr(tex, 'frameSize'):
                    if tex.frameSize is None:
                        raise RuntimeError(
                            "`Camera.frameSize` is not yet specified, cannot "
                            "initialize texture!")
                    self._origSize = frameSize = tex.frameSize
                    # empty texture for initialization
                    blankTexture = numpy.zeros(
                        (frameSize[0] * frameSize[1] * 3), dtype=numpy.uint8)
                    im = Image.frombuffer(
                        'RGB',
                        frameSize,
                        blankTexture
                    ).transpose(Image.FLIP_TOP_BOTTOM)
                else:
                    msg = "Failed to initialize texture from camera stream."
                    logging.error(msg)
                    logging.flush()
                    raise AttributeError(msg)
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
                dataType = GL.GL_FLOAT
            elif pixFormat == GL.GL_RGB:
                # we want RGB and might need to convert from CMYK or Lm
                # texture = im.tostring("raw", "RGB", 0, -1)
                im = im.convert("RGBA")
                wasLum = False
            else:
                raise ValueError('cannot determine if image is luminance or RGB')

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
                dataType != GL.GL_FLOAT):
            # was a lum image: stick with ubyte for speed
            internalFormat = GL.GL_RGB
            # initialise data array as a float
            data = numpy.ones((intensity.shape[0], intensity.shape[1], 3),
                              numpy.ubyte)
            data[:, :, 0] = intensity  # R
            data[:, :, 1] = intensity  # G
            data[:, :, 2] = intensity  # B
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
        else:
            raise ValueError("invalid or unsupported `pixFormat`")

        # check for RGBA textures
        if len(data.shape) > 2 and data.shape[2] == 4:
            if pixFormat == GL.GL_RGB:
                pixFormat = GL.GL_RGBA
            if internalFormat == GL.GL_RGB:
                internalFormat = GL.GL_RGBA
            elif internalFormat == GL.GL_RGB32F_ARB:
                internalFormat = GL.GL_RGBA32F_ARB
        texture = data.ctypes  # serialise

        # Create the pixel buffer object which will serve as the texture memory
        # store. First we compute the number of bytes used to store the texture.
        # We need to determine the data type in use by the texture to do this.
        if stim is not None and hasattr(stim, '_pixbuffID'):
            if dataType == GL.GL_UNSIGNED_BYTE:
                storageType = GL.GLubyte
            elif dataType == GL.GL_FLOAT:
                storageType = GL.GLfloat
            else:
                # raise waring or error? just default to `GLfloat` for now
                storageType = GL.GLfloat

            # compute buffer size
            bufferSize = data.size * ctypes.sizeof(storageType)

            # create the pixel buffer to access texture memory as an array
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, stim._pixbuffID)
            GL.glBufferData(
                GL.GL_PIXEL_UNPACK_BUFFER,
                bufferSize,
                None,
                GL.GL_STREAM_DRAW)  # one-way app -> GL
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

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
            # GL_GENERATE_MIPMAP was only available from OpenGL 1.4
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP,
                               GL.GL_TRUE)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                            data.shape[1], data.shape[0], 0,
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
        if hasattr(self, '_texID'):
            GL.glDeleteTextures(1, self._texID)

        if hasattr(self, '_maskID'):
            GL.glDeleteTextures(1, self._maskID)

        if hasattr(self, '_pixBuffID'):
            GL.glDeleteBuffers(1, self._pixBuffID)

    @attributeSetter
    def mask(self, value):
        """The alpha mask (forming the shape of the image).

        This can be one of various options:
            * 'circle', 'gauss', 'raisedCos', 'cross'
            * **None** (resets to default)
            * the name of an image file (most formats supported)
            * a numpy array (1xN or NxN) ranging -1:1

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
        """Various types of input. Default to `None`.

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
        """Whether to interpolate (linearly) the texture in the stimulus.

        If set to False then nearest neighbour will be used when needed,
        otherwise some form of interpolation will be used.
        """
        self.__dict__['interpolate'] = value


class WindowMixin:
    """Window-related attributes and methods.

    Used by BaseVisualStim, SimpleImageStim and ElementArrayStim.

    """
    @property
    def win(self):
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
        return self.__dict__['win']

    @win.setter
    def win(self, value):
        self.__dict__['win'] = value
        # Update window ref in size and pos objects
        if hasattr(self, "_size") and isinstance(self._size, Vector):
            self._size.win = value
        if hasattr(self, "_pos") and isinstance(self._pos, Vector):
            self._pos.win = value

    @property
    def pos(self):
        if hasattr(self, "_pos"):
            return getattr(self._pos, self.units)

    @pos.setter
    def pos(self, value):
        # If no autolog attribute, assume silent
        if hasattr(self, "autoLog"):
            log = self.autoLog
        else:
            log = False
        # Do attribute setting
        setAttribute(self, '_pos', Position(value, units=self.units, win=self.win), log)

        if hasattr(self, "_vertices"):
            self._vertices._pos = self._pos

        if hasattr(self, "_vertices"):
            self._vertices._pos = self._pos

    @property
    def size(self):
        if hasattr(self, "_size"):
            return getattr(self._size, self.units)

    @size.setter
    def size(self, value):
        # Convert None to a 2x1 tuple
        if value is None:
            value = (None, None)
        # If no autolog attribute, assume silent
        if hasattr(self, "autoLog"):
            log = self.autoLog
        else:
            log = False
        # Do attribute setting
        setAttribute(self, '_size', Size(value, units=self.units, win=self.win), log)

        if hasattr(self, "_vertices"):
            self._vertices._size = self._size

        if hasattr(self, "_vertices"):
            self._vertices._size = self._size

    @property
    def width(self):
        if len(self.size.shape) == 1:
            # Return first value if a 1d array
            return self.size[0]
        elif len(self.size.shape) == 2:
            # Return first column if a 2d array
            return self.size[:, 0]

    @width.setter
    def width(self, value):
        # Convert to a numpy array
        value = numpy.array(value)
        # Get original size
        size = self.size
        # Set size
        if len(self.size.shape) == 1:
            # Set first value if a 1d array
            size[0] = value
        elif len(self.size.shape) == 2:
            # Set first column if a 2d array
            size[:, 0] = value
        else:
            raise NotImplementedError(
                f"Cannot set height and width for {type(self).__name__} objects with more than 2 dimensions. "
                f"Please use .size instead."
            )

        self.size = size

    @property
    def height(self):
        if len(self.size.shape) == 1:
            # Return first value if a 1d array
            return self.size[1]
        elif len(self.size.shape) == 2:
            # Return first column if a 2d array
            return self.size[:, 1]

    @height.setter
    def height(self, value):
        # Convert to a numpy array
        value = numpy.array(value)
        # Get original size
        size = self.size
        # Set size
        if len(self.size.shape) == 1:
            # Set second value if a 1d array
            size[1] = value
        elif len(self.size.shape) == 2:
            # Set second column if a 2d array
            size[:, 1] = value
        else:
            raise NotImplementedError(
                f"Cannot set height and width for {type(self).__name__} objects with more than 2 dimensions. "
                f"Please use .size instead."
            )

        self.size = size

    @property
    def vertices(self):
        # Get or make Vertices object
        if hasattr(self, "_vertices"):
            verts = self._vertices
        else:
            # If not defined, assume vertices are just a square
            verts = self._vertices = Vertices(numpy.array([
                                [0.5, -0.5],
                                [-0.5, -0.5],
                                [-0.5, 0.5],
                                [0.5, 0.5],
                            ]), obj=self, flip=self.flip, anchor=self.anchor)
        return verts.base

    @vertices.setter
    def vertices(self, value):
        # If None, use defaut
        if value is None:
            value = [
                [0.5, -0.5],
                [-0.5, -0.5],
                [-0.5, 0.5],
                [0.5, 0.5],
            ]
        # Create Vertices object
        self._vertices = Vertices(value, obj=self, flip=self.flip, anchor=self.anchor)
        self._needVertexUpdate = True

    @property
    def flip(self):
        """
        1x2 array for flipping vertices along each axis; set as True to flip or False to not flip. If set as a single value, will duplicate across both axes. Accessing the protected attribute (`._flip`) will give an array of 1s and -1s with which to multiply vertices.
        """
        # Get base value
        if hasattr(self, "_flip"):
            flip = self._flip
        else:
            flip = numpy.array([[False, False]])
        # Convert from boolean
        return flip == -1

    @flip.setter
    def flip(self, value):
        if value is None:
            value = False
        # Convert to 1x2 numpy array
        value = numpy.array(value)
        value.resize((1, 2))
        # Ensure values were bool
        assert value.dtype == bool, "Flip values must be either a boolean (True/False) or an array of booleans"
        # Set as multipliers rather than bool
        self._flip = numpy.array([[
            -1 if value[0, 0] else 1,
            -1 if value[0, 1] else 1,
        ]])
        self._flipHoriz, self._flipVert = self._flip[0]
        # Apply to vertices
        if not hasattr(self, "_vertices"):
            self.vertices = None
        self._vertices.flip = self.flip
        # Mark as needing vertex update
        self._needVertexUpdate = True

    @property
    def flipHoriz(self):
        return self.flip[0][0]

    @flipHoriz.setter
    def flipHoriz(self, value):
        self.flip = [value, self.flip[0, 1]]

    @property
    def flipVert(self):
        return self.flip[0][1]

    @flipVert.setter
    def flipVert(self, value):
        self.flip = [self.flip[0, 0], value]

    @property
    def anchor(self):
        if hasattr(self, "_vertices"):
            return self._vertices.anchor
        elif hasattr(self, "_anchor"):
            # Return a backup value if there's no vertices yet
            return self._anchor

    @anchor.setter
    def anchor(self, value):
        if hasattr(self, "_vertices"):
            self._vertices.anchor = value
        else:
            # Set a backup value if there's no vertices yet
            self._anchor = value

    def setAnchor(self, value, log=None):
        setAttribute(self, 'anchor', value, log)

    @property
    def units(self):
        if hasattr(self, "_units"):
            return self._units
        else:
            return self.win.units

    @units.setter
    def units(self, value):
        """
        Units to use when drawing.

        Possible options are: None, 'norm', 'cm', 'deg', 'degFlat',
        'degFlatPos', or 'pix'.

        If None then the current units of the
        :class:`~psychopy.visual.Window` will be used.
        See :ref:`units` for explanation of other options.

        Note that when you change units, you don't change the stimulus
        parameters and it is likely to change appearance.

        Example::

            # This stimulus is 20% wide and 50% tall with respect to window
            stim = visual.PatchStim(win, units='norm', size=(0.2, 0.5)

            # This stimulus is 0.2 degrees wide and 0.5 degrees tall.
            stim.units = 'deg'

        """
        if value in unitTypes:
            self._units = value or self.win.units
            self._needVertexUpdate = True
        else:
            raise ValueError(f"Invalid unit type '{value}', must be one of: {unitTypes}")

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
        self._updateListShaders()


class DraggingMixin:
    """
    Mixin to give an object innate dragging behaviour.

    Attributes
    ==========
    draggable : bool
        Can this object be dragged by a Mouse click?
    isDragging : bool
        Is this object currently being dragged? (read only)

    Methods
    ==========
    doDragging :
        Call this each frame to make sure dragging behaviour happens. If
        `autoDraw` and `draggable` are both True, then this will be called
        automatically by the Window object on flip.
    """
    isDragging = False

    def doDragging(self):
        """
        If this stimulus is draggable, do the necessary actions on a frame
        flip to drag it.
        """
        # if not draggable, do nothing
        if not self.draggable:
            return
        # if something else is already dragging, do nothing
        if self.win.currentDraggable is not None and self.win.currentDraggable != self:
            return
        # if just clicked on, start dragging
        self.isDragging = self.isDragging or self.mouse.isPressedIn(self, buttons=[0])
        # if click is released, stop dragging
        self.isDragging = self.isDragging and self.mouse.getPressed()[0]
        # get relative mouse pos
        rel = self.mouse.getRel()

        # if dragging, do necessary updates
        if self.isDragging:
            # set as current draggable
            self.win.currentDraggable = self
            # get own pos in win units
            pos = getattr(self._pos, self.win.units)
            # add mouse movement to pos
            setattr(
                self._pos,
                self.win.units,
                pos + rel
            )
            # set pos
            self.pos = getattr(self._pos, self.units)
        else:
            # remove as current draggable
            self.win.currentDraggable = None

    @attributeSetter
    def draggable(self, value):
        """
        Can this stimulus be dragged by a mouse click?
        """
        # if we don't have reference to a mouse, make one
        if not isinstance(self.mouse, Mouse):
            self.mouse = Mouse(win=self.win)
            # make sure it has an initial pos for rel pos comparisons
            self.mouse.lastPos = self.mouse.getPos()
        # store value
        self.__dict__['draggable'] = value


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
        self.mouse = None
        # self.autoLog is set at end of MinimalStim.__init__
        super(BaseVisualStim, self).__init__(name=name, autoLog=autoLog)
        if self.autoLog:
            msg = ("%s is calling BaseVisualStim.__init__() with autolog=True"
                   ". Set autoLog to True only at the end of __init__())")
            logging.warning(msg % (self.__class__.__name__))

    @property
    def opacity(self):
        """Determines how visible the stimulus is relative to background.

        The value should be a single float ranging 1.0 (opaque) to 0.0
        (transparent). :ref:`Operations <attrib-operations>` are supported.
        Precisely how this is used depends on the :ref:`blendMode`.
        """
        alphas = []
        if hasattr(self, '_foreColor'):
            alphas.append(self._foreColor.alpha)
        if hasattr(self, '_fillColor'):
            alphas.append(self._fillColor.alpha)
        if hasattr(self, '_borderColor'):
            alphas.append(self._borderColor.alpha)
        if alphas:
            return mean(alphas)
        else:
            return 1

    @opacity.setter
    def opacity(self, value):
        # Setting opacity as a single value makes all colours the same opacity
        if value is None:
            # If opacity is set to be None, this indicates that each color should handle its own opacity
            return
        if hasattr(self, '_foreColor'):
            if self._foreColor != None:
                self._foreColor.alpha = value
        if hasattr(self, '_fillColor'):
            if self._fillColor != None:
                self._fillColor.alpha = value
        if hasattr(self, '_borderColor'):
            if self._borderColor != None:
                self._borderColor.alpha = value

    def updateOpacity(self):
        """Placeholder method to update colours when set externally, for example
        updating the `pallette` attribute of a textbox."""
        return

    @attributeSetter
    def ori(self, value):
        """The orientation of the stimulus (in degrees).

        Should be a single value (:ref:`scalar <attrib-scalar>`).
        :ref:`Operations <attrib-operations>` are supported.

        Orientation convention is like a clock: 0 is vertical, and positive
        values rotate clockwise. Beyond 360 and below zero values wrap
        appropriately.

        """
        self.__dict__['ori'] = float(value)
        radians = value * 0.017453292519943295
        sin, cos = numpy.sin, numpy.cos
        self._rotationMatrix = numpy.array([[cos(radians), -sin(radians)],
                                            [sin(radians), cos(radians)]])
        self._needVertexUpdate = True  # need to update update vertices
        self._needUpdate = True

    @property
    def size(self):
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
        return WindowMixin.size.fget(self)

    @size.setter
    def size(self, value):
        # Supply default for None
        if value is None:
            value = Size((1, 1), units="height", win=self.win)
        # Duplicate single values
        if isinstance(value, (float, int)):
            value = (value, value)
        # Do setting
        WindowMixin.size.fset(self, value)
        # Mark any updates needed
        self._needVertexUpdate = True
        self._needUpdate = True
        if hasattr(self, '_calcCyclesPerStim'):
            self._calcCyclesPerStim()

    @property
    def pos(self):
        """
        The position of the center of the stimulus in the stimulus
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
        it like this::

            from psychopy.tools.monitorunittools import posToPix
            posPix = posToPix(stim)

        """
        return WindowMixin.pos.fget(self)

    @pos.setter
    def pos(self, value):
        # Supply defualt for None
        if value is None:
            value = Position((0, 0), units="height", win=self.win)
        # Do setting
        WindowMixin.pos.fset(self, value)
        # Mark any updates needed
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
        # If we have an original size (e.g. for an image or movie), then we CAN set size with None
        useNone = hasattr(self, "origSize")
        # Set attribute
        setAttribute(self, 'size', val2array(newSize, useNone), log, operation)

    def setOri(self, newOri, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'ori', newOri, log, operation)

    def setOpacity(self, newOpacity, operation='', log=None):
        """Hard setter for opacity, allows the suppression of log messages and calls the update method
        """
        if operation in ['', '=']:
            self.opacity = newOpacity
        elif operation in ['+']:
            self.opacity += newOpacity
        elif operation in ['-']:
            self.opacity -= newOpacity
        else:
            logging.error(f"Operation '{operation}' not recognised.")
        # Trigger color update for components like Textbox which have different behaviours for a hard setter
        self.updateOpacity()

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
