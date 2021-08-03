import numpy
from .tools import monitorunittools as tools


# Dict of regexpressions for different formats
unitTypes = [
    None,
    'pix',
    'deg',
    'degFlat',
    'degFlatPos',
    'cm',
    'norm',
    'height',
]


class Vector(object):
    def __init__(self, value, units, win, correctFlat=False):
        # Create a dict to cache values on access
        self._cache = {}
        # Assume invalid until validation happens
        self.valid = False

        self.set(value, units, win, correctFlat)

    def set(self, value, units, win=None, correctFlat=False):
        # Check inputs
        if win is None:
            win = self.win
        # Set extras
        self.win = win
        self.correctFlat = correctFlat
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
        if units is None:
            units = self.win.units
        # Coerce value to a numpy array of floats
        try:
            value = numpy.array(value, dtype=float)
        except ValueError as err:
            self.valid = False
            raise err
        # Make sure it's the right array shape
        if len(value.shape) == 1:
            self.valid = value.shape[0] <= 3
        elif len(value.shape) == 2:
            self.valid = value.shape[1] <= 3
        else:
            self.valid = False
        assert self.valid, "Array of position/size values must be either Nx1, Nx2 or Nx3"

        return value, units

    def __bool__(self):
        return self.valid

    def __repr__(self):
        """If colour is printed, it will display its class and value"""
        if self:
            return f"<psychopy.layout.{self.__class__.__name__}: " + str(self.pix) + "px>"
        else:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + "Invalid" + ">"

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

    def __len__(self):
        """Will return number of dimensions"""
        return self.dimensions

    # ---operations---
    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix + other.pix, "pix")


    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix - other.pix, "pix")

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix * other.pix, "pix")

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.pix / other.pix, "pix")

    def copy(self):
        return self.__class__(self._requested, self._requestedUnits, self.win, self.correctFlat)

    @property
    def monitor(self):
        return self.win.monitor

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
        return numpy.hypot3d(*self.pix)

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
        # Check that object is valid
        assert self.valid, "Could not access pixel value of invalid position/size object"
        # Return cached value if present
        if 'pix' in self._cache:
            return self._cache['pix']

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
        self._cache['deg'] = tools.pix2deg(self.pix, self.monitor, self.correctFlat)
        # Return new cached value
        return self._cache['deg']

    @deg.setter
    def deg(self, value):
        # Validate
        value, units = self.validate(value, 'deg')
        # Convert and set
        self.pix = tools.deg2pix(value, self.monitor, self.correctFlat)

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
            buffer[:, i] /= self.win.size[i] / (self.win.useRetina + 1)
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
            buffer[:, i] *= self.win.size[i] / (self.win.useRetina + 1)
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
    def __init__(self, pos, units, win=None, correctFlat=False):
        Vector.__init__(self, pos, units, win, correctFlat)


class Size(Vector):
    def __init__(self, pos, units, win=None, correctFlat=False):
        Vector.__init__(self, pos, units, win, correctFlat)
