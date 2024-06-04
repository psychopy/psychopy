#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Classes and functions for working with coordinates systems."""

__all__ = [
    "unitTypes",
    "Vector",
    "Position",
    "Size",
    "Vertices"
]

import numpy as np
from .tools import monitorunittools as tools

# list of applicable units
unitTypes = [
    None,
    '',
    'pix',
    'deg',
    'degFlat',
    'degFlatPos',
    'cm',
    'pt',
    'norm',
    'height'
]

# anchor offsets and names
_anchorAliases = {
    'top': -0.5,
    'bottom': 0.5,
    'left': 0.5,
    'right': -0.5,
    'center': 0
}


class Vector:
    """Class representing a vector.

    A vector is a mathematical construct that specifies a length (or magnitude)
    and direction within a given coordinate system. This class provides methods
    to manipulate vectors and convert them between coordinates systems.

    This class may be used to assist in positioning stimuli on a screen.

    Parameters
    ----------
    value : ArrayLike
        Array of vector lengths along each dimension of the space the vector is
        within. Vectors are specified as either 1xN for single vectors, and
        Nx2 or Nx3 for multiple vectors.
    units : str or None
        Units which `value` has been specified in. Applicable values are
        `'pix'`, `'deg'`, `'degFlat'`, `'degFlatPos'`, `'cm'`, `'pt'`, `'norm'`,
        `'height'`, or `None`.
    win : `~psychopy.visual.Window` or None
        Window associated with this vector. This value must be specified if you
        wish to map vectors to coordinate systems that require additional
        information about the monitor the window is being displayed on.

    Examples
    --------
    Create a new vector object using coordinates specified in pixel (`'pix'`)
    units::

        my_vector = Vector([256, 256], 'pix')

    Multiple vectors may be specified by supplying a list of vectors::

        my_vector = Vector([[256, 256], [640, 480]], 'pix')

    Operators can be used to compare the magnitudes of vectors::

        mag_is_same = vec1 == vec2  # same magnitude
        mag_is_greater = vec1 > vec2  # one greater than the other

    1xN vectors return a boolean value while Nx2 or Nx3 arrays return N-length
    arrays of boolean values.

    """
    def __init__(self, value, units, win):
        # Create a dict to cache values on access
        self._cache = {}
        # Assume invalid until validation happens
        self.valid = False

        # define some names used by `set`
        self.win = None
        self._requested = None
        self._requestedUnits = None

        self.set(value, units, win)

    def set(self, value, units, win=None):
        # Check inputs
        if win is None:
            win = self.win

        self.win = win  # set extras

        # If input is a Vector object, duplicate all settings
        if isinstance(value, Vector):
            self._requested = value._requested
            self._requestedUnits = value._requestedUnits
            self.valid = value.valid
            self.pix = value.pix
            if win is None:
                self.win = value.win

            return

        # Validate
        value, units = self.validate(value, units)

        # Set values
        self._requested = value
        self._requestedUnits = units
        setattr(self, self._requestedUnits, self._requested)

    def validate(self, value, units):
        """Validate input values.

        Ensures the values are in the correct format.

        Returns
        -------
        tuple
            Parameters `value` and `units`.

        """
        # Assume valid until shown otherwise
        self.valid = True

        # Check units are valid
        if units not in unitTypes:
            raise ValueError(
                f"Unit type '{units}' not recognised, must be one of: "
                f"{unitTypes}")

        # Get window units if units are None
        if units in (None, ''):
            units = self.win.units

        # Coerce value to a numpy array of floats
        try:
            value = np.array(value, dtype=float)
        except ValueError as err:
            self.valid = False
            raise err

        # Make sure each value is no more than 3D
        if len(value.shape) == 0:
            value = np.array([value, value])
            self.valid = True
        elif len(value.shape) == 1:
            self.valid = value.shape[0] <= 3
        elif len(value.shape) == 2:
            self.valid = value.shape[1] <= 3
            if value.shape[0] == 1:
                # Remove extraneous layer if single value
                value = value[0]
        else:
            self.valid = False

        # Replace None with the matching window dimension
        if (value == None).any() or np.isnan(value).any():  # noqa: E711
            win = Vector((1, 1), units="norm", win=self.win)
            if len(value.shape) == 1:
                value[value == None] = getattr(win, units)[value == None]  # noqa: E711
                value[np.isnan(value)] = getattr(win, units)[np.isnan(value)]
            else:
                value[np.isnan(value[:, 0]), 0] = getattr(win, units)[0]
                value[np.isnan(value[:, 1]), 1] = getattr(win, units)[1]
                value[value[:, 0] == None, 0] = getattr(win, units)[0]  # noqa: E711
                value[value[:, 1] == None, 1] = getattr(win, units)[1]  # noqa: E711

        assert self.valid, (f"Array of position/size values must be either "
                            f"Nx1, Nx2 or Nx3, not {value.shape}")

        return value, units

    def __bool__(self):
        return self.valid

    def __repr__(self):
        """If vector is printed, it will display its class and value."""
        if self:
            return (f"<psychopy.layout.{self.__class__.__name__}: "
                    f"{np.round(self.pix, 3)}px>")
        else:
            return "<psychopy.layout.{self.__class__.__name__}: Invalid>"

    # --------------------------------------------------------------------------
    # Rich comparisons
    #

    def __eq__(self, target):
        """`==` will compare position in pix"""
        if isinstance(target, Vector):
            if self.pix.size > 1:
                return all(self.pix == target.pix)
            else:
                return self.pix == target.pix
        else:
            return False

    def __ne__(self, target):
        """`!=` will return the opposite of `==`"""
        return not self == target

    def __lt__(self, target):
        """`<` will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude < target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude < target
        else:
            return False

    def __le__(self, target):
        """`<=` will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude <= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude <= target
        else:
            return False

    def __gt__(self, target):
        """`>` will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude > target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude > target
        else:
            return False

    def __ge__(self, target):
        """`>=` will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude >= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude >= target
        else:
            return False

    # --------------------------------------------------------------------------
    # Operators
    #

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix + other.pix, "pix", self.win)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix - other.pix, "pix", self.win)

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix * other.pix, "pix", self.win)
        if isinstance(other, (int, float)):
            return Vector(self.pix * other, "pix", self.win)
        if isinstance(other, (list, tuple, np.ndarray)):
            return Vector(self.pix * np.array(other), "pix", self.win)

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix / other.pix, "pix", self.win)
        if isinstance(other, (int, float)):
            return Vector(self.pix / other, "pix", self.win)
        if isinstance(other, (list, tuple, np.ndarray)):
            return Vector(self.pix / np.array(other), "pix", self.win)

    # --------------------------------------------------------------------------
    # Class methods and properties
    #

    def copy(self):
        """Create a copy of this object"""
        return self.__copy__()

    def __copy__(self):
        return self.__deepcopy__()

    def __deepcopy__(self):
        return self.__class__(self._requested, self._requestedUnits, self.win)

    @property
    def monitor(self):
        """The monitor used for calculations within this object
        (`~psychopy.monitors.Monitor`).
        """
        return self.win.monitor

    @property
    def dimensions(self):
        """How many dimensions (x, y, z) are specified?"""
        # Run _requested through validator to sanitise it
        value, units = self.validate(self._requested, self._requestedUnits)

        if len(value.shape) == 1:
            # If single value, return number of coords
            return len(value)
        else:
            # If multi value, return number of columns
            return value.shape[1]

    def __len__(self):
        """How many values are specified?"""
        # Run _requested through validator to sanitise it
        value, units = self.validate(self._requested, self._requestedUnits)

        if len(value.shape) == 1:
            # If single value, return 1
            return 1
        else:
            # If multi value, return number of rows
            return value.shape[0]

    @property
    def magnitude(self):
        """Magnitude of vector (i.e. length of the line from vector to (0, 0)
        in pixels).
        """
        return np.hypot3d(*self.pix)

    @property
    def direction(self):
        """Direction of vector (i.e. angle between vector and the horizontal
        plane).
        """
        if self.dimensions < 2:
            # with only 1 dimension, y is essentially zero, so angle is always 0
            return 0.0

        toReturn = []  # store output values

        if self.dimensions >= 2:
            if self.pix[0] != 0.0:  # Angle from x-axis (y is opp, x is adj)
                x = np.degrees(np.arctan(self.pix[1] / self.pix[0]))
            else:
                x = 90.0

            toReturn.append(x)

            if self.pix[1] != 0.0:  # Angle from y-axis (x is opp, y is adj)
                y = np.degrees(np.arctan(self.pix[0] / self.pix[1]))
            else:
                y = 90.0

            toReturn.append(y)

        if self.dimensions == 3:
            # Angle from z-axis (z is opp, hyp(x,y) is adj)
            if np.hypot3d(*self.pix[:2]) != 0.0:
                u = np.hypot3d(*self.pix[:2])
                z = np.degrees(np.arctan(self.pix[2] / u))
            else:
                z = 90.0

            toReturn.append(z)

        return toReturn

    @property
    def pix(self):
        """Values in units of 'pix' (pixels).
        """
        # Check that object is valid
        assert self.valid, (
            u"Could not access pixel value of invalid position/size object")

        # Return cached value if present
        if 'pix' in self._cache:
            return self._cache['pix']
        else:
            raise AttributeError(
                f"Could not retrieve pixel value of Vector object set in "
                f"{self._requestedUnits}")

    @pix.setter
    def pix(self, value):
        # Validate
        value, units = self.validate(value, 'pix')
        # Clear cache and set
        self._cache = {
            'pix': value
        }

    @property
    def deg(self):
        """Values in units of 'deg' (degrees of visual angle).
        """
        # Return cached value if present
        if 'deg' in self._cache:
            return self._cache['deg']
        # Otherwise, do conversion and cache
        self._cache['deg'] = tools.pix2deg(self.pix, self.monitor)
        # Return new cached value
        return self._cache['deg']

    @deg.setter
    def deg(self, value):
        # Validate
        value, units = self.validate(value, 'deg')
        # Convert and set
        self.pix = tools.deg2pix(value, self.monitor)

    @property
    def degFlat(self):
        """Values in units of 'degFlat' (degrees of visual angle corrected for
        screen curvature).

        When dealing with positions/sizes in isolation; 'deg', 'degFlat' and
        'degFlatPos' are synonymous - as the conversion is done at the vertex
        level.
        """
        return self.deg

    @degFlat.setter
    def degFlat(self, value):
        self.deg = value

    @property
    def degFlatPos(self):
        """Values in units of 'degFlatPos'.

        When dealing with positions/sizes in isolation; 'deg', 'degFlat' and
        'degFlatPos' are synonymous - as the conversion is done at the vertex
        level.
        """
        return self.degFlat

    @degFlatPos.setter
    def degFlatPos(self, value):
        self.degFlat = value

    @property
    def cm(self):
        """Values in units of 'cm' (centimeters).
        """
        # Return cached value if present
        if 'cm' in self._cache:
            return self._cache['cm']
        # Otherwise, do conversion and cache
        self._cache['cm'] = tools.pix2cm(self.pix, self.monitor)
        # Return new cached value
        return self._cache['cm']

    @cm.setter
    def cm(self, value):
        # Validate
        value, units = self.validate(value, 'cm')
        # Convert and set
        self.pix = tools.cm2pix(value, self.monitor)

    @property
    def pt(self):
        """Vector coordinates in 'pt' (points).

        Points are commonly used in print media to define text sizes. One point
        is equivalent to 1/72 inches, or around 0.35 mm.
        """
        # Return cached value if present
        if 'pt' in self._cache:
            return self._cache['pt']
        # Otherwise, do conversion and cache
        self._cache['pt'] = self.cm / (2.54 / 72)
        # Return new cached value
        return self._cache['pt']

    @pt.setter
    def pt(self, value):
        # Validate
        value, units = self.validate(value, 'height')
        # Convert and set
        self.cm = value * (2.54 / 72)

    @property
    def norm(self):
        """Value in units of 'norm' (normalized device coordinates).
        """
        # Return cached value if present
        if 'norm' in self._cache:
            return self._cache['norm']
        # Otherwise, do conversion and cache
        buffer = np.ndarray(self.pix.shape, dtype=float)
        for i in range(self.dimensions):
            u = self.win.useRetina + 1
            if len(self) > 1:
                buffer[:, i] = self.pix[:, i] / (self.win.size[i] / u) * 2
            else:
                buffer[i] = self.pix[i] / (self.win.size[i] / u) * 2

        self._cache['norm'] = buffer

        return self._cache['norm']  # return new cached value

    @norm.setter
    def norm(self, value):
        # Validate
        value, units = self.validate(value, 'norm')

        # Convert and set
        buffer = np.ndarray(value.shape, dtype=float)
        for i in range(self.dimensions):
            u = self.win.useRetina + 1
            if len(self) > 1:
                buffer[:, i] = value[:, i] * (self.win.size[i] / u) / 2
            else:
                buffer[i] = value[i] * (self.win.size[i] / u) / 2

        self.pix = buffer

    @property
    def height(self):
        """Value in units of 'height' (normalized to the height of the window).
        """
        # Return cached value if present
        if 'height' in self._cache:
            return self._cache['height']
        # Otherwise, do conversion and cache
        self._cache['height'] = \
            self.pix / (self.win.size[1] / (self.win.useRetina + 1))
        # Return new cached value
        return self._cache['height']

    @height.setter
    def height(self, value):
        # Validate
        value, units = self.validate(value, 'height')
        # Convert and set
        self.pix = value * (self.win.size[1] / (self.win.useRetina + 1))


class Position(Vector):
    """Class representing a position vector.

    This class is used to specify the location of a point within some
    coordinate system (e.g., `(x, y)`).

    Parameters
    ----------
    value : ArrayLike
        Array of coordinates representing positions within a coordinate system.
        Positions are specified in a similar manner to `~psychopy.layout.Vector`
        as either 1xN for single vectors, and Nx2 or Nx3 for multiple positions.
    units : str or None
        Units which `value` has been specified in. Applicable values are
        `'pix'`, `'deg'`, `'degFlat'`, `'degFlatPos'`, `'cm'`, `'pt'`, `'norm'`,
        `'height'`, or `None`.
    win : `~psychopy.visual.Window` or None
        Window associated with this position. This value must be specified if
        you wish to map positions to coordinate systems that require additional
        information about the monitor the window is being displayed on.

    """
    def __init__(self, value, units, win=None):
        Vector.__init__(self, value, units, win)


class Size(Vector):
    """Class representing a size.

    Parameters
    ----------
    value : ArrayLike
        Array of values representing size axis-aligned bounding box within a
        coordinate system. Sizes are specified in a similar manner to
        `~psychopy.layout.Vector` as either 1xN for single vectors, and Nx2 or
        Nx3 for multiple positions.
    units : str or None
        Units which `value` has been specified in. Applicable values are
        `'pix'`, `'deg'`, `'degFlat'`, `'degFlatPos'`, `'cm'`, `'pt'`, `'norm'`,
        `'height'`, or `None`.
    win : `~psychopy.visual.Window` or None
        Window associated with this size object. This value must be specified if
        you wish to map sizes to coordinate systems that require additional
        information about the monitor the window is being displayed on.

    """
    def __init__(self, value, units, win=None):
        Vector.__init__(self, value, units, win)


class Vertices:
    """Class representing an array of vertices.

    Parameters
    ----------
    verts : ArrayLike
        Array of coordinates specifying the locations of vertices.
    obj : object or None
    size : ArrayLike or None
        Scaling factors for vertices along each dimension.
    pos : ArrayLike or None
        Offset for vertices along each dimension.
    units : str or None
        Units which `verts` has been specified in. Applicable values are
        `'pix'`, `'deg'`, `'degFlat'`, `'degFlatPos'`, `'cm'`, `'pt'`, `'norm'`,
        `'height'`, or `None`.
    flip : ArrayLike or None
        Array of boolean values specifying which dimensions to flip/mirror.
        Mirroring is applied prior to any other transformation.
    anchor : str or None
        Anchor location for vertices, specifies the origin for the vertices.

    """
    def __init__(self, verts, obj=None, size=None, pos=None, units=None,
                 flip=None, anchor=None):

        if obj is None and pos is None and size is None:
            raise ValueError(
                "Vertices array needs either an object or values for pos and "
                "size.")

        # Store object
        self.obj = obj

        # Store size and pos
        self._size = size
        self._pos = pos
        self._units = units
        self.flip = flip  # store flip
        self.anchor = anchor  # set anchor

        # Convert to numpy array
        verts = np.array(verts)

        # Make sure it's coercible to a Nx2 or nxNx2 numpy array
        assert (3 >= len(verts.shape) >= 2) and (verts.shape[-1] == 2), (
            f"Expected vertices to be coercible to a Nx2 or nxNx2 numpy array, not {verts.shape}"
        )

        # Store base vertices
        self.base = verts

    def __repr__(self):
        """If vertices object is printed, it will display its class and value.
        """
        if self:
            return (
                f"<psychopy.layout.{self.__class__.__name__}: "
                f"{np.round(self.base, 3)} * "
                f"{np.round(self.obj._size.pix, 3)} + "
                f"{np.round(self.obj._pos.pix, 3)}>")
        else:
            return "<psychopy.layout.{self.__class__.__name__}: Invalid>"

    @property
    def pos(self):
        """Positional offset of the vertices (`~psychopy.layout.Vector` or
        ArrayLike)."""
        if isinstance(self._pos, Vector):
            return self._pos
        if hasattr(self.obj, "_pos"):
            return self.obj._pos
        else:
            raise AttributeError(
                f"Could not derive position from object {self.obj} as object "
                f"does not have a position attribute.")

    @property
    def size(self):
        """Scaling factors for vertices (`~psychopy.layout.Vector` or
        ArrayLike)."""
        if isinstance(self._size, Vector):
            return self._size
        if hasattr(self.obj, "_size"):
            return self.obj._size
        else:
            raise AttributeError(
                f"Could not derive size from object {self.obj} as object does "
                f"not have a size attribute.")

    @property
    def units(self):
        """Units which the vertices are specified in (`str`).
        """
        if hasattr(self, "_units") and self._units is not None:
            return self._units
        if hasattr(self, "obj") and hasattr(self.obj, "units"):
            return self.obj.units

    @property
    def flip(self):
        """1x2 array for flipping vertices along each axis; set as `True` to
        flip or `False` to not flip (`ArrayLike`).

        If set as a single value, will duplicate across both axes. Accessing the
        protected attribute (`._flip`) will give an array of 1s and -1s with
        which to multiply vertices.
        """
        # Get base value
        if hasattr(self, "_flip"):
            flip = self._flip
        else:
            flip = np.array([[False, False]])
        # Convert from boolean
        return flip == -1

    @flip.setter
    def flip(self, value):
        if value is None:
            value = False

        # Convert to 1x2 numpy array
        value = np.array(value)
        value = np.resize(value, (1, 2))

        # Ensure values were bool
        assert value.dtype == bool, (
            "Flip values must be either a boolean (True/False) or an array of "
            "booleans")

        # Set as multipliers rather than bool
        self._flip = np.array([[
            -1 if value[0, 0] else 1,
            -1 if value[0, 1] else 1,
        ]])
        self._flipHoriz, self._flipVert = self._flip[0]

    @property
    def flipHoriz(self):
        """Apply horizontal mirroring (`bool`)?
        """
        return self.flip[0][0]

    @flipHoriz.setter
    def flipHoriz(self, value):
        self.flip = [value, self.flip[0, 1]]

    @property
    def flipVert(self):
        """Apply vertical mirroring (`bool`)?
        """
        return self.flip[0][1]

    @flipVert.setter
    def flipVert(self, value):
        self.flip = [self.flip[0, 0], value]

    @property
    def anchor(self):
        """Anchor location (`str`).

        Possible values are on of `'top'`, `'bottom'`, `'left'`, `'right'`,
        `'center'`. Combinations of these values may also be specified (e.g.,
        `'top_center'`, `'center-right'`, `'topleft'`, etc. are all valid).
        """
        if hasattr(self, "_anchorX") and hasattr(self, "_anchorY"):
            # If set, return set values
            return self._anchorX, self._anchorY
        if hasattr(self.obj, "anchor"):
            return self.obj.anchor

        # Otherwise, assume center
        return "center", "center"

    @anchor.setter
    def anchor(self, anchor):
        if anchor is None and hasattr(self.obj, "anchor"):
            anchor = self.obj.anchor
        # Set defaults
        self._anchorY = None
        self._anchorX = None
        # Look for unambiguous terms first (top, bottom, left, right)
        if 'top' in str(anchor):
            self._anchorY = 'top'
        elif 'bottom' in str(anchor):
            self._anchorY = 'bottom'
        if 'right' in str(anchor):
            self._anchorX = 'right'
        elif 'left' in str(anchor):
            self._anchorX = 'left'
        # Then 'center' can apply to either axis that isn't already set
        if self._anchorX is None:
            self._anchorX = 'center'
        if self._anchorY is None:
            self._anchorY = 'center'

    @property
    def anchorAdjust(self):
        """Map anchor values to numeric vertices adjustments.
        """
        return [_anchorAliases[a] for a in self.anchor]

    def getas(self, units):
        assert units in unitTypes, f"Unrecognised unit type '{units}'"
        # Start with base values
        verts = self.base.copy()
        verts = verts.astype(float)
        # Apply size
        if self.size is None:
            raise ValueError(
                u"Cannot not calculate absolute positions of vertices without "
                u"a size attribute")
        verts *= getattr(self.size, units)
        # Apply flip
        verts *= self._flip
        # Apply anchor
        verts += self.anchorAdjust * getattr(self.size, units)
        # Apply pos
        if self.pos is None:
            raise ValueError(
                u"Cannot not calculate absolute positions of vertices without "
                u"a pos attribute")
        verts += getattr(self.pos, units)

        return verts

    def setas(self, value, units):
        assert units in unitTypes, f"Unrecognised unit type '{units}'"
        # Enforce numpy
        value = np.array(value, dtype=float)
        # Account for size
        if self.size is None:
            raise ValueError(
                u"Cannot not calculate absolute positions of vertices without "
                u"a size attribute")
        value /= getattr(self.size, units)
        # Account for flip
        value *= self._flip
        # Account for anchor
        value -= self.anchorAdjust * getattr(self.size, units)

        # NOTE: This is commented out because the pos attribute is already used
        # to calculate the absolute position of the vertices during drawing.
        # If we subtract the pos attribute again, the vertices will be offset
        # by the pos attribute twice, and the orientation calculation will be off.

        # # Account for pos
        # if self.pos is None:
        #     raise ValueError(
        #         u"Cannot not calculate absolute positions of vertices without "
        #         u"a pos attribute")
        # value -= getattr(self.pos, units)

        self.base = value  # apply

    @property
    def pix(self):
        """Get absolute positions of vertices in 'pix' units.
        """
        # If correcting for screen curve, use the old functions
        if self.units == 'degFlat':
            return tools._degFlat2pix(
                self.base * self.obj.size, self.obj.pos, self.obj.win)
        elif self.units == 'degFlatPos':
            return tools._degFlatPos2pix(
                self.base * self.obj.size, self.obj.pos, self.obj.win)
        else:
            # Otherwise, use standardised method
            return self.getas('pix')

    @pix.setter
    def pix(self, value):
        self.setas(value, 'pix')

    @property
    def deg(self):
        """Get absolute positions of vertices in 'deg' units.
        """
        return self.getas('deg')

    @deg.setter
    def deg(self, value):
        self.setas(value, 'deg')

    @property
    def degFlat(self):
        """Get absolute positions of vertices in 'degFlat' units.
        """
        return self.getas('degFlat')

    @degFlat.setter
    def degFlat(self, value):
        cm = tools.deg2cm(value, self.obj.win.monitor, correctFlat=True)
        self.setas(cm, 'cm')

    @property
    def cm(self):
        """Get absolute positions of vertices in 'cm' units.
        """
        return self.getas('cm')

    @cm.setter
    def cm(self, value):
        self.setas(value, 'cm')

    @property
    def norm(self):
        """Get absolute positions of vertices in 'norm' units.
        """
        return self.getas('norm')

    @norm.setter
    def norm(self, value):
        self.setas(value, 'norm')

    @property
    def height(self):
        """Get absolute positions of vertices in 'height' units.
        """
        return self.getas('height')

    @height.setter
    def height(self, value):
        self.setas(value, 'height')


if __name__ == "__main__":
    pass
