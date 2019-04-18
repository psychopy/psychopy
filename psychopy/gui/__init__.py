#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Graphical user interface elements for experiments.

This lib will attempt to use PyQt (4 or 5) if possible and will revert to
using wxPython if PyQt is not found.
"""

from __future__ import absolute_import, print_function
import sys
from .. import constants

# check if wx has been imported. If so, import here too and check for app
if 'wx' in sys.modules:
    import wx
    wxApp = wx.GetApp()
else:
    wxApp = None

# then setup prefs for
haveQt = False  # until we confirm otherwise
if wxApp is None:  # i.e. don't try this if wx is already running
    # set order for attempts on PyQt4/PyQt5
    if constants.PY3:  # much more like to have PyQt5 on Python3
        importOrder = ['PyQt5', 'PyQt4']
    else:  # more likely the other way on Py27
        importOrder = ['PyQt4', 'PyQt5']
    # then check each in turn
    for libname in importOrder:
        try:
            exec("import {}".format(libname))
            haveQt = libname
            break
        except ImportError:
            pass

# now we know what we can import let's import the rest
if haveQt:
    from .qtgui import *
else:
    try:
        from .wxgui import *
    except ImportError:
        print("Neither wxPython nor PyQt could be imported "
              "so gui is not available")
