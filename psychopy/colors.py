#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from past.builtins import basestring
from past.builtins import basestring
from psychopy.tools.coordinatetools import sph2cart
from psychopy import logging
import re
import numpy
from math import floor, fsum

from psychopy import logging

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
        "none": (0, 0, 0),
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
        "indianred": (0.607843137254902, -0.27843137254902, -0.27843137254902),
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
# Shorthand for common regexpressions
_255 = r'(\d|\d\d|1\d\d|2[0-4]\d|25[0-5])'
_360 = r'((\d|\d\d|[12]\d\d|3[0-5]\d)(\.\d)*|360|360\.0*)'
_100 = r'((\d|\d\d)(\.\d)*|100|100\.0*)'
_1 = r'(0|1|1.0*|0\.\d*)'
_lbr = r'[\[\(]\s*'
_rbr = r'\s*[\]\)]'
# Dict of regexpressions for different formats
colorSpaces = {
    'named': re.compile("|".join(list(colorNames))), # A named colour space
    'hex': re.compile(r'#[\dabcdefABCDEF]{6}'), # Hex
    'rgb': re.compile(_lbr+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+r'\-?'+_1+_rbr), # RGB from -1 to 1
    'rgba': re.compile(_lbr+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+r'\-?'+_1+_rbr),  # RGB + alpha from -1 to 1
    'rgb1': re.compile(_lbr+_1+r',\s*'+_1+r',\s*'+_1+_rbr),  # RGB from 0 to 1
    'rgba1': re.compile(_lbr+_1+r',\s*'+_1+r',\s*'+_1+r',\s*'+_1+_rbr),  # RGB + alpha from 0 to 1
    'rgb255': re.compile(_lbr+_255+r',\s*'+_255+r',\s*'+_255+_rbr), # RGB from 0 to 255
    'rgba255': re.compile(_lbr+_255+r',\s*'+_255+r',\s*'+_255+r',\s*'+_1+_rbr), # RGB + alpha from 0 to 255
    'hsv': re.compile(_lbr+_360+r'\°?'+r',\s*'+_1+r',\s*'+_1+_rbr), # HSV with hue from 0 to 360 and saturation/vibrancy from 0 to 1
    'hsva': re.compile(_lbr+_360+r'\°?'+r',\s*'+_1+r',\s*'+_1+r',\s*'+_1+_rbr), # HSV with hue from 0 to 360 and saturation/vibrancy from 0 to 1 + alpha from 0 to 1
}


class Color(object):
    """A class to store colour details, knows what colour space it's in and can supply colours in any space"""

    def __init__(self, color=None, space=None, contrast=None):
        self._cache = {}
        self.contrast = contrast if isinstance(contrast, (int, float)) else 1
        self.alpha = 1
        self.set(color=color, space=space)

    def set(self, color=None, space=None):
        """Set the colour of this object - essentially the same as what happens on creation, but without
        having to initialise a new object"""
        if isinstance(color, numpy.ndarray):
            color = tuple(float(c) for c in color)
        if space in ['rgb255', 'rgba255']:
            color = tuple(int(c) for c in color)
        # If input is a Color object, duplicate all settings
        if isinstance(color, Color):
            self._requested = color._requested
            self._requestedSpace = color._requestedSpace
            self.rgba = color.rgba
            return
        # if supplied a named color, ignore color space
        if 'named' in self.getSpace(color, True):
            space = 'named'
        # Store requested colour and space (or defaults, if none given)
        self._requested = color if color is not None else None
        self._requestedSpace = space \
            if space and space in self.getSpace(self._requested, debug=True) \
            else self.getSpace(self._requested)
        if isinstance(self._requestedSpace, (list, type(None))):
            logging.error("Color space could not be determined by values supplied, please specify a color space.")
            return

        # Convert to lingua franca
        if self._requestedSpace:
            setattr(self, self._requestedSpace, self._requested)
        else:
            self.named = None

    def __repr__(self):
        """If colour is printed, it will display its class and value"""
        if self.rgba:
            if self.named:
                return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + self.named + ">"
            else:
                return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + str(tuple(round(c,2) for c in self.rgba)) + ">"
        else:
            return "<" + self.__class__.__module__ + "." + self.__class__.__name__ + ": " + "Invalid" + ">"

    def __bool__(self):
        """Determines truth value of object"""
        return bool(self.rgba)

    # ---rich comparisons---
    def __eq__(self, target):
        """== will compare RGBA values, rounded to 2dp"""
        if isinstance(target, Color):
            return tuple(round(c,2) for c in self.rgba) == tuple(round(c,2) for c in target.rgba)
        elif target == None:
            return self.named == 'none'
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

    #--operators---
    def __add__(self, other):
        if not isinstance(other, Color):
            if Color.getSpace(other):
                # Convert to a color if valid
                other = Color(other)
            elif AdvancedColor.getSpace(other):
                # Convert to an advanced color if valid
                other = AdvancedColor(other)
            elif isinstance(other, int) or isinstance(other, float):
                out = self.copy()
                out.brightness += other
                return out
            else:
                raise ValueError ("unsupported operand type(s) for +: '"
                                  + self.__class__.__name__ +"' and '"
                                  + other.__class__.__name__ + "'")
        if isinstance(other, Color):
            # If both are colours, average the two and sum their alphas
            alpha = min(self.alpha + other.alpha, 1)
            rgb = [None, None, None]
            selfWeight = self.alpha/(self.alpha+other.alpha)
            otherWeight = other.alpha/(self.alpha+other.alpha)
            for c in range(3):
                rgb[c] = self.rgb1[c]*selfWeight + other.rgb1[c]*otherWeight
            return Color(rgb+[alpha], 'rgba1')


    def copy(self):
        """Return a duplicate of this colour"""
        dupe = self.__class__(self._requested, self._requestedSpace)
        dupe.rgba = self.rgba
        return dupe

    @staticmethod
    def getSpace(color, debug=False):
        """Find what colour space a colour is from"""
        if isinstance(color, Color):
            return color._requestedSpace
        possible = [space for space in colorSpaces
                    if colorSpaces[space].fullmatch(str(color).lower())]
        # Return full list if debug or multiple, else return first value
        if debug or not len(possible) == 1:
            return possible
        else:
            return possible[0]

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

    def validate(self, color, against=None, enforce=None):
        # If not checking against anything, check against everything
        if not against:
            against = list(colorSpaces)
        # If looking for a string, convert from other forms it could be in
        if enforce == str:
            color = str(color).lower()
        # If looking for a tuple, convert from other forms it could be in
        if enforce == tuple or enforce == (tuple, int):
            if isinstance(color, str):
                color = [float(n) for n in color.strip('[]()').split(',')]
            if isinstance(color, list):
                color = tuple(color)
        # If enforcing multiple
        if enforce == (tuple, int):
            color = tuple(int(round(c)) for c in color)
        # Get possible colour spaces
        possible = Color.getSpace(color)
        if isinstance(possible, str):
            possible = [possible]
        # Return if any matches
        for space in possible:
            if space in against:
                return color
        # If no matches...
        self.named = None
        return None

    # ---adjusters---
    # @property
    # def saturation(self):
    #     '''Saturation in hsv (0 to 1)'''
    #     return self.hsv[1]
    # @saturation.setter
    # def saturation(self, value):
    #     h,s,v,a = self.hsva
    #     s += value
    #     s = min(s, 1)
    #     s = max(s, 0)
    #     self.hsva = (h, s, v, a)

    # @property
    # def brightness(self):
    #     return sum(self.rgb1)/3
    # @brightness.setter
    # def brightness(self, value):
    #     adj = value-self.brightness
    #     self.rgba1 = tuple(
    #         max(min(c+adj, 1),0)
    #         for c in self.rgb1
    #     ) + (self.alpha,)

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, value):
        value = min(value,1)
        value = max(value,0)
        self._alpha = value

    #---spaces---
    # Lingua franca is rgb
    @property
    def rgba(self):
        return self.rgb + (self.alpha,)
    @rgba.setter
    def rgba(self, color):
        self.rgb = color
    @property
    def rgb(self):
        if hasattr(self, '_franca'):
            return self._franca
    @rgb.setter
    def rgb(self, color):
        # Validate
        color = self.validate(color, against=['rgb', 'rgba'], enforce=tuple)
        if not color:
            return
        # Set color
        self._franca = color[:3]
        # Append alpha, if not present
        if color[3:]:
            self.alpha = color[3]
        # Clear outdated values from cache
        self._cache = {}

    @property
    def rgba255(self):
        return self.rgb255 + (self.alpha,)
    @rgba255.setter
    def rgba255(self, color):
        self.rgb255 = color
    @property
    def rgb255(self):
        if not self.rgb:
            return None
        # Recalculate if not cached
        if 'rgb255' not in self._cache:
            self._cache['rgb255'] = tuple(int(255 * (val + 1) / 2) for val in self.rgb)
        return self._cache['rgb255']
    @rgb255.setter
    def rgb255(self, color):
        # Validate
        color = self.validate(color, against=['rgb255', 'rgba255'], enforce=(tuple, int))
        if not color:
            return
        # Iterate through values and do conversion
        self.rgb = tuple(2 * (val / 255 - 0.5) for val in color[:3])+color[3:]
        # Clear outdated values from cache
        self._cache = {}

    @property
    def rgba1(self):
        return self.rgb1 + (self.alpha,)
    @rgba1.setter
    def rgba1(self, color):
        self.rgb1 = color
    @property
    def rgb1(self):
        if not self.rgb:
            return
        # Recalculate if not cached
        if 'rgb1' not in self._cache:
            self._cache['rgb1'] = tuple((val + 1) / 2 for val in self.rgb)
        return self._cache['rgb1']
    @rgb1.setter
    def rgb1(self, color):
        # Validate
        color = self.validate(color, against=['rgb1', 'rgba1'], enforce=tuple)
        if not color:
            return
        # Iterate through values and do conversion
        self.rgb = tuple(2 * (val - 0.5) for val in color[:3])+color[3:]
        # Clear outdated values from cache
        self._cache = {}

    @property
    def hex(self):
        if not self.rgb255:
            return
        if 'hex' not in self._cache:
            # Map rgb255 values to corresponding letters in hex
            hexmap = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
            # Iterate and do conversion
            flatList = ['#']
            for val in self.rgb255:
                dig1 = int(floor(val / 16))
                flatList.append(
                    str(dig1) if dig1 <= 9 else hexmap[dig1]
                )
                dig2 = int(val % 16)
                flatList.append(
                    str(dig2) if dig2 <= 9 else hexmap[dig2]
                )
            self._cache['hex'] = "".join(flatList)
        return self._cache['hex']
    @hex.setter
    def hex(self, color):
        # Validate
        color = self.validate(color, against=['hex'], enforce=str)
        if not color:
            return
        # Convert strings to list
        colorList = [color[i - 2:i] for i in [3, 5, 7] if color[i - 2:i]]
        # Map hex letters to corresponding values in rgb255
        hexmap = {'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}
        # Create adjustment for different digits
        adj = {0:16, 1:1}
        flatList = []
        for val in colorList:
            # Iterate through individual values
            flat = 0
            for i, v in enumerate(val):
                if re.match(r'\d', str(v)):
                    flat += int(v)*adj[i]
                elif re.match(r'[abcdef]', str(v).lower()):
                    flat += hexmap[str(v).lower()]*adj[i]
            flatList.append(flat)
        self.rgb255 = flatList
        # Clear outdated values from cache
        self._cache = {}

    @property
    def named(self):
        if 'named' not in self._cache:
            # Round all values to 2 decimal places to find approximate matches
            approxNames = {col: [round(val, 2) for val in colorNames[col]]
                           for col in colorNames}
            approxColor = [round(val, 2) for val in self.rgba]
            # Get matches
            possible = [nm for nm in approxNames if approxNames[nm] == approxColor]
            # Return the first match
            if possible:
                self._cache['named'] = possible[0]
            else:
                self._cache['named'] = None
        return self._cache['named']
    @named.setter
    def named(self, color):
        # Validate
        color = self.validate(color=str(color).lower(), against=['named'], enforce=str)
        if not color:
            return
        # Retrieve named colour
        self.rgb = colorNames[str(color).lower()]
        if color.lower() == 'none':
            self.alpha = 0
        # Clear outdated values from cache
        self._cache = {}

    @property
    def hsva(self):
        return self.hsv + (self.alpha,)
    @hsva.setter
    def hsva(self, color):
        self.hsv = color
    @property
    def hsv(self):
        # Based on https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
        if 'hsva' not in self._cache:
            red, green, blue = self.rgb1
            cmax = max(red, green, blue)
            cmin = min(red, green, blue)
            delta = cmax - cmin
            # Calculate hue
            if cmax == 0 and cmin == 0:
                return (0, 0, 0)
            elif delta == 0:
                return (0, 0, sum(self.rgb1) / 3)

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
            self._cache['hsv'] = (round(hue), saturation, vibrancy)
        return self._cache['hsv']
    @hsv.setter
    def hsv(self, color):
        # based on method in
        # http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB

        # Validate
        color = self.validate(color, against=['hsva', 'hsv'], enforce=tuple)
        if not color:
            return
        # Extract values
        hue, saturation, vibrancy, *alpha = color
        # Calculate pure hue
        pureHue = self.hue2rgb255(hue)
        # Apply value
        hueVal = tuple(h * vibrancy for h in pureHue)
        # Get desired value in 255
        vibrancy255 = vibrancy * 255
        # Apply saturation
        all255 = tuple(round(h + (vibrancy255 - h) * (1 - saturation)) for h in hueVal)
        # Apply via rgba255
        self.rgb255 = all255 + (alpha,) if alpha else all255
        # Clear outdated values from cache
        self._cache = {}

_rec = r'(\-4\.5|\-4\.4\d*|\-4\.[0-4]\d*|\-[0-3]\.\d*|\-[0-3]|0|0\.\d*|1|1\.0)' # -4.5 to 1
advancedSpaces = {
    'rec709TF': re.compile(_lbr+_rec+r',\s*'+_rec+r',\s*'+_rec+_rbr), # rec709TF adjusted RGB from -4.5 to 1 + alpha from 0 to 1
    'rec709TFa': re.compile(_lbr+_rec+r',\s*'+_rec+r',\s*'+_rec+r',\s*'+_1+_rbr), # rec709TF adjusted RGB from -4.5 to 1 + alpha from 0 to 1
    'srgbTF': re.compile(_lbr+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+r'\-?'+_1+_rbr), # srgbTF from -1 to 1 + alpha from 0 to 1
    'srgbTFa': re.compile(_lbr+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+r'\-?'+_1+r',\s*'+_1+_rbr), # srgbTF from -1 to 1 + alpha from 0 to 1
    'lms': re.compile(_lbr + r'\-?' + _1 + r',\s*' + r'\-?' + _1 + r',\s*' + r'\-?' + _1 + _rbr),  # LMS from -1 to 1
    'lmsa': re.compile(_lbr + r'\-?' + _1 + r',\s*' + r'\-?' + _1 + r',\s*' + r'\-?' + _1 + r',\s*' + r'\-?' + _1 + _rbr),  # LMS + alpha from -1 to 1
    'dkl': re.compile(_lbr + r'\-?' + r'\d*.?\d*' + r',\s*' + r'\-?' + r'\d*.?\d*' + r',\s*' + r'\-?' + r'\d*.?\d*' + _rbr), # DKL placeholder: Accepts any values
    'dkla': re.compile(_lbr + r'\-?' + r'\d*.?\d*' + r',\s*' + r'\-?' + r'\d*.?\d*' + r',\s*' + r'\-?' + r'\d*.?\d*' + r',\s*' + r'\-?' + r'\d*.?\d*' + _rbr) # DKLA placeholder: Accepts any values
}


class AdvancedColor(Color):
    def __init__(self, color, space, conematrix=None):
        Color.__init__(self, color, space)
        # Set matrix for cone conversion
        if conematrix is not None:
            self.conematrix = conematrix
        else:
            # Set _conematrix specifically as undefined, rather than just setting to default
            self._conematrix = None

    @staticmethod
    def getSpace(color, debug=False):
        """Overrides Color.getSpace, drawing from a much more comprehensive library of colour spaces"""
        if isinstance(color, Color):
            return color._requestedSpace
        # Check for advanced colours spaces
        possible = [space for space in advancedSpaces
                    if advancedSpaces[space].fullmatch(str(color))]
        # Append basic colour spaces
        basic = Color.getSpace(color, debug=True)
        possible += basic
        # Return full list if debug or multiple, else return first value
        if debug or len(possible) > 1:
            return possible
        else:
            return possible[0]

    def validate(self, color, against=None, enforce=None):
        # If not checking against anything, check against everything
        if not against:
            against = list(advancedSpaces)
        # If looking for a string, convert from other forms it could be in
        if enforce == str:
            color = str(color).lower()
        # If looking for a tuple, convert from other forms it could be in
        if enforce == tuple:
            if isinstance(color, str):
                color = [float(n) for n in color.strip('[]()').split(',')]
            if isinstance(color, list):
                color = tuple(color)
        # Get possible colour spaces
        possible = AdvancedColor.getSpace(color)
        if isinstance(possible, str):
            possible = [possible]
        # Return if any matches
        for space in possible:
            if space in against:
                return color
        # If no matches...
        self.named = None
        return None

    @property
    def rec709TFa(self):
        """Apply the Rec. 709 transfer function (or gamma) to linear RGB values.

            This transfer function is defined in the ITU-R BT.709 (2015) recommendation
            document (http://www.itu.int/rec/R-REC-BT.709-6-201506-I/en) and is
            commonly used with HDTV televisions.
            """
        if not self.rgb:
            return
        if 'rec709TFa' not in self._cache:
            self._cache['rec709TFa'] = tuple(1.099 * c ** 0.45 - 0.099
                         if c >= 0.018
                         else 4.5 * c
                         for c in self.rgb) + (self.rgba1[-1],)
        return self._cache['rec709TFa']

    @rec709TFa.setter
    def rec709TFa(self, color):
        # Validate
        color = self.validate(color, against=['rec709TF', 'rec709TFa'], enforce=tuple)
        if not color:
            return
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
        # Clear outdated values from cache
        self._cache = {}

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
        if not self.rgb:
            return
        if 'srgbTFa' not in self._cache:
            self._cache['srgbTFa'] = tuple(c * 12.92
                         if c <= 0.0031308
                         else (1.0 + 0.055) * c ** (1.0 / 2.4) - 0.055
                         for c in self.rgb) + (self.rgba1[-1],)
        return self._cache['srgbTFa']
    @srgbTFa.setter
    def srgbTFa(self, color):
        # Validate
        color = self.validate(color, against=['srgbTF', 'srgbTFa'], enforce=tuple)
        if not color:
            return
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
        # Clear outdated values from cache
        self._cache = {}

    @property
    def srgbTF(self):
        if self.srgbTFa:
            return self.srgbTFa[:-1]
    @srgbTF.setter
    def srgbTF(self, color):
        self.srgbTFa = color

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
        if 'lmsa' not in self._cache:
            if self._conematrix is None:
                self.conematrix = None
            # its easier to use in the other orientation!
            rgb_3xN = numpy.transpose(self.rgb)
            rgb_to_cones = numpy.linalg.inv(self.conematrix)
            lms = numpy.dot(rgb_to_cones, rgb_3xN)
            self._cache['lmsa'] = tuple(numpy.transpose(lms))  # return in the shape we received it
        return self._cache['lmsa']

    @lmsa.setter
    def lmsa(self, color):
        """Convert from cone space (Long, Medium, Short) to RGB.

        Requires a conversion matrix, which will be generated from generic
        Sony Trinitron phosphors if not supplied (note that you will not get
        an accurate representation of the color space unless you supply a
        conversion matrix)
        """
        # Validate
        color = self.validate(str(color).lower(), against=['lms', 'lmsa'], enforce=tuple)
        if not color:
            return
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
        # Clear outdated values from cache
        self._cache = {}

    @property
    def lms(self):
        if self.lmsa:
            return self.lmsa[:-1]

    @lms.setter
    def lms(self, color):
        self.lmsa = color

    @property
    def dkla(self):
        if 'dkla' in self._cache:
            return self._cache['dkla']
        else:
            logging.error(f"Conversion *to* dkl is not supported, dkl values can only be retrieved when Color was originally specified in dkl")
    @dkla.setter
    def dkla(self, color):
        # Extract values and convert to numpy
        d, k, l, *a = color
        nd = numpy.zeros(3)
        nd[:] = [d,k,l]
        # Do conversion
        self.rgb = tuple( dkl2rgb(nd) )
        if a:
            self.alpha = a[0]
        else:
            self.alpha = 1
        # Cache values
        self._cache = {'dkl': (d, k, l),
                       'dkla': (d, k, l, a)}
    @property
    def dkl(self):
        if 'dkl' in self._cache:
            return self._cache['dkl']
        else:
            logging.error(f"Conversion *to* dkl is not supported, dkl values can only be retrieved when Color was originally specified in dkl")
    @dkl.setter
    def dkl(self, color):
        self.dkla = color


"""----------Legacy-----------------"""
# Old reference tables
colors = colorNames
colorsHex = {key: Color(key, 'named').hex for key in colors}
colors255 = {key: Color(key, 'named').rgb255 for key in colors}

# Old conversion functions
def hex2rgb255(hexColor):
    """Convert a hex color string (e.g. "#05ff66") into an rgb triplet
    ranging from 0:255
    """
    col = Color(hexColor, 'hex')
    if len(hexColor.strip('#')) == 6:
        return col.rgb255
    elif len(hexColor.strip('#')) == 8:
        return col.rgba255

def isValidColor(color):
    """check color validity (equivalent to existing checks in _setColor)
    """
    if len(Color.getSpace(color, True)):
        return True
    else:
        return False

def unpackColors(colors):  # used internally, not exported by __all__
    """Reshape an array of color values to Nx3 format.

    Many color conversion routines operate on color data in Nx3 format, where
    rows are color space coordinates. 1x3 and NxNx3 input are converted to Nx3
    format. The original shape and dimensions are also returned, allowing the
    color values to be returned to their original format using 'reshape'.

    Parameters
    ----------
    colors : ndarray, list or tuple of floats
        Nx3 or NxNx3 array of colors, last dim must be size == 3 specifying each
        color coordinate.

    Returns
    -------
    tuple
        Nx3 ndarray of converted colors, original shape, original dims.

    """
    # handle the various data types and shapes we might get as input
    colors = numpy.asarray(colors, dtype=float)

    orig_shape = colors.shape
    orig_dim = colors.ndim
    if orig_dim == 1 and orig_shape[0] == 3:
        colors = numpy.array(colors, ndmin=2)
    elif orig_dim == 2 and orig_shape[1] == 3:
        pass  # NOP, already in correct format
    elif orig_dim == 3 and orig_shape[2] == 3:
        colors = numpy.reshape(colors, (-1, 3))
    else:
        raise ValueError(
            "Invalid input dimensions or shape for input colors.")

    return colors, orig_shape, orig_dim

def dkl2rgb(dkl, conversionMatrix=None):
    """Convert from DKL color space (Derrington, Krauskopf & Lennie) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that this will not be
    an accurate representation of the color space unless you supply a
    conversion matrix).

    usage::

        rgb(Nx3) = dkl2rgb(dkl_Nx3(el,az,radius), conversionMatrix)
        rgb(NxNx3) = dkl2rgb(dkl_NxNx3(el,az,radius), conversionMatrix)

    """
    if conversionMatrix is None:
        conversionMatrix = numpy.asarray([
            # (note that dkl has to be in cartesian coords first!)
            # LUMIN    %L-M    %L+M-S
            [1.0000, 1.0000, -0.1462],  # R
            [1.0000, -0.3900, 0.2094],  # G
            [1.0000, 0.0180, -1.0000]])  # B
        logging.warning('This monitor has not been color-calibrated. '
                        'Using default DKL conversion matrix.')

    if len(dkl.shape) == 3:
        dkl_NxNx3 = dkl
        # convert a 2D (image) of Spherical DKL colours to RGB space
        origShape = dkl_NxNx3.shape  # remember for later
        NxN = origShape[0] * origShape[1]  # find nPixels
        dkl = numpy.reshape(dkl_NxNx3, [NxN, 3])  # make Nx3
        rgb = dkl2rgb(dkl, conversionMatrix)  # convert
        return numpy.reshape(rgb, origShape)  # reshape and return

    else:
        dkl_Nx3 = dkl
        # its easier to use in the other orientation!
        dkl_3xN = numpy.transpose(dkl_Nx3)
        if numpy.size(dkl_3xN) == 3:
            RG, BY, LUM = sph2cart(dkl_3xN[0],
                                   dkl_3xN[1],
                                   dkl_3xN[2])
        else:
            RG, BY, LUM = sph2cart(dkl_3xN[0, :],
                                   dkl_3xN[1, :],
                                   dkl_3xN[2, :])
        dkl_cartesian = numpy.asarray([LUM, RG, BY])
        rgb = numpy.dot(conversionMatrix, dkl_cartesian)

        # return in the shape we received it:
        return numpy.transpose(rgb)

def lms2rgb(lms_Nx3, conversionMatrix=None):
    """Convert from cone space (Long, Medium, Short) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that you will not get
    an accurate representation of the color space unless you supply a
    conversion matrix)

    usage::

        rgb_Nx3 = lms2rgb(dkl_Nx3(el,az,radius), conversionMatrix)

    """

    col = Color(tuple(lms_Nx3), 'lms')
    if len(lms_Nx3) == 3:
        return unpackColors(col.rgb)
    elif len(lms_Nx3) == 4:
        return unpackColors(col.rgba)

def hsv2rgb(hsv_Nx3):
    """Convert from HSV color space to RGB gun values.

    usage::

        rgb_Nx3 = hsv2rgb(hsv_Nx3)

    Note that in some uses of HSV space the Hue component is given in
    radians or cycles (range 0:1]). In this version H is given in
    degrees (0:360).

    Also note that the RGB output ranges -1:1, in keeping with other
    PsychoPy functions.
    """
    # based on method in
    # http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB

    col = Color(tuple(hsv_Nx3), 'hsv')
    if len(hsv_Nx3) == 3:
        return unpackColors(col.rgb)
    elif len(hsv_Nx3) == 4:
        return unpackColors(col.rgba)