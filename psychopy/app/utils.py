#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""utility classes for the Builder
"""
import glob
import os
from pathlib import Path

from wx.lib.agw.aui.aui_constants import *
from wx.lib.agw.aui.aui_utilities import IndentPressedBitmap, ChopText, TakeScreenShot
import sys
import wx
import wx.lib.agw.aui as aui
from wx.lib import platebtn

import psychopy
from psychopy import logging
from . import pavlovia_ui
from . import icons
from .themes import ThemeMixin, IconCache
from psychopy.localization import _translate
from psychopy.tools.stringtools import prettyname


class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """

    def __init__(self, targetFrame):
        wx.FileDropTarget.__init__(self)
        self.target = targetFrame
        self.app = targetFrame.app

    def OnDropFiles(self, x, y, filenames):
        logging.debug(
            'PsychoPyBuilder: received dropped files: %s' % filenames)
        for fname in filenames:
            if isinstance(self.target, psychopy.app.coder.CoderFrame) and wx.GetKeyState(wx.WXK_ALT):
                # If holding ALT and on coder, insert filename into current coder doc
                if self.app.coder:
                    if self.app.coder.currentDoc:
                        self.app.coder.currentDoc.AddText(fname)
            if isinstance(self.target, psychopy.app.runner.RunnerFrame):
                # If on Runner, load file to run
                self.app.showRunner()
                self.app.runner.addTask(fileName=fname)
            elif fname.lower().endswith('.psyexp'):
                # If they dragged on a .psyexp file, open it in in Builder
                self.app.showBuilder()
                self.app.builder.fileOpen(filename=fname)
            else:
                # If they dragged on any other file, try to open it in Coder (if it's not text, this will give error)
                self.app.showCoder()
                self.app.coder.fileOpen(filename=fname)
        return True


class WindowFrozen():
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


class PsychopyToolbar(wx.ToolBar, ThemeMixin):
    """Toolbar for the Builder/Coder Frame"""
    def __init__(self, frame):
        wx.ToolBar.__init__(self, frame)
        self.frame = frame
        self.app = self.frame.app
        self._needMakeTools = True
        # Configure toolbar appearance
        self.SetWindowStyle(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_NODIVIDER)
        # self.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
        # Set icon size (16 for win/linux small mode, 32 for everything else
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
        # self.makeTools()  # will be done when theme is applied
        self.buttons = {}
        # Finished setup. Make it happen

    def makeTools(self):
        frame = self.frame
        # Create tools
        cl = frame.__class__.__name__
        pavButtons = pavlovia_ui.toolbar.PavloviaButtons(
                frame, toolbar=self, tbSize=self.iconSize)
        if frame.__class__.__name__ == 'BuilderFrame':
            self.addPsychopyTool(
                    name='filenew',
                    label=_translate('New'),
                    shortcut='new',
                    tooltip=_translate("Create new experiment file"),
                    func=self.frame.app.newBuilderFrame)  # New
            self.addPsychopyTool(
                    name='fileopen',
                    label=_translate('Open'),
                    shortcut='open',
                    tooltip=_translate("Open an existing experiment file"),
                    func=self.frame.fileOpen)  # Open
            self.frame.bldrBtnSave = self.addPsychopyTool(
                        name='filesave',
                        label=_translate('Save'),
                        shortcut='save',
                        tooltip=_translate("Save current experiment file"),
                        func=self.frame.fileSave)  # Save
            self.addPsychopyTool(
                    name='filesaveas',
                    label=_translate('Save As...'),
                    shortcut='saveAs',
                    tooltip=_translate("Save current experiment file as..."),
                    func=self.frame.fileSaveAs)  # SaveAs
            self.frame.bldrBtnUndo = self.addPsychopyTool(
                        name='undo',
                        label=_translate('Undo'),
                        shortcut='undo',
                        tooltip=_translate("Undo last action"),
                        func=self.frame.undo)  # Undo
            self.frame.bldrBtnRedo = self.addPsychopyTool(
                        name='redo',
                        label=_translate('Redo'),
                        shortcut='redo',
                        tooltip=_translate("Redo last action"),
                        func=self.frame.redo)  # Redo
            self.AddSeparator()  # Seperator
            self.addPsychopyTool(
                    name='monitors',
                    label=_translate('Monitor Center'),
                    shortcut='none',
                    tooltip=_translate("Monitor settings and calibration"),
                    func=self.frame.app.openMonitorCenter)  # Monitor Center
            self.addPsychopyTool(
                    name='cogwindow',
                    label=_translate('Experiment Settings'),
                    shortcut='none',
                    tooltip=_translate("Edit experiment settings"),
                    func=self.frame.setExperimentSettings)  # Settings
            self.AddSeparator()
            self.addPsychopyTool(
                    name='compile_py',
                    label=_translate('Compile Python Script'),
                    shortcut='compileScript',
                    tooltip=_translate("Compile to Python script"),
                    func=self.frame.compileScript)  # Compile
            self.addPsychopyTool(
                    name='compile_js',
                    label=_translate('Compile JS Script'),
                    shortcut='compileScript',
                    tooltip=_translate("Compile to JS script"),
                    func=self.frame.fileExport)  # Compile
            self.frame.bldrBtnRunner = self.addPsychopyTool(
                    name='runner',
                    label=_translate('Runner'),
                    shortcut='runnerScript',
                    tooltip=_translate("Send experiment to Runner"),
                    func=self.frame.runFile)  # Run
            self.frame.bldrBtnRun = self.addPsychopyTool(
                    name='run',
                    label=_translate('Run'),
                    shortcut='runScript',
                    tooltip=_translate("Run experiment"),
                    func=self.frame.runFile)  # Run
            self.AddSeparator()  # Seperator
            pavButtons.addPavloviaTools()
        elif frame.__class__.__name__ == 'CoderFrame':
            self.addPsychopyTool('filenew', _translate('New'), 'new',
                                 _translate("Create new experiment file"),
                                 self.frame.fileNew)  # New
            self.addPsychopyTool('fileopen', _translate('Open'), 'open',
                                 _translate("Open an existing experiment file"),
                                 self.frame.fileOpen)  # Open
            self.frame.cdrBtnSave = \
                self.addPsychopyTool('filesave', _translate('Save'), 'save',
                                     _translate("Save current experiment file"),
                                     self.frame.fileSave)  # Save
            self.addPsychopyTool('filesaveas', _translate('Save As...'), 'saveAs',
                                 _translate("Save current experiment file as..."),
                                 self.frame.fileSaveAs)  # SaveAs
            self.frame.cdrBtnUndo = \
                self.addPsychopyTool('undo', _translate('Undo'), 'undo',
                                     _translate("Undo last action"),
                                     self.frame.undo)  # Undo
            self.frame.cdrBtnRedo = \
                self.addPsychopyTool('redo', _translate('Redo'), 'redo',
                                     _translate("Redo last action"),
                                     self.frame.redo)  # Redo
            self.AddSeparator()  # Seperator
            self.addPsychopyTool('monitors', _translate('Monitor Center'), 'none',
                                 _translate("Monitor settings and calibration"),
                                 self.frame.app.openMonitorCenter)
            self.addPsychopyTool('color', _translate('Color Picker'), 'none',
                                 _translate("Color Picker -> clipboard"),
                                 self.frame.app.colorPicker)
            self.AddSeparator()
            self.frame.cdrBtnRunner = self.addPsychopyTool(
                    'runner', _translate('Runner'), 'runnerScript',
                    _translate("Send experiment to Runner"),
                    self.frame.runFile)
            self.frame.cdrBtnRun = self.addPsychopyTool(
                    'run', _translate('Run'), 'runScript',
                    _translate("Run experiment"),
                    self.frame.runFile)
            self.AddSeparator()
            pavButtons.addPavloviaTools(
                buttons=['pavloviaSync', 'pavloviaSearch', 'pavloviaUser'])
        frame.btnHandles.update(pavButtons.btnHandles)
        self.Realize()
        # Disable compile buttons until an experiment is present
        if 'compile_py' in self.buttons:
            self.EnableTool(self.buttons['compile_py'].GetId(), Path(self.frame.filename).is_file())
        if 'compile_js' in self.buttons:
            self.EnableTool(self.buttons['compile_js'].GetId(), Path(self.frame.filename).is_file())

    def addPsychopyTool(self, name, label, shortcut, tooltip, func,
                        emblem=None):
        if not name.endswith('.png'):
            filename = name + '.png'
        else:
            filename = name
        self.buttons[name] = self.app.iconCache.makeBitmapButton(parent=self, filename=filename,
                                                   name=label,
                                                   label=("%s [%s]" % (
                                                       label,
                                                       self.keys[shortcut])),
                                                   emblem=emblem, toolbar=self,
                                                   tip=tooltip,
                                                   size=self.iconSize)
        # Bind function
        self.Bind(wx.EVT_TOOL, func, self.buttons[name])
        return self.buttons[name]


class PsychopyPlateBtn(platebtn.PlateButton, ThemeMixin):
    def __init__(self, parent, id=wx.ID_ANY, label='', bmp=None,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=1, name=wx.ButtonNameStr):
        platebtn.PlateButton.__init__(self, parent, id, label, bmp, pos, size, style, name)
        self.parent = parent
        self.__InitColors()
        self._applyAppTheme()

    def _applyAppTheme(self):
        cs = ThemeMixin.appColors
        self.__InitColors()
        self.SetBackgroundColour(wx.Colour(self.parent.GetBackgroundColour()))
        self.SetPressColor(cs['txtbutton_bg_hover'])
        self.SetLabelColor(cs['text'],
                           cs['txtbutton_fg_hover'])

    def __InitColors(self):
        cs = ThemeMixin.appColors
        """Initialize the default colors"""
        colors = dict(default=True,
                      hlight=cs['txtbutton_bg_hover'],
                      press=cs['txtbutton_bg_hover'],
                      htxt=cs['text'])
        return colors


class ButtonArray(wx.Window):

    class ArrayBtn(wx.Button):
        def __init__(self, parent, label=""):
            wx.Button.__init__(self, parent, label=label, style=wx.BORDER_NONE)
            self.parent = parent
            # Setup sizer
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SetSizer(self.sizer)
            # Create remove btn
            self.removeBtn = wx.Button()
            self.removeBtn.SetBackgroundStyle(wx.BG_STYLE_TRANSPARENT)
            self.removeBtn.Create(self, size=(12, 12), style=wx.BORDER_NONE)
            self.removeBtn.SetBitmap(IconCache().getBitmap(name="delete", size=8))
            # Add remove btn to spacer
            self.sizer.AddStretchSpacer(1)
            self.sizer.Add(self.removeBtn, border=4, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
            self.Layout()
            # Bind remove btn to remove function
            self.removeBtn.Bind(wx.EVT_BUTTON, self.remove)
            # Bind button to button function
            self.Bind(wx.EVT_BUTTON, self.onClick)

        def remove(self, evt=None):
            self.parent.removeItem(self)

        def onClick(self, evt=None):
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self)
            wx.PostEvent(self.parent, evt)

    def __init__(self, parent, orient=wx.HORIZONTAL, items=[]):
        # Create self
        wx.Window.__init__(self, parent)
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.parent = parent
        # Create sizer
        self.sizer = wx.WrapSizer(orient=orient)
        self.SetSizer(self.sizer)
        # Create add button
        self.addBtn = wx.Button(self, size=(24, 24), label="+", style=wx.BORDER_NONE)
        self.addBtn.Bind(wx.EVT_BUTTON, self.newItem)
        self.sizer.Add(self.addBtn, border=3, flag=wx.EXPAND | wx.ALL)
        # Add items
        self.items = items
        # Layout
        self.Layout()

    @property
    def items(self):
        items = {}
        for child in self.sizer.Children:
            if not child.Window == self.addBtn:
                items[child.Window.Label] = child.Window
        return items

    @items.setter
    def items(self, value):
        assert isinstance(value, (list, tuple))

        value.reverse()

        self.clear()
        for item in value:
            self.addItem(item)

    def newItem(self, evt=None):
        _dlg = wx.TextEntryDialog(self.parent, message="Add tag...")
        if _dlg.ShowModal() != wx.ID_OK:
            return
        self.addItem(_dlg.GetValue())

    def addItem(self, item):
        if not isinstance(item, wx.Window):
            item = self.ArrayBtn(self, label=item)
        self.sizer.Insert(0, item, border=3, flag=wx.EXPAND | wx.ALL)
        self.Layout()
        # Raise event
        evt = wx.ListEvent(wx.EVT_LIST_INSERT_ITEM.typeId)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def removeItem(self, item):
        items = self.items.copy()
        # Get value from key if needed
        if item in items:
            item = items[item]
        # Delete object and item in dict
        if item in list(items.values()):
            i = self.sizer.Children.index(self.sizer.GetItem(item))
            self.sizer.Remove(i)
            item.Hide()
        self.Layout()
        # Raise event
        evt = wx.ListEvent(wx.EVT_LIST_DELETE_ITEM.typeId)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def clear(self):
        # Raise event
        evt = wx.ListEvent(wx.EVT_LIST_DELETE_ALL_ITEMS.typeId)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)
        # Delete all items
        for item in self.items:
            self.removeItem(item)

    def Enable(self, enable=True):
        for child in self.Children:
            child.Enable(enable)

    def Disable(self):
        self.Enable(False)

    def GetValue(self):
        return list(self.items)


class ImageCtrl(wx.StaticBitmap):
    def __init__(self, parent, bitmap, size=(128, 128)):
        wx.StaticBitmap.__init__(self, parent, bitmap=wx.Bitmap(), size=size)
        self.parent = parent
        # Set bitmap
        self.SetBitmap(bitmap)
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddStretchSpacer(1)
        self.SetSizer(self.sizer)
        # Add edit button
        self.editBtn = wx.Button(self, size=(24, 24), label=chr(int("270E", 16)), style=wx.BORDER_NONE)
        self.editBtn.Bind(wx.EVT_BUTTON, self.LoadBitmap)
        self.sizer.Add(self.editBtn, border=6, flag=wx.ALIGN_BOTTOM | wx.ALL)

    def LoadBitmap(self, evt=None):
        # Open file dlg
        _dlg = wx.FileDialog(self.parent, message=_translate("Select image..."))
        if _dlg.ShowModal() != wx.ID_OK:
            return
        # Get value
        path = str(Path(_dlg.GetPath()))
        self.SetBitmap(path)
        # Post event
        evt = wx.FileDirPickerEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self, -1, path)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def SetBitmap(self, bitmap):
        # Get from file if needed
        if not isinstance(bitmap, wx.Bitmap):
            bitmap = wx.Bitmap(bitmap)
        # Sub in blank bitmaps
        if not bitmap.IsOk():
            wx.StaticBitmap.SetBitmap(self, wx.Bitmap())
            return
        # Store full size bitmap
        self._fullBitmap = bitmap
        # Resize bitmap
        buffer = bitmap.ConvertToImage()
        buffer = buffer.Scale(*self.Size, quality=wx.IMAGE_QUALITY_HIGH)
        scaledBitmap = wx.BitmapFromImage(buffer)
        # Set image
        wx.StaticBitmap.SetBitmap(self, scaledBitmap)

    def GetBitmapFull(self):
        return self._fullBitmap

    @property
    def BitmapFull(self):
        return self.GetBitmapFull()

    def Enable(self, enable=True):
        wx.StaticBitmap.Enable(self, enable)
        self.editBtn.Enable(enable)

    def Disable(self):
        self.Enable(False)


class PsychopyScrollbar(wx.ScrollBar):
    def __init__(self, parent, ori=wx.VERTICAL):
        wx.ScrollBar.__init__(self)
        if ori == wx.HORIZONTAL:
            style = wx.SB_HORIZONTAL
        else:
            style = wx.SB_VERTICAL
        self.Create(parent, style=style)
        self.ori = ori
        self.parent = parent
        self.Bind(wx.EVT_SCROLL, self.DoScroll)
        self.Resize()

    def DoScroll(self, event):
        if self.ori == wx.HORIZONTAL:
            w = event.GetPosition()
            h = self.parent.GetScrollPos(wx.VERTICAL)
        elif self.ori == wx.VERTICAL:
            w = self.parent.GetScrollPos(wx.HORIZONTAL)
            h = event.GetPosition()
        else:
            return
        self.parent.Scroll(w, h)
        self.Resize()

    def Resize(self):
        sz = self.parent.GetSize()
        vsz = self.parent.GetVirtualSize()
        start = self.parent.GetViewStart()
        if self.ori == wx.HORIZONTAL:
            sz = (sz.GetWidth(), 20)
            vsz = vsz.GetWidth()
        elif self.ori == wx.VERTICAL:
            sz = (20, sz.GetHeight())
            vsz = vsz.GetHeight()
        self.SetDimensions(start[0], start[1], sz[0], sz[1])
        self.SetScrollbar(
            position=self.GetScrollPos(self.ori),
            thumbSize=10,
            range=1,
            pageSize=vsz
        )


class FileCtrl(wx.TextCtrl):
    def __init__(self, parent, dlgtype="file"):
        wx.TextCtrl.__init__(self, parent, size=(-1, 24))
        # Store type
        self.dlgtype = dlgtype
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.sizer.AddStretchSpacer(1)
        # Add button
        self.fileBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
        self.fileBtn.SetBackgroundColour(self.GetBackgroundColour())
        self.fileBtn.SetBitmap(IconCache().getBitmap(name="folder", size=16))
        self.sizer.Add(self.fileBtn, border=4, flag=wx.ALL)
        # Bind browse function
        self.fileBtn.Bind(wx.EVT_BUTTON, self.browse)

    def browse(self, evt=None):
        file = Path(self.GetValue())
        # Open file or dir dlg
        if self.dlgtype == "dir":
            dlg = wx.DirDialog(self, message=_translate("Specify folder..."), defaultPath=str(file))
        else:
            dlg = wx.FileDialog(self, message=_translate("Specify file..."), defaultDir=str(file))
        if dlg.ShowModal() != wx.ID_OK:
            return
        # Get data from dlg
        file = Path(dlg.GetPath())
        # Set data
        self.SetValue(str(file))

    def SetValue(self, value):
        # Do base value setting
        wx.TextCtrl.SetValue(self, value)
        # Post event
        evt = wx.FileDirPickerEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self, -1, value)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def Enable(self, enable=True):
        wx.TextCtrl.Enable(self, enable)
        self.fileBtn.Enable(enable)
        self.fileBtn.SetBackgroundColour(self.GetBackgroundColour())

    def Disable(self):
        self.Enable(False)

    def Show(self, show=True):
        wx.TextCtrl.Show(self, show)
        self.fileBtn.Show(show)

    def Hide(self):
        self.Show(False)


def updateDemosMenu(frame, menu, folder, ext):
    """Update Demos menu as needed."""
    def _makeButton(parent, menu, demo):
        # Skip if demo name starts with _
        if demo.name.startswith("_"):
            return
        # Create menu button
        item = menu.Append(wx.ID_ANY, demo.name)
        # Store in window's demos list
        parent.demos.update({item.Id: demo})
        # Link button to demo opening function
        parent.Bind(wx.EVT_MENU, parent.demoLoad, item)

    def _makeFolder(parent, menu, folder, ext):
        # Skip if underscore in folder name
        if folder.name.startswith("_"):
            return
        # Create and append menu for this folder
        submenu = wx.Menu()
        menu.AppendSubMenu(submenu, folder.name)
        # Get folder contents
        folderContents = glob.glob(str(folder / '*'))
        for subfolder in sorted(folderContents):
            subfolder = Path(subfolder)
            # Make menu/button for each:
            # subfolder according to whether it contains a psyexp, or...
            # subfile according to whether it matches the ext
            if subfolder.is_dir():
                subContents = glob.glob(str(subfolder / '*'))
                if any(file.endswith(".psyexp") and not file.startswith("_") for file in subContents):
                    _makeButton(parent, submenu, subfolder)
                else:
                    _makeFolder(parent, submenu, subfolder, ext)
            elif subfolder.suffix == ext and not subfolder.name.startswith("_"):
                _makeButton(parent, submenu, subfolder)

    # Make blank dict to store demo details in
    frame.demos = {}
    if not folder:  # if there is no unpacked demos folder then just return
        return

    # Get root folders
    rootGlob = glob.glob(str(Path(folder) / '*'))
    for fdr in rootGlob:
        fdr = Path(fdr)
        # Make menus/buttons recursively for each folder according to whether it contains a psyexp
        if fdr.is_dir():
            folderContents = glob.glob(str(fdr / '*'))
            if any(file.endswith(".psyexp") for file in folderContents):
                _makeButton(frame, menu, fdr)
            else:
                _makeFolder(frame, menu, fdr, ext)

class FrameSwitcher(wx.Menu):
    """Menu for switching between different frames"""
    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        self.app = parent.app
        self.itemFrames = {}
        # Listen for window switch
        self.next = self.Append(wx.ID_MDI_WINDOW_NEXT,
                                _translate("&Next Window\t%s") % self.app.keys['cycleWindows'],
                                _translate("&Next Window\t%s") % self.app.keys['cycleWindows'])
        self.Bind(wx.EVT_MENU, self.nextWindow, self.next)
        self.AppendSeparator()
        # Add creator options
        self.minItemSpec = [
            {'label': "Builder", 'class': psychopy.app.builder.BuilderFrame, 'method': self.app.showBuilder},
            {'label': "Coder", 'class': psychopy.app.coder.CoderFrame, 'method': self.app.showCoder},
            {'label': "Runner", 'class': psychopy.app.runner.RunnerFrame, 'method': self.app.showRunner},
        ]
        for spec in self.minItemSpec:
            if not isinstance(self.Window, spec['class']):
                item = self.Append(
                    wx.ID_ANY, spec['label'], spec['label']
                )
                self.Bind(wx.EVT_MENU, spec['method'], item)
        self.AppendSeparator()
        self.updateFrames()

    @property
    def frames(self):
        return self.parent.app.getAllFrames()

    def updateFrames(self):
        """Set items according to which windows are open"""
        self.next.Enable(len(self.frames) > 1)
        # Make new items if needed
        for frame in self.frames:
            if frame not in self.itemFrames:
                if frame.filename:
                    label = type(frame).__name__.replace("Frame", "") + ": " + os.path.basename(frame.filename)
                else:
                    label = type(frame).__name__.replace("Frame", "")
                self.itemFrames[frame] = self.AppendRadioItem(wx.ID_ANY, label, label)
                self.Bind(wx.EVT_MENU, self.showFrame, self.itemFrames[frame])
        # Edit items to match frames
        for frame in self.itemFrames:
            item = self.itemFrames[frame]
            if not item:
                continue
            if frame not in self.frames:
                # Disable unused items
                item.Enable(False)
            else:
                # Rename item
                if frame.filename:
                    self.itemFrames[frame].SetItemLabel(
                        type(frame).__name__.replace("Frame", "") + ": " + os.path.basename(frame.filename)
                    )
                else:
                    self.itemFrames[frame].SetItemLabel(
                        type(frame).__name__.replace("Frame", "") + ": None"
                    )
            item.Check(frame == self.Window)
        self.itemFrames = {key: self.itemFrames[key] for key in self.itemFrames if self.itemFrames[key] is not None}

    def showFrame(self, event=None):
        itemFrames = event.EventObject.itemFrames
        frame = [key for key in itemFrames if itemFrames[key].Id == event.Id][0]
        frame.Show(True)
        frame.Raise()
        self.parent.app.SetTopWindow(frame)
        self.updateFrames()

    def nextWindow(self, event=None):
        """Cycle through list of open windows"""
        current = event.EventObject.Window
        i = self.frames.index(current)
        while self.frames[i] == current:
            i -= 1
        self.frames[i].Raise()
        self.frames[i].Show()
        self.updateFrames()
