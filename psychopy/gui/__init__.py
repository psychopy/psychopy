#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Graphical user interface elements for experiments.

This lib will attempt to use PyQt (4 or 5) if possible and will revert to
using wxPython if PyQt is not found.
"""

from __future__ import absolute_import, print_function

haveQt = False  # until we find otherwise

import wx

if wx.GetApp() is None:  # i.e. don't try this if wx is already running
    try:
        import PyQt4
        haveQt = True
    except ImportError:
        try:
            import PyQt5
            haveQt = True
        except ImportError:
            haveQt = False

if haveQt:
    from .qtgui import *
else:
    try:
        from .wxgui import *
    except ImportError:
        print("Neither wxPython nor PyQt could be imported "
              "so gui is not available")
