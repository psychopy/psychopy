#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""utility classes for the Builder
"""

from __future__ import (absolute_import, print_function, division)

import sys
import wx
from psychopy import logging


class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """
    def __init__(self, builder):
        wx.FileDropTarget.__init__(self)
        self.builder = builder
    def OnDropFiles(self, x, y, filenames):
        logging.debug('PsychoPyBuilder: received dropped files: %s' % filenames)
        for filename in filenames:
            if filename.endswith('.psyexp') or filename.lower().endswith('.py'):
                self.builder.fileOpen(filename=filename)
            else:
                logging.warning('dropped file ignored: did not end in .psyexp or .py')


class WindowFrozen(object):
    """
    Equivalent to wxWindowUpdateLocker.

    Usage::

        with WindowFrozen(wxControl):
          update multiple things
        #will automatically thaw here

    """
    def __init__(self, ctrl):
        self.ctrl = ctrl
    def __enter__(self):#started the with... statement
        if sys.platform == 'win32': #Freeze should not be called if platform is win32.
            return self.ctrl
        if self.ctrl is not None and wx.__version__[:3]<='2.8':#check it hasn't been deleted
            self.ctrl.Freeze()
        return self.ctrl
    def __exit__(self, exc_type, exc_val, exc_tb):#ended the with... statement
        if sys.platform == 'win32': #Thaw should not be called if platform is win32.
            return
        if self.ctrl is not None and self.ctrl.IsFrozen():#check it hasn't been deleted
            self.ctrl.Thaw()
