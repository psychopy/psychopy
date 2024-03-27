import numpy
import wx

from . import theme


class BaseColor(wx.Colour):
    """
    Essentially a wx.Colour with some extra features for convenience
    """
    def __add__(self, other):
        # Get own RGB value
        rgb = numpy.array([self.Red(), self.Green(), self.Blue()])
        # Get adjustment
        adj = self._getAdj(other)
        # Do addition
        result = numpy.clip(rgb + adj, 0, 255)
        # Create new wx.Colour object from result
        return wx.Colour(result[0], result[1], result[2], self.Alpha())

    def __sub__(self, other):
        # Get own RGB value
        rgb = numpy.array([self.Red(), self.Green(), self.Blue()])
        # Get adjustment
        adj = self._getAdj(other)
        # Do subtraction
        result = numpy.clip(rgb - adj, 0, 255)
        # Create new wx.Colour object from result
        return wx.Colour(result[0], result[1], result[2], self.Alpha())

    def __mul__(self, other):
        assert isinstance(other, (int, float)), (
            "BaseColor can only be multiplied by a float (0-1) or int (0-255), as this sets its alpha."
        )
        # If given as a float, convert to 255
        if isinstance(other, float):
            other = round(other * 255)
        # Set alpha
        return wx.Colour(self.Red(), self.Green(), self.Blue(), alpha=other)

    @staticmethod
    def _getAdj(other):
        """
        Get the adjustment indicated by another object given to this as an operator for __add__ or __sub__
        """
        # If other is also a wx.Colour, adjustment is its RGBA value
        if isinstance(other, wx.Colour):
            adj = numpy.array([other.Red(), other.Green(), other.Blue()])
        # If other is an int, adjustment is itself*15
        elif isinstance(other, int):
            adj = other * 15
        # Otherwise, just treat it as an RGBA array
        else:
            adj = numpy.array(other)

        return adj


# PsychoPy brand colours
scheme = {
    'none': BaseColor(0, 0, 0, 0),
    'white': BaseColor(255, 255, 255, 255),
    'offwhite': BaseColor(242, 242, 242, 255),
    'grey': BaseColor(102, 102, 110, 255),
    'lightgrey': BaseColor(172, 172, 176, 255),
    'black': BaseColor(0, 0, 0, 255),
    'red': BaseColor(242, 84, 91, 255),
    'purple': BaseColor(195, 190, 247, 255),
    'blue': BaseColor(2, 169, 234, 255),
    'green': BaseColor(108, 204, 116, 255),
    'yellow': BaseColor(241, 211, 2, 255),
    'orange': BaseColor(236, 151, 3, 255),
}


class AppColors(dict):
    light = {
        "text": scheme['black'],
        "frame_bg": scheme['offwhite'] - 1,
        "docker_bg": scheme['offwhite'] - 2,
        "docker_fg": scheme['black'],
        "panel_bg": scheme['offwhite'],
        "tab_bg": scheme['white'],
        "bmpbutton_bg_hover": scheme['offwhite'] - 1,
        "bmpbutton_fg_hover": scheme['black'],
        "txtbutton_bg_hover": scheme['red'],
        "txtbutton_fg_hover": scheme['offwhite'],
        "rt_timegrid": scheme['grey'],
        "rt_comp": scheme['blue'],
        "rt_comp_force": scheme['orange'],
        "rt_comp_disabled": scheme['offwhite'] - 2,
        "rt_static": scheme['red'] * 75,
        "rt_static_disabled": scheme['grey'] * 75,
        "fl_routine_fg": scheme['offwhite'] + 1,
        "fl_routine_bg_slip": scheme['blue'],
        "fl_routine_bg_nonslip": scheme['green'],
        "fl_flowline_bg": scheme['grey'],
        "fl_flowline_fg": scheme['white'] + 1,
    }
    dark = {
        "text": scheme['offwhite'],
        "frame_bg": scheme['grey'] - 1,
        "docker_bg": scheme['grey'] - 2,
        "docker_fg": scheme['offwhite'],
        "panel_bg": scheme['grey'],
        "tab_bg": scheme['grey'] + 1,
        "bmpbutton_bg_hover": scheme['grey'] + 1,
        "bmpbutton_fg_hover": scheme['offwhite'],
        "txtbutton_bg_hover": scheme['red'],
        "txtbutton_fg_hover": scheme['offwhite'],
        "rt_timegrid": scheme['grey'] + 2,
        "rt_comp": scheme['blue'],
        "rt_comp_force": scheme['orange'],
        "rt_comp_disabled": scheme['grey'],
        "rt_static": scheme['red'] * 75,
        "rt_static_disabled": scheme['white'] * 75,
        "fl_routine_fg": scheme['white'],
        "fl_routine_bg_slip": scheme['blue'],
        "fl_routine_bg_nonslip": scheme['green'],
        "fl_flowline_bg": scheme['offwhite'] - 1,
        "fl_flowline_fg": scheme['black'],
    }
    contrast_white = {
        "text": scheme['black'],
        "frame_bg": scheme['offwhite'] + 1,
        "docker_bg": scheme['yellow'],
        "docker_fg": scheme['black'],
        "panel_bg": scheme['offwhite'],
        "tab_bg": scheme['offwhite'] + 1,
        "bmpbutton_bg_hover": scheme['red'],
        "bmpbutton_fg_hover": scheme['offwhite'],
        "txtbutton_bg_hover": scheme['red'],
        "txtbutton_fg_hover": scheme['offwhite'],
        "rt_timegrid": scheme['black'],
        "rt_comp": scheme['blue'],
        "rt_comp_force": scheme['orange'],
        "rt_comp_disabled": scheme['grey'],
        "rt_static": scheme['red'] * 75,
        "rt_static_disabled": scheme['grey'] * 75,
        "fl_routine_fg": scheme['offwhite'] + 1,
        "fl_routine_bg_slip": scheme['blue'],
        "fl_routine_bg_nonslip": scheme['green'],
        "fl_flowline_bg": scheme['black'],
        "fl_flowline_fg": scheme['offwhite'] + 1,
    }

    contrast_black = {
        "text": scheme['offwhite'],
        "frame_bg": scheme['black'],
        "docker_bg": "#800080",
        "docker_fg": scheme['offwhite'],
        "panel_bg": scheme['black'] + 1,
        "tab_bg": scheme['black'] + 1,
        "bmpbutton_bg_hover": scheme['red'],
        "bmpbutton_fg_hover": scheme['offwhite'],
        "txtbutton_bg_hover": scheme['red'],
        "txtbutton_fg_hover": scheme['offwhite'],
        "rt_timegrid": scheme['offwhite'],
        "rt_comp": scheme['blue'],
        "rt_comp_force": scheme['orange'],
        "rt_comp_disabled": scheme['grey'],
        "rt_static": scheme['red'] * 75,
        "rt_static_disabled": scheme['grey'] * 75,
        "fl_routine_fg": scheme['white'],
        "fl_routine_bg_slip": scheme['blue'],
        "fl_routine_bg_nonslip": scheme['green'],
        "fl_flowline_bg": scheme['offwhite'],
        "fl_flowline_fg": scheme['black'],
    }

    pink = {
        "text": scheme['red'] - 10,
        "frame_bg": scheme['red'] + 8,
        "docker_bg": scheme['red'] + 7,
        "docker_fg": scheme['red'] - 10,
        "panel_bg": scheme['red'] + 9,
        "tab_bg": scheme['red'] + 10,
        "bmpbutton_bg_hover": scheme['red'] + 7,
        "bmpbutton_fg_hover": scheme['red'] - 10,
        "txtbutton_bg_hover": scheme['red'] + 7,
        "txtbutton_fg_hover": scheme['red'] - 10,
        "rt_timegrid": scheme['red'] + 4,
        "rt_comp": scheme['blue'] + 12,
        "rt_comp_force": scheme['orange'] + 12,
        "rt_comp_disabled": scheme['red'] + 6,
        "rt_static": scheme['white'] * 170,
        "rt_static_disabled": scheme['red'] * 21,
        "fl_routine_fg": scheme['red'] - 10,
        "fl_routine_bg_slip": scheme['blue'] + 12,
        "fl_routine_bg_nonslip": scheme['green'] + 8,
        "fl_flowline_bg": scheme['red'] + 4,
        "fl_flowline_fg": scheme['red'] - 10,
    }

    def __getitem__(self, item):
        # When getting an attribute of this object, return the key from the theme-appropriate dict
        return getattr(self, theme.app)[item]


app = AppColors()

