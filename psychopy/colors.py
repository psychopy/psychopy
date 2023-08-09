#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for working with colors.
"""

__all__ = [
    "colorExamples",
    "colorNames",
    "colorSpaces",
    "isValidColor",
    "hex2rgb255",
    "Color"
]

import re
from math import inf
from psychopy import logging
import psychopy.tools.colorspacetools as ct
from psychopy.tools.mathtools import infrange
import numpy as np


# Dict of examples of Psychopy Red at 12% opacity in different formats
colorExamples = {
    'named': 'crimson',
    'hex': '#F2545B',
    'hexa': '#F2545B1E',
    'rgb': (0.89, -0.35, -0.28),
    'rgba': (0.89, -0.35, -0.28, -0.76),
    'rgb1': (0.95, 0.32, 0.36),
    'rgba1': (0.95, 0.32, 0.36, 0.12),
    'rgb255': (242, 84, 91),
    'rgba255': (242, 84, 91, 30),
    'hsv': (357, 0.65, 0.95),
    'hsva': (357, 0.65, 0.95, 0.12),
}

# Dict of named colours
colorNames = {
    "none": (0, 0, 0, 0),
    "transparent": (0, 0, 0, 0),
    "aliceblue": (0.882352941176471, 0.945098039215686, 1),
    "antiquewhite": (0.96078431372549, 0.843137254901961, 0.686274509803922),
    "aqua": (-1, 1, 1),
    "aquamarine": (-0.00392156862745097, 1, 0.662745098039216),
    "azure": (0.882352941176471, 1, 1),
    "beige": (0.92156862745098, 0.92156862745098, 0.725490196078431),
    "bisque": (1, 0.788235294117647, 0.537254901960784),
    "black": (-1, -1, -1),
    "blanchedalmond": (1, 0.843137254901961, 0.607843137254902),
    "blue": (-1, -1, 1),
    "blueviolet": (0.0823529411764705, -0.662745098039216, 0.772549019607843),
    "brown": (0.294117647058824, -0.670588235294118, -0.670588235294118),
    "burlywood": (0.741176470588235, 0.443137254901961, 0.0588235294117647),
    "cadetblue": (-0.254901960784314, 0.23921568627451, 0.254901960784314),
    "chartreuse": (-0.00392156862745097, 1, -1),
    "chestnut": (0.607843137254902, -0.27843137254902, -0.27843137254902),
    "chocolate": (0.647058823529412, -0.176470588235294, -0.764705882352941),
    "coral": (1, -0.00392156862745097, -0.372549019607843),
    "cornflowerblue": (-0.215686274509804, 0.168627450980392, 0.858823529411765),
    "cornsilk": (1, 0.945098039215686, 0.725490196078431),
    "crimson": (0.725490196078431, -0.843137254901961, -0.529411764705882),
    "cyan": (-1, 1, 1),
    "darkblue": (-1, -1, 0.0901960784313725),
    "darkcyan": (-1, 0.0901960784313725, 0.0901960784313725),
    "darkgoldenrod": (0.443137254901961, 0.0509803921568628, -0.913725490196078),
    "darkgray": (0.325490196078431, 0.325490196078431, 0.325490196078431),
    "darkgreen": (-1, -0.215686274509804, -1),
    "darkgrey": (0.325490196078431, 0.325490196078431, 0.325490196078431),
    "darkkhaki": (0.482352941176471, 0.435294117647059, -0.16078431372549),
    "darkmagenta": (0.0901960784313725, -1, 0.0901960784313725),
    "darkolivegreen": (-0.333333333333333, -0.16078431372549, -0.631372549019608),
    "darkorange": (1, 0.0980392156862746, -1),
    "darkorchid": (0.2, -0.607843137254902, 0.6),
    "darkred": (0.0901960784313725, -1, -1),
    "darksalmon": (0.827450980392157, 0.176470588235294, -0.0431372549019607),
    "darkseagreen": (0.12156862745098, 0.474509803921569, 0.12156862745098),
    "darkslateblue": (-0.435294117647059, -0.52156862745098, 0.0901960784313725),
    "darkslategray": (-0.631372549019608, -0.380392156862745, -0.380392156862745),
    "darkslategrey": (-0.631372549019608, -0.380392156862745, -0.380392156862745),
    "darkturquoise": (-1, 0.615686274509804, 0.63921568627451),
    "darkviolet": (0.16078431372549, -1, 0.654901960784314),
    "deeppink": (1, -0.843137254901961, 0.152941176470588),
    "deepskyblue": (-1, 0.498039215686275, 1),
    "dimgray": (-0.176470588235294, -0.176470588235294, -0.176470588235294),
    "dimgrey": (-0.176470588235294, -0.176470588235294, -0.176470588235294),
    "dodgerblue": (-0.764705882352941, 0.129411764705882, 1),
    "firebrick": (0.396078431372549, -0.733333333333333, -0.733333333333333),
    "floralwhite": (1, 0.96078431372549, 0.882352941176471),
    "forestgreen": (-0.733333333333333, 0.0901960784313725, -0.733333333333333),
    "fuchsia": (1, -1, 1),
    "gainsboro": (0.725490196078431, 0.725490196078431, 0.725490196078431),
    "ghostwhite": (0.945098039215686, 0.945098039215686, 1),
    "gold": (1, 0.686274509803922, -1),
    "goldenrod": (0.709803921568627, 0.294117647058824, -0.749019607843137),
    "gray": (0.00392156862745097, 0.00392156862745097, 0.00392156862745097),
    "grey": (0.00392156862745097, 0.00392156862745097, 0.00392156862745097),
    "green": (-1, 0.00392156862745097, -1),
    "greenyellow": (0.356862745098039, 1, -0.631372549019608),
    "honeydew": (0.882352941176471, 1, 0.882352941176471),
    "hotpink": (1, -0.176470588235294, 0.411764705882353),
    "indigo": (-0.411764705882353, -1, 0.0196078431372548),
    "ivory": (1, 1, 0.882352941176471),
    "khaki": (0.882352941176471, 0.803921568627451, 0.0980392156862746),
    "lavender": (0.803921568627451, 0.803921568627451, 0.96078431372549),
    "lavenderblush": (1, 0.882352941176471, 0.92156862745098),
    "lawngreen": (-0.0274509803921569, 0.976470588235294, -1),
    "lemonchiffon": (1, 0.96078431372549, 0.607843137254902),
    "lightblue": (0.356862745098039, 0.694117647058824, 0.803921568627451),
    "lightcoral": (0.882352941176471, 0.00392156862745097, 0.00392156862745097),
    "lightcyan": (0.756862745098039, 1, 1),
    "lightgoldenrodyellow": (0.96078431372549, 0.96078431372549, 0.647058823529412),
    "lightgray": (0.654901960784314, 0.654901960784314, 0.654901960784314),
    "lightgreen": (0.129411764705882, 0.866666666666667, 0.129411764705882),
    "lightgrey": (0.654901960784314, 0.654901960784314, 0.654901960784314),
    "lightpink": (1, 0.427450980392157, 0.513725490196078),
    "lightsalmon": (1, 0.254901960784314, -0.0431372549019607),
    "lightseagreen": (-0.749019607843137, 0.396078431372549, 0.333333333333333),
    "lightskyblue": (0.0588235294117647, 0.615686274509804, 0.96078431372549),
    "lightslategray": (-0.0666666666666667, 0.0666666666666667, 0.2),
    "lightslategrey": (-0.0666666666666667, 0.0666666666666667, 0.2),
    "lightsteelblue": (0.380392156862745, 0.537254901960784, 0.741176470588235),
    "lightyellow": (1, 1, 0.756862745098039),
    "lime": (-1, 1, -1),
    "limegreen": (-0.607843137254902, 0.607843137254902, -0.607843137254902),
    "linen": (0.96078431372549, 0.882352941176471, 0.803921568627451),
    "magenta": (1, -1, 1),
    "maroon": (0.00392156862745097, -1, -1),
    "mediumaquamarine": (-0.2, 0.607843137254902, 0.333333333333333),
    "mediumblue": (-1, -1, 0.607843137254902),
    "mediumorchid": (0.458823529411765, -0.333333333333333, 0.654901960784314),
    "mediumpurple": (0.152941176470588, -0.12156862745098, 0.717647058823529),
    "mediumseagreen": (-0.529411764705882, 0.403921568627451, -0.113725490196078),
    "mediumslateblue": (-0.0352941176470588, -0.184313725490196, 0.866666666666667),
    "mediumspringgreen": (-1, 0.96078431372549, 0.207843137254902),
    "mediumturquoise": (-0.435294117647059, 0.63921568627451, 0.6),
    "mediumvioletred": (0.56078431372549, -0.835294117647059, 0.0431372549019609),
    "midnightblue": (-0.803921568627451, -0.803921568627451, -0.12156862745098),
    "mintcream": (0.92156862745098, 1, 0.96078431372549),
    "mistyrose": (1, 0.788235294117647, 0.764705882352941),
    "moccasin": (1, 0.788235294117647, 0.419607843137255),
    "navajowhite": (1, 0.741176470588235, 0.356862745098039),
    "navy": (-1, -1, 0.00392156862745097),
    "oldlace": (0.984313725490196, 0.92156862745098, 0.803921568627451),
    "olive": (0.00392156862745097, 0.00392156862745097, -1),
    "olivedrab": (-0.16078431372549, 0.113725490196078, -0.725490196078431),
    "orange": (1, 0.294117647058824, -1),
    "orangered": (1, -0.458823529411765, -1),
    "orchid": (0.709803921568627, -0.12156862745098, 0.67843137254902),
    "palegoldenrod": (0.866666666666667, 0.819607843137255, 0.333333333333333),
    "palegreen": (0.192156862745098, 0.968627450980392, 0.192156862745098),
    "paleturquoise": (0.372549019607843, 0.866666666666667, 0.866666666666667),
    "palevioletred": (0.717647058823529, -0.12156862745098, 0.152941176470588),
    "papayawhip": (1, 0.874509803921569, 0.670588235294118),
    "peachpuff": (1, 0.709803921568627, 0.450980392156863),
    "peru": (0.607843137254902, 0.0431372549019609, -0.505882352941176),
    "pink": (1, 0.505882352941176, 0.592156862745098),
    "plum": (0.733333333333333, 0.254901960784314, 0.733333333333333),
    "powderblue": (0.380392156862745, 0.756862745098039, 0.803921568627451),
    "purple": (0.00392156862745097, -1, 0.00392156862745097),
    "red": (1, -1, -1),
    "rosybrown": (0.474509803921569, 0.12156862745098, 0.12156862745098),
    "royalblue": (-0.490196078431373, -0.176470588235294, 0.764705882352941),
    "saddlebrown": (0.0901960784313725, -0.458823529411765, -0.850980392156863),
    "salmon": (0.96078431372549, 0.00392156862745097, -0.105882352941176),
    "sandybrown": (0.913725490196079, 0.286274509803922, -0.247058823529412),
    "seagreen": (-0.63921568627451, 0.0901960784313725, -0.317647058823529),
    "seashell": (1, 0.92156862745098, 0.866666666666667),
    "sienna": (0.254901960784314, -0.356862745098039, -0.647058823529412),
    "silver": (0.505882352941176, 0.505882352941176, 0.505882352941176),
    "skyblue": (0.0588235294117647, 0.615686274509804, 0.843137254901961),
    "slateblue": (-0.168627450980392, -0.294117647058823, 0.607843137254902),
    "slategray": (-0.12156862745098, 0.00392156862745097, 0.129411764705882),
    "slategrey": (-0.12156862745098, 0.00392156862745097, 0.129411764705882),
    "snow": (1, 0.96078431372549, 0.96078431372549),
    "springgreen": (-1, 1, -0.00392156862745097),
    "steelblue": (-0.450980392156863, 0.0196078431372548, 0.411764705882353),
    "tan": (0.647058823529412, 0.411764705882353, 0.0980392156862746),
    "teal": (-1, 0.00392156862745097, 0.00392156862745097),
    "thistle": (0.694117647058824, 0.498039215686275, 0.694117647058824),
    "tomato": (1, -0.223529411764706, -0.443137254901961),
    "turquoise": (-0.498039215686275, 0.756862745098039, 0.631372549019608),
    "violet": (0.866666666666667, 0.0196078431372548, 0.866666666666667),
    "wheat": (0.92156862745098, 0.741176470588235, 0.403921568627451),
    "white": (1, 1, 1),
    "whitesmoke": (0.92156862745098, 0.92156862745098, 0.92156862745098),
    "yellow": (1, 1, -1),
    "yellowgreen": (0.207843137254902, 0.607843137254902, -0.607843137254902)
}

# Convert all named colors to numpy arrays
for key in colorNames:
    colorNames[key] = np.array(colorNames[key])

# Dict of regexpressions/ranges for different formats
colorSpaces = {
    'named': re.compile("|".join(list(colorNames))), # A named colour space
    'hex': re.compile(r'#[\dabcdefABCDEF]{6}'), # Hex
    'rgb': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1)], # RGB from -1 to 1
    'rgba': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1), infrange(0, 1)],  # RGB + alpha from -1 to 1
    'rgb1': [infrange(0, 1), infrange(0, 1), infrange(0, 1)],  # RGB from 0 to 1
    'rgba1': [infrange(0, 1), infrange(0, 1), infrange(0, 1), infrange(0, 1)],  # RGB + alpha from 0 to 1
    'rgb255': [infrange(0, 255, 1), infrange(0, 255, 1), infrange(0, 255, 1)], # RGB from 0 to 255
    'rgba255': [infrange(0, 255, 1), infrange(0, 255, 1), infrange(0, 255, 1), infrange(0, 1)], # RGB + alpha from 0 to 255
    'hsv': [infrange(0, 360, 1), infrange(0, 1), infrange(0, 1)], # HSV with hue from 0 to 360 and saturation/vibrancy from 0 to 1
    'hsva': [infrange(0, 360, 1), infrange(0, 1), infrange(0, 1), infrange(0, 1)], # HSV with hue from 0 to 360 and saturation/vibrancy from 0 to 1 + alpha from 0 to 1
    # 'rec709TF': [infrange(-4.5, 1), infrange(-4.5, 1), infrange(-4.5, 1)], # rec709TF adjusted RGB from -4.5 to 1
    # 'rec709TFa': [infrange(-4.5, 1), infrange(-4.5, 1), infrange(-4.5, 1), infrange(0, 1)], # rec709TF adjusted RGB from -4.5 to 1 + alpha from 0 to 1
    'srgb': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1)],  # srgb from -1 to 1
    'srgba': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1), infrange(0, 1)], # srgb from -1 to 1 + alpha from 0 to 1
    'lms': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1), infrange(0, 1)],  # LMS from -1 to 1
    'lmsa': [infrange(-1, 1), infrange(-1, 1), infrange(-1, 1), infrange(0, 1)],  # LMS + alpha from 0 to 1
    'dkl': [infrange(-inf, inf), infrange(-inf, inf), infrange(-inf, inf), infrange(0, 1)], # DKL placeholder: Accepts any values
    'dkla': [infrange(-inf, inf), infrange(-inf, inf), infrange(-inf, inf), infrange(0, 1)], # DKLA placeholder: Accepts any values + alpha from 0 to 1
    'dklCart': [infrange(-inf, inf), infrange(-inf, inf), infrange(-inf, inf), infrange(0, 1)],
    # Cartesian DKL placeholder: Accepts any values
    'dklaCart': [infrange(-inf, inf), infrange(-inf, inf), infrange(-inf, inf), infrange(0, 1)],
    # Cartesian DKLA placeholder: Accepts any values + alpha from 0 to 1
}

# Create subgroups of spaces for easy reference
integerSpaces = []
strSpaces = []
for key, val in colorSpaces.items():
    if isinstance(val, re.compile("").__class__):
        # Add any spaces which are str to a list
        strSpaces.append(key)
    elif isinstance(val, (list, tuple)):
        # Add any spaces which are integer-only to a list
        for cell in val:
            if isinstance(cell, infrange):
                if cell.step == 1 and key not in integerSpaces:
                    integerSpaces.append(key)

alphaSpaces = [
    'rgba', 'rgba1', 'rgba255', 'hsva', 'srgba', 'lmsa', 'dkla', 'dklaCart']
nonAlphaSpaces = list(colorSpaces)
for val in alphaSpaces:
    nonAlphaSpaces.remove(val)


class Color:
    """A class to store color details, knows what colour space it's in and can
    supply colours in any space.

    Parameters
    ----------
    color : ArrayLike or None
        Color values (coordinates). Value must be in a format applicable to the
        specified `space`.
    space : str or None
        Colorspace to interpret the value of `color` as being within.
    contrast : int or float
        Factor to modulate the contrast of the color.
    conematrix : ArrayLike or None
        Cone matrix for colorspaces which require it. Must be a 3x3 array.

    """
    def __init__(self, color=None, space=None, contrast=None, conematrix=None):
        self._cache = {}
        self._renderCache = {}
        self.contrast = contrast if isinstance(contrast, (int, float)) else 1
        self.alpha = 1
        self.valid = False
        self.conematrix = conematrix

        # defined here but set later
        self._requested = None
        self._requestedSpace = None

        self.set(color=color, space=space)

    def validate(self, color, space=None):
        """
        Check that a color value is valid in the given space, or all spaces if space==None.
        """
        # Treat None as a named color
        if color is None:
            color = "none"
        if isinstance(color, str):
            if color == "":
                color = "none"
        # Handle everything as an array
        if not isinstance(color, np.ndarray):
            color = np.array(color)
        if color.ndim <= 1:
            color = np.reshape(color, (1, -1))
        # If data type is string, check against named and hex as these override other spaces
        if color.dtype.char == 'U':
            # Remove superfluous quotes
            for i in range((len(color[:, 0]))):
                color[i, 0] = color[i, 0].replace("\"", "").replace("'", "")
            # If colors are all named, override color space
            namedMatch = np.vectorize(
                lambda col: bool(colorSpaces['named'].fullmatch(
                    str(col).lower())))  # match regex against named
            if all(namedMatch(color[:, 0])):
                space = 'named'
            # If colors are all hex, override color space
            hexMatch = np.vectorize(
                lambda col: bool(colorSpaces['hex'].fullmatch(str(col))))  # match regex against hex
            if all(hexMatch(color[:, 0])):
                space = 'hex'
            # If color is a string but does not match any string space, it's invalid
            if space not in strSpaces:
                self.valid = False
        # Error if space still not set
        if not space:
            self.valid = False
            raise ValueError("Please specify a color space.")
        # Check that color space is valid
        if not space in colorSpaces:
            self.valid = False
            raise ValueError("{} is not a valid color space.".format(space))
        # Get number of columns
        if color.ndim == 1:
            ncols = len(color)
        else:
            ncols = color.shape[1]
        # Extract alpha if set
        if space in strSpaces and ncols > 1:
            # If color should only be one value, extract second row
            self.alpha = color[:, 1]
            color = color[:, 0]
            ncols -= 1
        elif space not in strSpaces and ncols > 3:
            # If color should be triplet, extract fourth row
            self.alpha = color[:, 3]
            color = color[:, :3]
            ncols -= 1
        elif space not in strSpaces and ncols == 2:
            # If color should be triplet but is single value, extract second row
            self.alpha = color[:, 1]
            color = color[:, 1]
            ncols -= 1
        # If single value given in place of triplet, duplicate it
        if space not in strSpaces and ncols == 1:
            color = np.tile(color, (1, 3))
            # ncols = 3  # unused?
        # If values should be integers, round them
        if space in integerSpaces:
            color.round()
        # Finally, if array is only 1 long, remove extraneous dimension
        if color.shape[0] == 1:
            color = color[0]

        return color, space

    def set(self, color=None, space=None):
        """Set the colour of this object - essentially the same as what happens
        on creation, but without having to initialise a new object.
        """
        # If input is a Color object, duplicate all settings
        if isinstance(color, Color):
            self._requested = color._requested
            self._requestedSpace = color._requestedSpace
            self.valid = color.valid
            if color.valid:
                self.rgba = color.rgba
            return
        # Store requested colour and space (or defaults, if none given)
        self._requested = color
        self._requestedSpace = space
        # Validate and prepare values
        color, space = self.validate(color, space)
        # Convert to lingua franca
        if space in colorSpaces:
            self.valid = True
            setattr(self, space, color)
        else:
            self.valid = False
            raise ValueError("{} is not a valid color space.".format(space))

    def render(self, space='rgb'):
        """Apply contrast to the base color value and return the adjusted color
        value.
        """
        if space not in colorSpaces:
            raise ValueError(f"{space} is not a valid color space")
        # If value is cached, return it rather than doing calculations again
        if space in self._renderCache:
            return self._renderCache[space]
        # Transform contrast to match rgb
        contrast = self.contrast
        contrast = np.reshape(contrast, (-1, 1))
        contrast = np.hstack((contrast, contrast, contrast))
        # Multiply
        adj = np.clip(self.rgb * contrast, -1, 1)
        buffer = self.copy()
        buffer.rgb = adj
        return getattr(buffer, space)

    def __repr__(self):
        """If colour is printed, it will display its class and value.
        """
        if self.valid:
            if self.named:
                return (f"<{self.__class__.__module__}."
                        f"{self.__class__.__name__}: {self.named}, "
                        f"alpha={self.alpha}>")
            else:
                return (f"<{self.__class__.__module__}."
                        f"{self.__class__.__name__}: "
                        f"{tuple(np.round(self.rgba, 2))}>")
        else:
            return (f"<{self.__class__.__module__}."
                    f"{self.__class__.__name__}: Invalid>")

    def __bool__(self):
        """Determines truth value of object"""
        return self.valid

    def __len__(self):
        """Determines the length of object"""
        if len(self.rgb.shape) > 1:
            return self.rgb.shape[0]
        else:
            return int(bool(self.rgb.shape))

    # --------------------------------------------------------------------------
    # Rich comparisons
    #

    def __eq__(self, target):
        """`==` will compare RGBA values, rounded to 2dp"""
        if isinstance(target, Color):
            return np.all(np.round(target.rgba, 2) == np.round(self.rgba, 2))
        elif target == None:
            return self._requested is None
        else:
            return False

    def __ne__(self, target):
        """`!=` will return the opposite of `==`"""
        return not self == target

    # --------------------------------------------------------------------------
    # Operators
    #

    def __add__(self, other):
        buffer = self.copy()
        # If target is a list or tuple, convert it to an array
        if isinstance(other, (list, tuple)):
            other = np.array(other)
        # If target is a single number, add it to each rgba value
        if isinstance(other, (int, float)):
            buffer.rgba = self.rgba + other
        # If target is an array, add the arrays provided they are viable
        if isinstance(other, np.ndarray):
            if other.shape in [(len(self), 1), self.rgb.shape, self.rgba.shape]:
                buffer.rgba = self.rgba + other
        # If target is a Color object, add together the rgba values
        if isinstance(other, Color):
            if len(self) == len(other):
                buffer.rgba = self.rgba + other.rgba
        return buffer

    def __sub__(self, other):
        buffer = self.copy()
        # If target is a list or tuple, convert it to an array
        if isinstance(other, (list, tuple)):
            other = np.array(other)
        # If target is a single number, subtract it from each rgba value
        if isinstance(other, (int, float)):
            buffer.rgba = self.rgba - other
        # If target is an array, subtract the arrays provided they are viable
        if isinstance(other, np.ndarray):
            if other.shape in [(len(self), 1), self.rgb.shape, self.rgba.shape]:
                buffer.rgba = self.rgba - other
        # If target is a Color object, add together the rgba values
        if isinstance(other, Color):
            if len(self) == len(other):
                buffer.rgb = self.rgb - other.rgb
        return buffer

    # --------------------------------------------------------------------------
    # Methods and properties
    #

    def copy(self):
        """Return a duplicate of this colour"""
        return self.__copy__()

    def __copy__(self):
        return self.__deepcopy__()

    def __deepcopy__(self):
        dupe = self.__class__(None, contrast=self.contrast)
        dupe._requested = self._requested
        dupe._requestedSpace = self._requestedSpace
        dupe.valid = self.valid
        dupe._cache = self._cache

        return dupe

    def getReadable(self, contrast=4.5/21):
        """
        Get a color which will stand out and be easily readable against this
        one. Useful for choosing text colors based on background color.

        Parameters
        ----------
        contrast : float
            Desired perceived contrast between the two colors, between 0 (the
            same color) and 1 (as opposite as possible). Default is the
            w3c recommended minimum of 4.5/21 (dividing by 21 to adjust for
            sRGB units).

        Returns
        -------
        colors.Color
            A contrasting color to this color.
        """
        # adjust contrast to sRGB
        contrast *= 21
        # get value as rgb1
        rgb = self.rgb1
        # convert to srgb
        srgb = rgb**2.2 * [0.2126, 0.7151, 0.0721]
        # apply contrast adjustment
        if np.sum(srgb) < 0.5:
            srgb = (srgb + 0.05) * contrast
        else:
            srgb = (srgb + 0.05) / contrast
        # convert back
        rgb = (srgb / [0.2126, 0.7151, 0.0721])**(1/2.2)
        # cap
        rgb = np.clip(rgb, 0, 1)
        # Return new color
        return Color(rgb, "rgb1")

    @property
    def alpha(self):
        """How opaque (1) or transparent (0) this color is. Synonymous with
        `opacity`.
        """
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        # Treat 1x1 arrays as a float
        if isinstance(value, np.ndarray):
            if value.size == 1:
                value = float(value)
        # Clip value(s) to within range
        if isinstance(value, np.ndarray):
            value = np.clip(value, 0, 1)
        else:
            # If coercible to float, do so
            try:
                value = float(value)
            except (TypeError, ValueError) as err:
                raise TypeError(
                    "Could not set alpha as value `{}` of type `{}`".format(value, type(value).__name__)
                )
            value = min(value, 1)
            value = max(value, 0)
        # Set value
        self._alpha = value
        # Clear render cache
        self._renderCache = {}

    @property
    def contrast(self):
        if hasattr(self, "_contrast"):
            return self._contrast

    @contrast.setter
    def contrast(self, value):
        # Set value
        self._contrast = value
        # Clear render cache
        self._renderCache = {}

    @property
    def opacity(self):
        """How opaque (1) or transparent (0) this color is (`float`). Synonymous
        with `alpha`.
        """
        return self.alpha

    @opacity.setter
    def opacity(self, value):
        self.alpha = value

    def _appendAlpha(self, space):
        # Get alpha, if necessary transform to an array of same length as color
        alpha = self.alpha
        if isinstance(alpha, (int, float)):
            if len(self) > 1:
                alpha = np.tile([alpha], (len(self), 1))
            else:
                alpha = np.array([alpha])
        if isinstance(alpha, np.ndarray) and len(self) > 1:
            alpha = alpha.reshape((len(self), 1))
        # Get color
        color = getattr(self, space)
        # Append alpha to color
        return np.append(color, alpha, axis=1 if color.ndim > 1 else 0)

    #---spaces---
    # Lingua franca is rgb
    @property
    def rgba(self):
        """Color value expressed as an RGB triplet from -1 to 1, with alpha
        values (0 to 1).
        """
        return self._appendAlpha('rgb')

    @rgba.setter
    def rgba(self, color):
        self.rgb = color

    @property
    def rgb(self):
        """Color value expressed as an RGB triplet from -1 to 1.
        """
        if not self.valid:
            return
        if hasattr(self, '_franca'):
            rgb = self._franca
            return rgb
        else:
            return np.array([0, 0, 0])

    @rgb.setter
    def rgb(self, color):
        # Validate
        color, space = self.validate(color, space='rgb')
        if space != 'rgb':
            setattr(self, space, color)
            return
        # Set color
        self._franca = color
        # Clear outdated values from cache
        self._cache = {'rgb': color}
        self._renderCache = {}

    @property
    def rgba255(self):
        """Color value expressed as an RGB triplet from 0 to 255, with alpha
        value (0 to 1).
        """
        return self._appendAlpha('rgb255')

    @rgba255.setter
    def rgba255(self, color):
        self.rgb255 = color

    @property
    def rgb255(self):
        """Color value expressed as an RGB triplet from 0 to 255.
        """
        if not self.valid:
            return
        # Recalculate if not cached
        if 'rgb255' not in self._cache:
            self._cache['rgb255'] = np.round(255 * (self.rgb + 1) / 2)
        return self._cache['rgb255']

    @rgb255.setter
    def rgb255(self, color):
        # Validate
        color, space = self.validate(color, space='rgb255')
        if space != 'rgb255':
            setattr(self, space, color)
            return
        # Iterate through values and do conversion
        self.rgb = 2 * (color / 255 - 0.5)
        # Clear outdated values from cache
        self._cache = {'rgb255': color}
        self._renderCache = {}

    @property
    def rgba1(self):
        """Color value expressed as an RGB triplet from 0 to 1, with alpha value
        (0 to 1).
        """
        return self._appendAlpha('rgb1')

    @rgba1.setter
    def rgba1(self, color):
        self.rgb1 = color

    @property
    def rgb1(self):
        """Color value expressed as an RGB triplet from 0 to 1.
        """
        if not self.valid:
            return
        # Recalculate if not cached
        if 'rgb1' not in self._cache:
            self._cache['rgb1'] = (self.rgb + 1) / 2
        return self._cache['rgb1']

    @rgb1.setter
    def rgb1(self, color):
        # Validate
        color, space = self.validate(color, space='rgb1')
        if space != 'rgb1':
            setattr(self, space, color)
            return
        # Iterate through values and do conversion
        self.rgb = 2 * (color - 0.5)
        # Clear outdated values from cache
        self._cache = {'rgb1': color}
        self._renderCache = {}

    @property
    def hex(self):
        """Color value expressed as a hex string. Can be a '#' followed by 6
        values from 0 to F (e.g. #F2545B).
        """
        if not self.valid:
            return
        if 'hex' not in self._cache:
            # Map rgb255 values to corresponding letters in hex
            hexmap = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
            # Handle arrays
            if self.rgb255.ndim > 1:
                rgb255 = self.rgb255
                # Iterate through rows of rgb255
                self._cache['hex'] = np.array([])
                for row in rgb255:
                    rowHex = '#'
                    # Convert each value to hex and append
                    for val in row:
                        dig = hex(int(val)).strip('0x')
                        rowHex += dig if len(dig) == 2 else '0' + dig
                    # Append full hex value to new array
                    self._cache['hex'] = np.append(
                        self._cache['hex'], [rowHex], 0)
            else:
                rowHex = '#'
                # Convert each value to hex and append
                for val in self.rgb255:
                    dig = hex(int(val))[2:]
                    rowHex += dig if len(dig) == 2 else '0' + dig
                # Append full hex value to new array
                self._cache['hex'] = rowHex
        return self._cache['hex']

    @hex.setter
    def hex(self, color):
        # Validate
        color, space = self.validate(color, space='hex')
        if space != 'hex':
            setattr(self, space, color)
            return
        if len(color) > 1:
            # Handle arrays
            rgb255 = np.array([""])
            for row in color:
                if isinstance(row, np.ndarray):
                    row = row[0]
                row = row.strip('#')
                # Convert string to list of strings
                hexList = [row[:2], row[2:4], row[4:6]]
                # Convert strings to int
                hexInt = [int(val, 16) for val in hexList]
                # Convert to array and append
                rgb255 = np.append(rgb255, np.array(hexInt), 0)
        else:
            # Handle single values
            if isinstance(color, np.ndarray):
                # Strip away any extraneous numpy layers
                color = color[(0,)*color.ndim]
            color = color.strip('#')
            # Convert string to list of strings
            hexList = [color[:2], color[2:4], color[4:6]]
            # Convert strings to int
            hexInt = [int(val, 16) for val in hexList]
            # Convert to array
            rgb255 = np.array(hexInt)
        # Set rgb255 accordingly
        self.rgb255 = rgb255
        # Clear outdated values from cache
        self._cache = {'hex': color}
        self._renderCache = {}

    @property
    def named(self):
        """The name of this color, if it has one (`str`).
        """
        if 'named' not in self._cache:
            self._cache['named'] = None
            # If alpha is 0, then we know that the color is None
            if isinstance(self.alpha, np.ndarray):
                invis = all(self.alpha == 0)
            elif isinstance(self.alpha, (int, float)):
                invis = self.alpha == 0
            else:
                invis = False
            if invis:
                self._cache['named'] = 'none'
                return self._cache['named']
            self._cache['named'] = np.array([])
            # Handle array
            if len(self) > 1:
                for row in self.rgb:
                    for name, val in colorNames.items():
                        if all(val[:3] == row):
                            self._cache['named'] = np.append(
                                self._cache['named'], [name], 0)
                            continue
                self._cache['named'] = np.reshape(self._cache['named'], (-1, 1))
            else:
                rgb = self.rgb
                for name, val in colorNames.items():
                    if name == 'none': # skip None
                        continue
                    if all(val[:3] == rgb):
                        self._cache['named'] = name
                        continue
        return self._cache['named']

    @named.setter
    def named(self, color):
        # Validate
        color, space = self.validate(color=color, space='named')
        if space != 'named':
            setattr(self, space, color)
            return
        # Retrieve named colour
        if len(color) > 1:
            # Handle arrays
            for row in color:
                row = str(np.reshape(row, ())) # Enforce str
                if str(row).lower() in colorNames:
                    self.rgb = colorNames[str(row).lower()]
                if row.lower() == 'none':
                    self.alpha = 0
        else:
            color = str(np.reshape(color, ())) # Enforce str
            if color.lower() in colorNames:
                self.rgb = colorNames[str(color).lower()]
            if color.lower() == 'none':
                self.alpha = 0
        # Clear outdated values from cache
        self._cache = {'named': color}
        self._renderCache = {}

    @property
    def hsva(self):
        """Color value expressed as an HSV triplet, with alpha value (0 to 1).
        """
        return self._appendAlpha('hsv')

    @hsva.setter
    def hsva(self, color):
        self.hsv = color

    @property
    def hsv(self):
        """Color value expressed as an HSV triplet.
        """
        if 'hsva' not in self._cache:
            self._cache['hsv'] = ct.rgb2hsv(self.rgb)
        return self._cache['hsv']

    @hsv.setter
    def hsv(self, color):
        # Validate
        color, space = self.validate(color=color, space='hsv')
        if space != 'hsv':
            setattr(self, space, color)
            return
        # Apply via rgba255
        self.rgb = ct.hsv2rgb(color)
        # Clear outdated values from cache
        self._cache = {'hsv': color}
        self._renderCache = {}

    @property
    def lmsa(self):
        """Color value expressed as an LMS triplet, with alpha value (0 to 1).
        """
        return self._appendAlpha('lms')

    @lmsa.setter
    def lmsa(self, color):
        self.lms = color

    @property
    def lms(self):
        """Color value expressed as an LMS triplet.
        """
        if 'lms' not in self._cache:
            self._cache['lms'] = ct.rgb2lms(self.rgb)
        return self._cache['lms']

    @lms.setter
    def lms(self, color):
        # Validate
        color, space = self.validate(color=color, space='lms')
        if space != 'lms':
            setattr(self, space, color)
            return
        # Apply via rgba255
        self.rgb = ct.lms2rgb(color, self.conematrix)
        # Clear outdated values from cache
        self._cache = {'lms': color}
        self._renderCache = {}

    @property
    def dkla(self):
        """Color value expressed as a DKL triplet, with alpha value (0 to 1).
        """
        return self._appendAlpha('dkl')

    @dkla.setter
    def dkla(self, color):
        self.dkl = color

    @property
    def dkl(self):
        """Color value expressed as a DKL triplet.
        """
        if 'dkl' not in self._cache:
            raise NotImplementedError(
                "Conversion from rgb to dkl is not yet implemented.")
        return self._cache['dkl']

    @dkl.setter
    def dkl(self, color):
        # Validate
        color, space = self.validate(color=color, space='dkl')
        if space != 'dkl':
            setattr(self, space, color)
            return
        # Apply via rgba255
        self.rgb = ct.dkl2rgb(color, self.conematrix)
        # Clear outdated values from cache
        self._cache = {'dkl': color}
        self._renderCache = {}

    @property
    def dklaCart(self):
        """Color value expressed as a cartesian DKL triplet, with alpha value
        (0 to 1).
        """
        return self.dklCart

    @dklaCart.setter
    def dklaCart(self, color):
        self.dklCart = color

    @property
    def dklCart(self):
        """Color value expressed as a cartesian DKL triplet.
        """
        if 'dklCart' not in self._cache:
            self._cache['dklCart'] = ct.rgb2dklCart(self.rgb)
        return self._cache['dklCart']

    @dklCart.setter
    def dklCart(self, color):
        # Validate
        color, space = self.validate(color=color, space='dklCart')
        if space != 'dkl':
            setattr(self, space, color)
            return
        # Apply via rgba255
        self.rgb = ct.dklCart2rgb(color, self.conematrix)
        # Clear outdated values from cache
        self._cache = {'dklCart': color}
        self._renderCache = {}

    @property
    def srgb(self):
        """
        Color value expressed as an sRGB triplet
        """
        if 'srgb' not in self._cache:
            self._cache['srgb'] = ct.srgbTF(self.rgb)
        return self._cache['srgb']

    @srgb.setter
    def srgb(self, color):
        # Validate
        color, space = self.validate(color=color, space='srgb')
        if space != 'srgb':
            setattr(self, space, color)
            return
        # Apply via rgba255
        self.rgb = ct.srgbTF(color, reverse=True)
        # Clear outdated values from cache
        self._cache = {'srgb': color}
        self._renderCache = {}

    # removing for now
    # @property
    # def rec709TF(self):
    #     if 'rec709TF' not in self._cache:
    #         self._cache['rec709TF'] = ct.rec709TF(self.rgb)
    #     return self._cache['rec709TF']
    #
    # @rec709TF.setter
    # def rec709TF(self, color):
    #     # Validate
    #     color, space = self.validate(color=color, space='rec709TF')
    #     if space != 'rec709TF':
    #         setattr(self, space, color)
    #         return
    #     # Apply via rgba255
    #     self.rgb = ct.rec709TF(color, reverse=True)
    #     # Clear outdated values from cache
    #     self._cache = {'rec709TF': color}
    #     self._renderCache = {}


# ------------------------------------------------------------------------------
# Legacy functions
#

# Old reference tables
colors = colorNames
# colorsHex = {key: Color(key, 'named').hex for key in colors}
# colors255 = {key: Color(key, 'named').rgb255 for key in colors}


# Old conversion functions
def hex2rgb255(hexColor):
    """Depreciated as of 2021.0

    Converts a hex color string (e.g. "#05ff66") into an rgb triplet
    ranging from 0:255
    """
    col = Color(hexColor, 'hex')
    if len(hexColor.strip('#')) == 6:
        return col.rgb255
    elif len(hexColor.strip('#')) == 8:
        return col.rgba255


def isValidColor(color, space='rgb'):
    """Depreciated as of 2021.0
    """
    logging.warning(
        "DEPRECIATED: While psychopy.colors.isValidColor will still roughly "
        "work, you should use a Color object, allowing you to check its "
        "validity simply by converting it to a `bool` (e.g. `bool(myColor)` or "
        "`if myColor:`). If you use this function for colors in any space "
        "other than hex, named or rgb, please specify the color space.")
    try:
        buffer = Color(color, space)
        return bool(buffer)
    except:
        return False


if __name__ == "__main__":
    pass
