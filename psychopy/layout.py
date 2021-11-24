import numpy
from .tools import monitorunittools as tools


# Dict of regexpressions for different formats
unitTypes = [
    None,
    '',
    'pix',
    'deg',
    'degFlat',
    'degFlatPos',
    'cm',
    'norm',
    'height',
]


class Vector(object):
    def __init__(self, value, units, win):
        # Create a dict to cache values on access
        self._cache = {}
        # Assume invalid until validation happens
        self.valid = False

        self.set(value, units, win)

    def set(self, value, units, win=None):
        # Check inputs
        if win is None:
            win = self.win
        # Set extras
        self.win = win
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
        # Assume valid until shown otherwise
        self.valid = True
        # Check units are valid
        if units not in unitTypes:
            raise ValueError(f"Unit type '{units}' not recognised, must be one of: {unitTypes}")
        # Get window units if units are None
        if units in (None, ''):
            units = self.win.units
        # Coerce value to a numpy array of floats
        try:
            value = numpy.array(value, dtype=float)
        except ValueError as err:
            self.valid = False
            raise err
        # Make sure each value is no more than 3D
        if len(value.shape) == 0:
            value = numpy.array([value, value])
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
        if (value == None).any() or numpy.isnan(value).any():
            win = Vector((1, 1), units="norm", win=self.win)
            if len(value.shape) == 1:
                value[0] = getattr(win, units)[0]
                value[1] = getattr(win, units)[1]
            else:
                value[value[:, 0] == None, 0] = getattr(win, units)[0]
                value[value[:, 1] == None, 1] = getattr(win, units)[1]
        assert self.valid, f"Array of position/size values must be either Nx1, Nx2 or Nx3, not {value.shape}"

        return value, units

    def __bool__(self):
        return self.valid

    def __repr__(self):
        """If vector is printed, it will display its class and value"""
        if self:
            return f"<psychopy.layout.{self.__class__.__name__}: {numpy.round(self.pix, 3)}px>"
        else:
            return "<psychopy.layout.{self.__class__.__name__}: Invalid>"

    #--rich comparisons---
    def __eq__(self, target):
        """== will compare position in pix"""
        if isinstance(target, Vector):
            return self.pix == target.pix
        else:
            return False

    def __ne__(self, target):
        """!= will return the opposite of =="""
        return not self == target

    def __lt__(self, target):
        """< will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude < target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude < target
        else:
            return False

    def __le__(self, target):
        """<= will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude <= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude <= target
        else:
            return False

    def __gt__(self, target):
        """> will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude > target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude > target
        else:
            return False

    def __ge__(self, target):
        """>= will compare magnitude"""
        if isinstance(target, Vector):
            return self.magnitude >= target.magnitude
        elif isinstance(target, (int, float)):
            return self.magnitude >= target
        else:
            return False

    # ---operations---
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
        if isinstance(other, (list, tuple, numpy.ndarray)):
            return Vector(self.pix * numpy.array(other), "pix", self.win)

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix / other.pix, "pix", self.win)
        if isinstance(other, (int, float)):
            return Vector(self.pix / other, "pix", self.win)
        if isinstance(other, (list, tuple, numpy.ndarray)):
            return Vector(self.pix / numpy.array(other), "pix", self.win)

    def copy(self):
        """Create a copy of this object"""
        return self.__class__(self._requested, self._requestedUnits, self.win)

    @property
    def monitor(self):
        """The monitor used for calculations within this object"""
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
        """How many different values are specified?"""
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
        """Return magnitude of vector (i.e. length of the line from vector to (0,0) in pixels) (WIP)"""
        return numpy.hypot3d(*self.pix)

    @property
    def direction(self):
        """Return direction of vector (i.e. angle between vector and the horizontal plane (WIP)"""
        deg = []
        if self.dimensions < 2:
            return 0 # With only 1 dimension, y is essentially zero, so angle is always 0
        if self.dimensions == 2:
            x = numpy.degrees(numpy.arctan(self.pix[1]/self.pix[0])) if self.pix[0] != 0 else 90 # Angle from x axis (y is opp, x is adj)
            y = numpy.degrees(numpy.arctan(self.pix[0]/self.pix[1])) if self.pix[1] != 0 else 90 # Angle from y axis (x is opp, y is adj)
            return (x, y)
        if self.dimensions == 3:
            x = numpy.degrees(numpy.arctan(self.pix[1]/self.pix[0])) if self.pix[0] != 0 else 90 # Angle from x axis (y is opp, x is adj)
            y = numpy.degrees(numpy.arctan(self.pix[0]/self.pix[1])) if self.pix[1] != 0 else 90 # Angle from y axis (x is opp, y is adj)
            z = numpy.degrees(numpy.arctan(self.pix[2]/numpy.hypot3d(*self.pix[:2]))) if numpy.hypot3d(*self.pix[:2]) != 0 else 90 # Angle from z axis (z is opp, hyp(x,y) is adj)
            return (x,y,z)

    @property
    def pix(self):
        """

        """
        # Check that object is valid
        assert self.valid, "Could not access pixel value of invalid position/size object"
        # Return cached value if present
        if 'pix' in self._cache:
            return self._cache['pix']
        else:
            raise AttributeError(f"Could not retrieve pixel value of Vector object set in {self._requestedUnits}")

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
        """

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
        """
        When dealing with positions/sizes in isolation; deg, degFlat and degFlatPos are synonymous - as the conversion is done at the vertex level.
        """
        return self.deg

    @degFlat.setter
    def degFlat(self, value):
        self.deg = value

    @property
    def degFlatPos(self):
        """
        When dealing with positions/sizes in isolation; deg, degFlat and degFlatPos are synonymous - as the conversion is done at the vertex level.
        """
        return self.degFlat

    @degFlatPos.setter
    def degFlatPos(self, value):
        self.degFlat = value

    @property
    def cm(self):
        """

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
    def norm(self):
        """

        """
        # Return cached value if present
        if 'norm' in self._cache:
            return self._cache['norm']
        # Otherwise, do conversion and cache
        buffer = numpy.ndarray(self.pix.shape, dtype=float)
        for i in range(self.dimensions):
            if len(self) > 1:
                buffer[:, i] = self.pix[:, i] / (self.win.size[i] / (self.win.useRetina + 1)) * 2
            else:
                buffer[i] = self.pix[i] / (self.win.size[i] / (self.win.useRetina + 1)) * 2
        self._cache['norm'] = buffer
        # Return new cached value
        return self._cache['norm']

    @norm.setter
    def norm(self, value):
        # Validate
        value, units = self.validate(value, 'norm')
        # Convert and set
        buffer = numpy.ndarray(value.shape, dtype=float)
        for i in range(self.dimensions):
            if len(self) > 1:
                buffer[:, i] = value[:, i] * (self.win.size[i] / (self.win.useRetina + 1)) / 2
            else:
                buffer[i] = value[i] * (self.win.size[i] / (self.win.useRetina + 1)) / 2
        self.pix = buffer

    @property
    def height(self):
        """

        """
        # Return cached value if present
        if 'height' in self._cache:
            return self._cache['height']
        # Otherwise, do conversion and cache
        self._cache['height'] = self.pix / (self.win.size[1] / (self.win.useRetina + 1))
        # Return new cached value
        return self._cache['height']

    @height.setter
    def height(self, value):
        # Validate
        value, units = self.validate(value, 'height')
        # Convert and set
        self.pix = value * (self.win.size[1] / (self.win.useRetina + 1))


class Position(Vector):
    def __init__(self, value, units, win=None):
        Vector.__init__(self, value, units, win)


class Size(Vector):
    def __init__(self, value, units, win=None):
        Vector.__init__(self, value, units, win)


class Vertices(object):
    def __init__(self, verts, obj=None, size=None, pos=None, flip=None, anchor=None):
        if obj is None and pos is None and size is None:
            raise ValueError("Vertices array needs either an object or values for pos and size.")
        # Store object
        self.obj = obj
        # Store size and pos
        self._size = size
        self._pos = pos
        # Store flip
        self.flip = flip
        # Set anchor
        self.anchor = anchor
        # Convert to numpy array
        verts = numpy.array(verts)
        # Make sure it's coercible to a Nx2 numpy array
        assert len(verts.shape) == 2, "Vertices must be coercible to a Nx2 numpy array"
        assert verts.shape[1] == 2, "Vertices must be coercible to a Nx2 numpy array"
        # Store base vertices
        self.base = verts

    def __repr__(self):
        """If vertices object is printed, it will display its class and value"""
        if self:
            return f"<psychopy.layout.{self.__class__.__name__}: {numpy.round(self.base, 3)} * {numpy.round(self.obj._size.pix, 3)} + {numpy.round(self.obj._pos.pix, 3)}>"
        else:
            return "<psychopy.layout.{self.__class__.__name__}: Invalid>"

    @property
    def pos(self):
        if isinstance(self._pos, Vector):
            return self._pos
        if hasattr(self.obj, "_pos"):
            return self.obj._pos
        else:
            raise AttributeError(f"Could not derive position from object {self.obj} as object does not have a "
                                 f"position attribute.")

    @property
    def size(self):
        if isinstance(self._size, Vector):
            return self._size
        if hasattr(self.obj, "_size"):
            return self.obj._size
        else:
            raise AttributeError(f"Could not derive size from object {self.obj} as object does not have a "
                                 f"size attribute.")

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
        """anchor is a string of terms, top, bottom, left, right, center

        e.g. 'top_center', 'center-right', 'topleft', 'center' are all valid"""
        if hasattr(self, "_anchorX") and hasattr(self, "_anchorY"):
            # If set, return set values
            return (self._anchorX, self._anchorY)
        else:
            # Otherwise, assume center
            return ("center", "center")

    @anchor.setter
    def anchor(self, anchor):
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
        """
        Map anchor values to numeric vertices adjustments
        """
        anchorAliases = {
            'top': -0.5,
            'bottom': 0.5,
            'left': 0.5,
            'right': -0.5,
            'center': 0,
        }
        return [anchorAliases[a] for a in self.anchor]

    def getas(self, units):
        assert units in unitTypes, f"Unrecognised unit type '{units}'"
        # Start with base values
        verts = self.base.copy()
        # Apply anchor
        verts += self.anchorAdjust
        # Apply size
        if self.size is None:
            raise ValueError("Cannot not calculate absolute positions of vertices without a size attribute")
        verts *= getattr(self.size, units)
        # Apply flip
        verts *= self._flip
        # Apply pos
        if self.pos is None:
            raise ValueError("Cannot not calculate absolute positions of vertices without a pos attribute")
        verts += getattr(self.pos, units)

        return verts

    def setas(self, value, units):
        assert units in unitTypes, f"Unrecognised unit type '{units}'"
        # Enforce numpy
        value = numpy.array(value, dtype=float)
        # Account for size
        if self.size is None:
            raise ValueError("Cannot not calculate absolute positions of vertices without a size attribute")
        value /= getattr(self.size, units)
        # Account for flip
        value *= self._flip
        # Account for pos
        if self.pos is None:
            raise ValueError("Cannot not calculate absolute positions of vertices without a pos attribute")
        value -= getattr(self.pos, units)
        # Apply
        self.base = value

    @property
    def pix(self):
        """
        Get absolute positions of vertices in pix units
        """
        # If correcting for screen curve, use the old functions
        if self.obj.units == 'degFlat':
            return tools._degFlat2pix(self.base * self.obj.size, self.obj.pos, self.obj.win)
        elif self.obj.units == 'degFlatPos':
            return tools._degFlatPos2pix(self.base * self.obj.size, self.obj.pos, self.obj.win)
        else:
            # Otherwise, use standardised method
            return self.getas('pix')

    @pix.setter
    def pix(self, value):
        self.setas(value, 'pix')

    @property
    def deg(self):
        """
        Get absolute positions of vertices in deg units
        """
        return self.getas('deg')

    @deg.setter
    def deg(self, value):
        self.setas(value, 'deg')

    @property
    def degFlat(self):
        return self.getas('degFlat')

    @degFlat.setter
    def degFlat(self, value):
        cm = tools.deg2cm(value, self.obj.win.monitor, correctFlat=True)
        self.setas(cm, 'cm')

    @property
    def cm(self):
        """
        Get absolute positions of vertices in cm units
        """
        return self.getas('cm')

    @cm.setter
    def cm(self, value):
        self.setas(value, 'cm')

    @property
    def norm(self):
        """
        Get absolute positions of vertices in norm units
        """
        return self.getas('norm')

    @norm.setter
    def norm(self, value):
        self.setas(value, 'norm')

    @property
    def height(self):
        """
        Get absolute positions of vertices in height units
        """
        return self.getas('height')

    @height.setter
    def height(self, value):
        self.setas(value, 'height')
