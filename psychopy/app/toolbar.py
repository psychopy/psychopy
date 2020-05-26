#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines the behavior of Psychopy's toolbar within builder and coder view
Part of the PsychoPy library
Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, division, print_function

from pkg_resources import parse_version
import wx
import wx.stc
from wx.lib import platebtn, scrolledpanel

try:
    from wx import aui
except ImportError:
    import wx.lib.agw.aui as aui  # some versions of phoenix
try:
    from wx.adv import PseudoDC
except ImportError:
    from wx import PseudoDC

if parse_version(wx.__version__) < parse_version('4.0.3'):
    wx.NewIdRef = wx.NewId

import sys
import os
import glob
import copy
import traceback
import codecs
import numpy

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # python 2.x

from psychopy.localization import _translate

from .. import experiment
from . import dialogs, icons
from .builder import builder
from .coder import coder
from psychopy.app.style import cLib, cs
from .icons import getAllIcons, combineImageEmblem
from psychopy import logging, constants, data
from psychopy.tools.filetools import mergeFolder
from .builder.dialogs import (DlgComponentProperties, DlgExperimentProperties,
                      DlgCodeComponentProperties, DlgLoopProperties)
from .utils import FileDropTarget, WindowFrozen
from psychopy.experiment import components
from builtins import str
from psychopy.app import pavlovia_ui
from psychopy.projects import pavlovia

from psychopy.scripts.psyexpCompile import generateScript

# _localized separates internal (functional) from displayed strings
# long form here allows poedit string discovery
_localized = {
    'Field': _translate('Field'),
    'Default': _translate('Default'),
    'Favorites': _translate('Favorites'),
    'Stimuli': _translate('Stimuli'),
    'Responses': _translate('Responses'),
    'Custom': _translate('Custom'),
    'I/O': _translate('I/O'),
    'Add to favorites': _translate('Add to favorites'),
    'Remove from favorites': _translate('Remove from favorites'),
    # contextMenuLabels
    'edit': _translate('edit'),
    'remove': _translate('remove'),
    'copy': _translate('copy'),
    'move to top': _translate('move to top'),
    'move up': _translate('move up'),
    'move down': _translate('move down'),
    'move to bottom': _translate('move to bottom')
}

class PsychopyToolbar(wx.ToolBar):
    """Toolbar for the Builder/Coder Frame"""
    def __init__(self, frame):
        wx.ToolBar.__init__(self, frame)
        self.frame = frame

        # Configure toolbar appearance
        self.SetWindowStyle(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.SetBackgroundColour(cs['toolbar_bg'])
        # Set icon size (16 for win/linux small mode, 32 for everything else
        if (sys.platform == 'win32' or sys.platform.startswith('linux')) \
                and not self.frame.appPrefs['largeIcons']:
            self.iconSize = 16
        else:
            self.iconSize = 32  # mac: 16 either doesn't work, or looks bad
        self.SetToolBitmapSize((self.iconSize, self.iconSize))
        # OS-dependent tool-tips
        ctrlKey = 'Ctrl+'
        if sys.platform == 'darwin':
            ctrlKey = 'Cmd+'
        # keys are the keyboard keys, not the keys of the dict
        self.keys = {k: self.frame.app.keys[k].replace('Ctrl+', ctrlKey)
                for k in self.frame.app.keys}
        self.keys['none'] = ''

        # Create tools
        if isinstance(frame, builder.BuilderFrame):
            self.AddPsychopyTool('filenew', 'New', 'new',
                            "Create new experiment file",
                            self.frame.app.newBuilderFrame) # New
            self.AddPsychopyTool('fileopen', 'Open', 'open',
                                 "Open an existing experiment file",
                                 self.frame.fileOpen)  # Open
            self.frame.bldrBtnSave = \
                self.AddPsychopyTool('filesave', 'Save', 'save',
                                 "Save current experiment file",
                                 self.frame.fileSave)  # Save
            self.AddPsychopyTool('filesaveas', 'Save As...', 'saveAs',
                                 "Save current experiment file as...",
                                 self.frame.fileSaveAs)  # SaveAs
            self.frame.bldrBtnUndo = \
                self.AddPsychopyTool('undo', 'Undo', 'undo',
                                 "Undo last action",
                                 self.frame.undo)  # Undo
            self.frame.bldrBtnRedo = \
                self.AddPsychopyTool('redo', 'Redo', 'redo',
                                 "Redo last action",
                                 self.frame.redo)  # Redo
            self.AddSeparator() # Seperator
            self.AddPsychopyTool('monitors', 'Monitor Center', 'none',
                                 "Monitor settings and calibration",
                                 self.frame.app.openMonitorCenter)  # Monitor Center
            self.AddPsychopyTool('cogwindow', 'Experiment Settings', 'none',
                                 "Edit experiment settings",
                                 self.frame.setExperimentSettings)  # Settings
            self.AddSeparator()
            self.AddPsychopyTool('compile', 'Compile Script', 'compileScript',
                                 "Compile to script",
                                 self.frame.compileScript)  # Compile
            self.frame.bldrBtnRun = self.AddPsychopyTool(('run', 'runner'), 'Run', 'runScript',
                                 "Run experiment",
                                 self.frame.runFile)  # Run
        elif isinstance(frame, coder.CoderFrame):
            self.AddPsychopyTool('filenew', 'New', 'new',
                                 "Create new experiment file",
                                 self.frame.app.newBuilderFrame)  # New
            self.AddPsychopyTool('fileopen', 'Open', 'open',
                                 "Open an existing experiment file",
                                 self.frame.fileOpen)  # Open
            self.frame.bldrBtnSave = \
                self.AddPsychopyTool('filesave', 'Save', 'save',
                                     "Save current experiment file",
                                     self.frame.fileSave)  # Save
            self.AddPsychopyTool('filesaveas', 'Save As...', 'saveAs',
                                 "Save current experiment file as...",
                                 self.frame.fileSaveAs)  # SaveAs
            self.frame.bldrBtnUndo = \
                self.AddPsychopyTool('undo', 'Undo', 'undo',
                                     "Undo last action",
                                     self.frame.undo)  # Undo
            self.frame.bldrBtnRedo = \
                self.AddPsychopyTool('redo', 'Redo', 'redo',
                                     "Redo last action",
                                     self.frame.redo)  # Redo
            self.AddSeparator()  # Seperator
            self.AddPsychopyTool('monitors', 'Monitor Center', 'none',
                                 "Monitor settings and calibration",
                                 self.frame.app.openMonitorCenter)  # Monitor Center
            self.AddPsychopyTool('color', 'Color Picker', 'none',
                                 "Color Picker -> clipboard",
                                 self.frame.app.colorPicker)
            self.AddSeparator()
            self.frame.bldrBtnRun = self.AddPsychopyTool(('run', 'runner'), 'Run', 'runScript',
                                                         "Run experiment",
                                                         self.frame.runFile)  # Run
        self.AddSeparator()
        pavButtons = pavlovia_ui.toolbar.PavloviaButtons(frame, toolbar=self, tbSize=self.iconSize)
        pavButtons.addPavloviaTools()
        frame.btnHandles.update(pavButtons.btnHandles)

        # Finished setup. Make it happen
        self.Realize()


    def AddPsychopyTool(self, fName, label, shortcut, tooltip, func):
        # Load in graphic resource
        rc = self.frame.app.prefs.paths['resources']
        if isinstance(fName, str):
            # If one stimulus is supplied, read bitmap
            bmp = wx.Bitmap(os.path.join(
                rc, fName+'%i.png' % self.iconSize
            ), wx.BITMAP_TYPE_PNG)
        elif isinstance(fName, tuple) and len(fName) == 2:
            # If two are supplied, create combined bitmap
            bmp = combineImageEmblem(os.path.join(rc, fName[0]+'%i.png' % self.iconSize),
                               os.path.join(rc, fName[1]+'16.png'),
                               pos='bottom_right')
        else:
            return
        # Create tool object
        if 'phoenix' in wx.PlatformInfo:
            item = self.AddTool(wx.ID_ANY,
                              _translate(label + " [%s]") % self.keys[shortcut],
                              bmp,
                              _translate(tooltip))
        else:
            item = self.AddSimpleTool(wx.ID_ANY,
                                    bmp,
                                    _translate(label + " [%s]") % self.keys[shortcut],
                                    _translate(tooltip))
        # Bind function
        self.Bind(wx.EVT_TOOL, func, item)
        return item