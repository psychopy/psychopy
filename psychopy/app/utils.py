#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""utility classes for the Builder
"""

from __future__ import absolute_import, division, print_function
from builtins import object

from wx.lib.agw.aui.aui_constants import *
from wx.lib.agw.aui.aui_utilities import IndentPressedBitmap, ChopText, TakeScreenShot
import sys
import wx
import wx.lib.agw.aui as aui
from psychopy import logging
from psychopy.app. style import cLib, cs



class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """

    def __init__(self, targetFrame):
        wx.FileDropTarget.__init__(self)
        self.target = targetFrame

    def OnDropFiles(self, x, y, filenames):
        logging.debug(
            'PsychoPyBuilder: received dropped files: %s' % filenames)
        for fname in filenames:
            if fname.endswith('.psyexp') or fname.lower().endswith('.py'):
                self.target.fileOpen(filename=fname)
            else:
                logging.warning(
                    'dropped file ignored: did not end in .psyexp or .py')
        return True


class WindowFrozen(object):
    """
    Equivalent to wxWindowUpdateLocker.

    Usage::

        with WindowFrozen(wxControl):
            update multiple things
        # will automatically thaw here

    """

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def __enter__(self):  # started the with... statement
        # Freeze should not be called if platform is win32.
        if sys.platform == 'win32':
            return self.ctrl

        # check it hasn't been deleted
        #
        # Don't use StrictVersion() here, as `wx` doesn't follow the required
        # numbering scheme.
        if self.ctrl is not None and wx.__version__[:3] <= '2.8':
            self.ctrl.Freeze()
        return self.ctrl

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Thaw should not be called if platform is win32.
        if sys.platform == 'win32':
            return
        # check it hasn't been deleted
        if self.ctrl is not None and self.ctrl.IsFrozen():
            self.ctrl.Thaw()


def getSystemFonts(encoding='system', fixedWidthOnly=False):
    """Get a list of installed system fonts.

    Parameters
    ----------
    encoding : str
        Get fonts with matching encodings.
    fixedWidthOnly : bool
        Return on fixed width fonts.

    Returns
    -------
    list
        List of font facenames.

    """
    fontEnum = wx.FontEnumerator()

    encoding = "FONTENCODING_" + encoding.upper()
    if hasattr(wx, encoding):
        encoding = getattr(wx, encoding)

    return fontEnum.GetFacenames(encoding, fixedWidthOnly=fixedWidthOnly)

class PsychoPyTabArt(aui.AuiDefaultTabArt):
    def __init__(self):
        aui.AuiDefaultTabArt.__init__(self)

        self.SetDefaultColours()

    def SetDefaultColours(self):
        """
        Sets the default colours, which are calculated from the given base colour.

        :param `base_colour`: an instance of :class:`wx.Colour`. If defaulted to ``None``, a colour
         is generated accordingly to the platform and theme.
        """

        self.SetBaseColour( wx.Colour(cs['tab_active']) )
        self._background_top_colour = wx.Colour(cs['note_bg'])
        self._background_bottom_colour = wx.Colour(cs['note_bg'])

        self._tab_top_colour = wx.Colour(cs['tab_active'])
        self._tab_bottom_colour = wx.Colour(cs['tab_active'])
        self._tab_gradient_highlight_colour = wx.Colour(cs['tab_active'])
        self._border_colour = wx.Colour(cs['tab_active'])
        self._border_pen = wx.Pen(self._border_colour)

        self._tab_inactive_top_colour = wx.Colour(cs['tab_face'])
        self._tab_inactive_bottom_colour = wx.Colour(cs['tab_face'])

        self._tab_text_colour = self._tab_text_colour = lambda page: page.text_colour
        self._tab_disabled_text_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

    def DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control=False):
        """
        Extends AuiDefaultTabArt.DrawTab to add a transparent border to inactive tabs
        """
        if page.active:
            self._border_pen = wx.Pen(self._border_colour)
        else:
            self._border_pen = wx.TRANSPARENT_PEN

        out_tab_rect, out_button_rect, x_extent = aui.AuiDefaultTabArt.DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control)

        return out_tab_rect, out_button_rect, x_extent