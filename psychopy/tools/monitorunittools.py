#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to unit conversion respective to a particular
monitor"""

from __future__ import absolute_import, division, print_function

from builtins import str
from past.utils import old_div
from psychopy import monitors
from psychopy import logging
import numpy as np
import re
from numpy import array, sin, cos, tan, pi, radians, hypot, degrees, arctan, abs
from math import hypot as hypot3d

# Maps supported coordinate unit type names to the function that converts
# the given unit type to PsychoPy OpenGL pix unit space.
_unit2PixMappings = dict()

# the following are to be used by convertToPix


def _pix2pix(vertices, pos, win=None):
    return pos + vertices
_unit2PixMappings['pix'] = _pix2pix
_unit2PixMappings['pixels'] = _pix2pix


def _cm2pix(vertices, pos, win):
    return cm2pix(pos + vertices, win.monitor)
_unit2PixMappings['cm'] = _cm2pix


def _deg2pix(vertices, pos, win):
    return deg2pix(pos + vertices, win.monitor)
_unit2PixMappings['deg'] = _deg2pix
_unit2PixMappings['degs'] = _deg2pix


def _degFlatPos2pix(vertices, pos, win):
    posCorrected = deg2pix(pos, win.monitor, correctFlat=True)
    vertices = deg2pix(vertices, win.monitor, correctFlat=False)
    return posCorrected + vertices
_unit2PixMappings['degFlatPos'] = _degFlatPos2pix


def _degFlat2pix(vertices, pos, win):
    return deg2pix(array(pos) + array(vertices), win.monitor,
                   correctFlat=True)
_unit2PixMappings['degFlat'] = _degFlat2pix


def _norm2pix(vertices, pos, win):
    if win.useRetina:
        return (pos + vertices) * win.size / 4.0
    else:
        return (pos + vertices) * win.size / 2.0

_unit2PixMappings['norm'] = _norm2pix


def _height2pix(vertices, pos, win):
    if win.useRetina:
        return (pos + vertices) * win.size[1] / 2.0
    else:
        return (pos + vertices) * win.size[1]

_unit2PixMappings['height'] = _height2pix


def posToPix(stim):
    """Returns the stim's position in pixels,
    based on its pos, units, and win.
    """
    return convertToPix([0, 0], stim.pos, stim.win.units, stim.win)


def convertToPix(vertices, pos, units, win):
    """Takes vertices and position, combines and converts to pixels
    from any unit

    The reason that `pos` and `vertices` are provided separately is that
    it allows the conversion from deg to apply flat-screen correction to
    each separately.

    The reason that these use function args rather than relying on
    self.pos is that some stimuli use other terms (e.g. ElementArrayStim
    uses fieldPos).
    """
    unit2pixFunc = _unit2PixMappings.get(units)
    if unit2pixFunc:
        return unit2pixFunc(vertices, pos, win)
    else:
        msg = "The unit type [{0}] is not registered with PsychoPy"
        raise ValueError(msg.format(units))


def addUnitTypeConversion(unitLabel, mappingFunc):
    """Add support for converting units specified by unit_label to pixels
    to be used by convertToPix (therefore a valid unit for your PsychoPy
    stimuli)

    mapping_func must have the function prototype:

    def mapping_func(vertices, pos, win):
        # Convert the input vertices, pos to pixel positions PsychoPy
        # will use for OpenGL call.

        # unit type -> pixel mapping logic here
        # .....

        return pix
    """
    if unitLabel in _unit2PixMappings:
        msg = "The unit type label [{0}] is already registered with PsychoPy"
        raise ValueError(msg.format(unitLabel))
    _unit2PixMappings[unitLabel] = mappingFunc


# Built in conversion functions follow ...


def cm2deg(cm, monitor, correctFlat=False):
    """Convert size in cm to size in degrees for a given Monitor object
    """
    # check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        msg = ("cm2deg requires a monitors.Monitor object as the second "
               "argument but received %s")
        raise ValueError(msg % str(type(monitor)))
    # get monitor dimensions
    dist = monitor.getDistance()
    # check they all exist
    if dist is None:
        msg = "Monitor %s has no known distance (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if correctFlat:
        return np.degrees(np.arctan(old_div(cm, dist)))
    else:
        return old_div(cm, (dist * 0.017455))


def deg2cm(degrees, monitor, correctFlat=False):
    """Convert size in degrees to size in pixels for a given Monitor object.

    If `correctFlat == False` then the screen will be treated as if all
    points are equal distance from the eye. This means that each "degree"
    will be the same size irrespective of its position.

    If `correctFlat == True` then the `degrees` argument must be an Nx2 matrix
    for X and Y values (the two cannot be calculated separately in this case).

    With `correctFlat == True` the positions may look strange because more
    eccentric vertices will be spaced further apart.
    """
    # check we have a monitor
    if not hasattr(monitor, 'getDistance'):
        msg = ("deg2cm requires a monitors.Monitor object as the second "
               "argument but received %s")
        raise ValueError(msg % str(type(monitor)))
    # get monitor dimensions
    dist = monitor.getDistance()
    # check they all exist
    if dist is None:
        msg = "Monitor %s has no known distance (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if correctFlat:
        rads = radians(degrees)
        cmXY = np.zeros(rads.shape, 'd')  # must be a double (not float)
        if rads.shape == (2,):
            x, y = rads
            cmXY[0] = hypot(dist, tan(y) * dist) * tan(x)
            cmXY[1] = hypot(dist, tan(x) * dist) * tan(y)
        elif len(rads.shape) > 1 and rads.shape[1] == 2:
            cmXY[:, 0] = hypot(dist, tan(rads[:, 1]) * dist) * tan(rads[:, 0])
            cmXY[:, 1] = hypot(dist, tan(rads[:, 0]) * dist) * tan(rads[:, 1])
        else:
            msg = ("If using deg2cm with correctedFlat==True then degrees "
                   "arg must have shape [N,2], not %s")
            raise ValueError(msg % (repr(rads.shape)))
        # derivation:
        #    if hypotY is line from eyeball to [x,0] given by
        #       hypot(dist, tan(degX))
        #    then cmY is distance from [x,0] to [x,y] given by
        #       hypotY * tan(degY)
        #    similar for hypotX to get cmX
        # alternative:
        #    we could do this by converting to polar coords, converting
        #    deg2cm and then going back to cartesian,
        #    but this would be slower(?)
        return cmXY
    else:
        # the size of 1 deg at screen centre
        return np.array(degrees) * dist * 0.017455


def cm2pix(cm, monitor):
    """Convert size in cm to size in pixels for a given Monitor object.
    """
    # check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        msg = ("cm2pix requires a monitors.Monitor object as the"
               " second argument but received %s")
        raise ValueError(msg % str(type(monitor)))
    # get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix is None:
        msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if scrWidthCm is None:
        msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)

    return cm * scrSizePix[0] / float(scrWidthCm)


def pix2cm(pixels, monitor):
    """Convert size in pixels to size in cm for a given Monitor object
    """
    # check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        msg = ("cm2pix requires a monitors.Monitor object as the second"
               " argument but received %s")
        raise ValueError(msg % str(type(monitor)))
    # get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix is None:
        msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if scrWidthCm is None:
        msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    return pixels * float(scrWidthCm) / scrSizePix[0]


def deg2pix(degrees, monitor, correctFlat=False):
    """Convert size in degrees to size in pixels for a given Monitor object
    """
    # get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix is None:
        msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if scrWidthCm is None:
        msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)

    cmSize = deg2cm(degrees, monitor, correctFlat)
    return cmSize * scrSizePix[0] / float(scrWidthCm)


def pix2deg(pixels, monitor, correctFlat=False):
    """Convert size in pixels to size in degrees for a given Monitor object
    """
    # get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix is None:
        msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if scrWidthCm is None:
        msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    cmSize = pixels * float(scrWidthCm) / scrSizePix[0]
    return cm2deg(cmSize, monitor, correctFlat)

class DummyMonitor(object):
    def getDistance(self):
        return 50
    def getSizePix(self):
        return (1920, 1080)
    def getWidth(self):
        return 50

class DummyWin(object):
    @property
    def size(self):
        return (1920, 1080, 1000)
    @property
    def useRetina(self):
        return False

# Shorthand for common regexpressions
_lbr = r'[\[\(]\s*'
_rbr = r'\s*[\]\)]'
_float = r'\d*.?\d*?'
_int = r'\d*(.0*)?'
_360 = r'(\d|\d\d|[12]\d\d|3[0-5]\d|360).?\d*?'
# Dict of regexpressions for different formats
vectorSpaces = {
    'pix': re.compile(_lbr+r'('+r'\-?'+_int+r',\s*'+r')*'+r'\-?'+_int+_rbr),
    'deg': re.compile(_lbr+r'('+r'\-?'+_360+r',\s*'+r')*'+r'\-?'+_360+_rbr),
    'cm': re.compile(_lbr+r'('+r'\-?'+_float+r',\s*'+r')*'+r'\-?'+_float+_rbr),
    'norm': re.compile(_lbr+r'('+r'\-?'+_float+r',\s*'+r')*'+r'\-?'+_float+_rbr),
    'height': re.compile(_lbr+r'('+r'\-?'+_float+r',\s*'+r')*'+r'\-?'+_float+_rbr),
}

class Vector(object):
    def __init__(self, pos, units, win=None, monitor=None, correctFlat=False):
        self.set(pos, units, win, monitor, correctFlat)
        # if not isinstance(monitor, monitors.Monitor):
        #     msg = ("Vertex calculation requires a monitors.Monitor object as the second "
        #            "argument but received %s")
        #     raise ValueError(msg % str(type(monitor)))
        # if not monitor.getSizePix():
        #     msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        #     raise ValueError(msg % self.monitor.name)
        # if not monitor.getWidth():
        #     msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        #     raise ValueError(msg % self.monitor.name)
        # if self.monitor.getDistance() is None:
        #     msg = "Monitor %s has no known distance (SEE MONITOR CENTER)"
        #     raise ValueError(msg % self.monitor.name)


    def set(self, pos, units=None, win=None, monitor=None, correctFlat=False):
        # If input is a Vector object, duplicate all settings
        if isinstance(pos, type(self)):
            pos = getattr(pos, pos._requestedUnits)
            units = pos._requestedUnits
            win = pos.win
            monitor = pos.monitor
            correctFlat = pos.correctFlat
        # Require units spec
        if units not in vectorSpaces:
            logging.warning("Not units found. Please specify units for Vector object, or supply set command with an instance of "+type(self).__name__)
            return
        # Set values
        self._requested = pos
        self._requestedUnits = units
        self._franca = None

        self.win = win
        self.monitor = monitor
        self.correctFlat = correctFlat

        setattr(self, self._requestedUnits, self._requested)

    def __repr__(self):
        """If colour is printed, it will display its class and value"""
        if self.pix:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + str(self.pix) + ">"
        else:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + "Invalid" + ">"
    #--rich comparisons---
    def __eq__(self, target):
        """== will compare position in pix"""
        if isinstance(target, type(self)):
            return self.pix == target.pix
        elif isinstance(target, (list, tuple)):
            # If input is a list or tuple, compare values against each space
            for space in vectorSpaces:
                if getattr(self, space) == tuple(target):
                    return True
        else:
            return False
    def __ne__(self, target):
        """!= will return the opposite of =="""
        return not self == target
    def __lt__(self, target):
        """< will compare magnitude"""
        if isinstance(target, type(self)):
            return self.magnitude < target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude < target
        else:
            return False
    def __le__(self, target):
        """<= will compare magnitude"""
        if isinstance(target, type(self)):
            return self.magnitude <= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude <= target
        else:
            return False
    def __gt__(self, target):
        """> will compare magnitude"""
        if isinstance(target, type(self)):
            return self.magnitude > target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude > target
        else:
            return False
    def __ge__(self, target):
        """>= will compare magnitude"""
        if isinstance(target, type(self)):
            return self.magnitude >= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude >= target
        else:
            return False
    def __len__(self):
        """Will return number of dimensions"""
        return self.dimensions

    # ---operations---
    def _canOperate(self, other):
        if isinstance(other, type(self)):
            # If operating with a Vector
            if not self.pix and other.pix:
                raise ValueError("Vector operation could not be performed as one or both Vectors have a value of None")
            if not self.win == other.win \
                    or not self.monitor == other.monitor \
                    or not self.correctFlat == other.correctFlat:
                raise ValueError(
                    "Vectors must share the same window, monitor and correctFlat setting to operate upon one another")
            if not self.dimensions == other.dimensions:
                raise ValueError("Vectors must have the same number of dimensions in order to operate upon one another")
            # If no errors hit, return True
            return True
        else:
            raise TypeError("unsupported operand type(s) for -: '"+type(self).__name__+"' and '"+type(other).__name__+"'")

    def __add__(self, other):
        if isinstance(other, (int, float)):
            out = self.copy()
            out.magnitude += other
            return out
        if self._canOperate(other):
            return Vector(tuple(self.pix[i]+other.pix[i] for i in range(self.dimensions)),
                          'pix', win=self.win, monitor=self.monitor, correctFlat=self.correctFlat)
    def __sub__(self, other):
        if isinstance(other, (int, float)):
            out = self.copy()
            out.magnitude -= other
            return out
        if self._canOperate(other):
            return Vector(tuple(self.pix[i]-other.pix[i] for i in range(self.dimensions)),
                            'pix', win=self.win, monitor=self.monitor, correctFlat=self.correctFlat)
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            out = self.copy()
            out.magnitude *= other
            return out
        if self._canOperate(other):
            return Vector(tuple(self.pix[i]*other.pix[i] for i in range(self.dimensions)),
                          'pix', win=self.win, monitor=self.monitor, correctFlat=self.correctFlat)
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            out = self.copy()
            out.magnitude /= other
            return out
        if self._canOperate(other):
            return Vector(tuple(self.pix[i]/other.pix[i] for i in range(self.dimensions)),
                          'pix', win=self.win, monitor=self.monitor, correctFlat=self.correctFlat)

    def copy(self):
        return self.__class__(self._requested, self._requestedUnits, self.win, self.monitor, self.correctFlat)

    def validate(self, pos, against=None, set=False):
        # If not checking against anything, check against everything
        if not against:
            against = list(vectorSpaces)
        if not isinstance(against, (list, tuple)):
            against = [against]
        # Do validation
        for space in against:
            # Convert from str if needed
            if isinstance(pos, str) and space in ['pix', 'deg', 'cm', 'norm', 'height']:
                pos = [float(n) for n in pos.strip('[]()').split(',')]
            # If supplied with a single value, add braces
            if isinstance(pos, (int, float)):
                pos = (pos,)
            # Enforce int for int-only spaces
            if space in ['pix']:
                pos = [int(p) for p in pos]
            # Enforce tuple
            if isinstance(pos, (list, np.ndarray)):
                pos = tuple(pos)
            # If None, default to 0
            if pos == None:
                pos = (0,0)
            if vectorSpaces[space].fullmatch('('+ ', '.join([f'{pos[i]:.20f}' for i in range(self.dimensions)]) +')'):
                # Check for monitor if needed
                if space in ['deg', 'cm']:
                    if set and not self.monitor:
                        msg = "Vector cannot be specified in " + space + " with no monitor specified."
                        logging.error(msg)
                        raise NameError(msg)
                    elif not self.monitor:
                        logging.warning("Vector could not be calculated in " + space + " with no monitor specified.")
                        return None
                # Check for window if needed
                if space in ['norm', 'height']:
                    if set and not self.win:
                        msg = "Vector cannot be specified in " + space + " with no window specified."
                        logging.error(msg)
                        raise NameError(msg)
                    elif not self.monitor:
                        logging.warning("Vector could not be calculated in " + space + " with no window specified.")
                        return None

                # If it makes it this far, pos is valid
                return pos

    @property
    def dimensions(self):
        if isinstance(self._requested, (list, tuple, np.ndarray)):
            return len(self._requested)
        elif isinstance(self._requested, (int, float, type(None))):
            return 1
    @dimensions.setter
    def dimensions(self, value):
        # Check that there aren't more dimensions than the window has (assume 3 if no window is set)
        if hasattr(self, 'win'):
            maxdim = len(self.win.size)
        else:
            maxdim = 3
        if value > maxdim:
            raise ValueError("Vector has more dimensions than are supported by the window")

        # Adjust values to fit if dimensions is set manually
        if value > len(self.pix):
            self.pix = self.pix + (0,)*(value - self.pix)
        if value < len(self.pix):
            self.pix = self.pix[:value]

    @property
    def magnitude(self):
        """Return magnitude of vector (i.e. length of the line from vector to (0,0) in pixels)"""
        return hypot3d(*self.pix)
    @magnitude.setter
    def magnitude(self, value):
        """Extend Vector in current direction"""
        # Divide by current magnitude
        root = tuple(p/self.magnitude if self.magnitude else 0 for p in self.pix)
        self.pix = tuple(r*value for r in root)

    @property
    def direction(self):
        """Return direction of vector (i.e. angle between vector and the horizontal plane"""
        deg = []
        if self.dimensions < 2:
            return 0 # With only 1 dimension, y is essentially zero, so angle is always 0
        if self.dimensions == 2:
            x = degrees(arctan(self.pix[1]/self.pix[0])) if self.pix[0] != 0 else 90 # Angle from x axis (y is opp, x is adj)
            y = degrees(arctan(self.pix[0]/self.pix[1])) if self.pix[1] != 0 else 90 # Angle from y axis (x is opp, y is adj)
            return (x, y)
        if self.dimensions == 3:
            x = degrees(arctan(self.pix[1]/self.pix[0])) if self.pix[0] != 0 else 90 # Angle from x axis (y is opp, x is adj)
            y = degrees(arctan(self.pix[0]/self.pix[1])) if self.pix[1] != 0 else 90 # Angle from y axis (x is opp, y is adj)
            z = degrees(arctan(self.pix[2]/hypot3d(*self.pix[:2]))) if hypot3d(*self.pix[:2]) != 0 else 90 # Angle from z axis (z is opp, hyp(x,y) is adj)
            return (x,y,z)

    @property
    def pix(self):
        return self._franca

    @pix.setter
    def pix(self, value):
        # Validate
        value = self.validate(value, 'pix', True)
        if not value:
            return

        self._franca = value

    @property
    def deg(self):
        """Convert size in pixels to size in degrees for a given Monitor object
        """
        # get monitor dimensions
        dist = self.monitor.getDistance()
        if self.correctFlat:
            #return np.degrees(np.arctan(old_div(self.cm, dist)))
            return tuple((c*360)/(pi*dist**2) for c in self.cm)
        else:
            return tuple(arctan(c/(2*dist))*2 for c in self.cm)
    @deg.setter
    def deg(self, value):
        """Convert size in degrees to size in pixels for a given Monitor object.

        If `correctFlat == False` then the screen will be treated as if all
        points are equal distance from the eye. This means that each "degree"
        will be the same size irrespective of its position.

        If `correctFlat == True` then the `degrees` argument must be an Nx2 matrix
        for X and Y values (the two cannot be calculated separately in this case).

        With `correctFlat == True` the positions may look strange because more
        eccentric vertices will be spaced further apart.
        """
        # Validate
        value = self.validate(value, 'deg', True)
        if not value:
            return

        # get monitor dimensions
        dist = self.monitor.getDistance()

        if self.correctFlat:
            self.cm = tuple(dist**2 * pi * c / 360 for c in value)
            # rads = tuple(radians(c) for c in value)
            # cmXY = np.zeros(rads.shape, 'd')  # must be a double (not float)
            # if rads.shape == (2,):
            #     x, y = rads
            #     cmXY[0] = hypot(dist, tan(y) * dist) * tan(x)
            #     cmXY[1] = hypot(dist, tan(x) * dist) * tan(y)
            # elif len(rads.shape) > 1 and rads.shape[1] == 2:
            #     cmXY[:, 0] = hypot(dist, tan(rads[:, 1]) * dist) * tan(rads[:, 0])
            #     cmXY[:, 1] = hypot(dist, tan(rads[:, 0]) * dist) * tan(rads[:, 1])
            # else:
            #     msg = ("If using deg2cm with correctedFlat==True then degrees "
            #            "arg must have shape [N,2], not %s")
            #     raise ValueError(msg % (repr(rads.shape)))
            # self.cm = cmXY
        else:
            self.cm = tuple(tan(c/2) * dist*2 for c in value)

    @property
    def cm(self):
        """Convert size in pixels to size in cm for a given Monitor object
        """
        # get monitor params and raise error if necess
        cmRatio = self.monitor.getWidth() / self.monitor.getSizePix()[0]
        return tuple(c * cmRatio for c in self.pix)

    @cm.setter
    def cm(self, value):
        # Validate
        value = self.validate(value, 'cm', True)
        if not value:
            return

        # get monitor params and raise error if necess
        cmRatio = self.monitor.getSizePix()[0] / self.monitor.getWidth()
        self.pix = tuple(c * cmRatio for c in value)

    @property
    def norm(self):
        if self.win.useRetina:
            return tuple(
                self.pix[i] * 2.0 / self.win.size[i]
                for i in range(self.dimensions)
            )
        else:
            return tuple(
                self.pix[i] / self.win.size[i]
                for i in range(self.dimensions)
            )
    @norm.setter
    def norm(self, value):
        # Validate
        value = self.validate(value, 'norm', True)
        if not value:
            return

        if self.win.useRetina:
            self.pix = tuple(
                value[i] * self.win.size[i] / 2.0
                for i in range(self.dimensions)
            )
        else:
            self.pix = tuple(
                value[i] * self.win.size[i]
                for i in range(self.dimensions)
            )

    @property
    def height(self):
        if self.win.useRetina:
            return tuple(c * 2.0 / self.win.size[1] for c in self.pix)
        else:
            return tuple(c / self.win.size[1] for c in self.pix)

    @height.setter
    def height(self, value):
        # Validate
        value = self.validate(value, 'height', True)
        if not value:
            return

        if self.win.useRetina:
            self.pix = tuple(self.win.size[1] * c / 2.0 for c in value)
        else:
            self.pix = tuple(self.win.size[1] * c for c in value)

class Coordinate(Vector):
    def __init__(self, pos, units, win=None, monitor=None, correctFlat=False):
        Vector.__init__(self, pos, units, win, monitor, correctFlat)

class Size(Vector):
    def __init__(self, pos, units, win=None, monitor=None, correctFlat=False):
        Vector.__init__(self, pos, units, win, monitor, correctFlat)