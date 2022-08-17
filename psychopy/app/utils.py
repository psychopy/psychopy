#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""utility classes for the Builder
"""
import glob
import os
import re
from pathlib import Path

import numpy
from wx.lib.agw.aui.aui_constants import *
import wx.lib.statbmp
from wx.lib.agw.aui.aui_utilities import IndentPressedBitmap, ChopText, TakeScreenShot
import sys
import wx
import wx.lib.agw.aui as aui
from wx.lib import platebtn

import psychopy
from psychopy import logging
from . import pavlovia_ui
from .themes import colors, handlers, icons
from psychopy.localization import _translate
from psychopy.tools.stringtools import prettyname
from psychopy.tools.apptools import SortTerm


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


class BasePsychopyToolbar(wx.ToolBar, handlers.ThemeMixin):
    """Toolbar for the Builder/Coder Frame"""
    def __init__(self, frame):
        # Initialise superclass
        wx.ToolBar.__init__(self, frame)
        # Store necessary refs
        self.frame = frame
        self.app = self.frame.app
        # Configure toolbar appearance
        self.SetWindowStyle(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_NODIVIDER)
        # Set icon size
        self.iconSize = 32
        self.SetToolBitmapSize((self.iconSize, self.iconSize))
        # OS-dependent tool-tips
        ctrlKey = 'Ctrl+'
        if sys.platform == 'darwin':
            ctrlKey = 'Cmd+'
        # keys are the keyboard keys, not the keys of the dict
        self.keys = {k: self.frame.app.keys[k].replace('Ctrl+', ctrlKey)
                for k in self.frame.app.keys}
        self.keys['none'] = ''

        self.buttons = {}

        self.makeTools()

    def makeTools(self):
        """
        Make tools
        """
        pass

    def makeTool(self, name, label="", shortcut=None, tooltip="", func=None):
        # Get icon
        icn = icons.ButtonIcon(name, size=self.iconSize)
        # Make button
        if 'phoenix' in wx.PlatformInfo:
            btn = self.AddTool(
                wx.ID_ANY, label=label,
                bitmap=icn.bitmap, shortHelp=tooltip,
                kind=wx.ITEM_NORMAL
            )
        else:
            btn = self.AddSimpleTool(
                wx.ID_ANY, label=label,
                bitmap=icn.bitmap, shortHelp=tooltip,
                kind=wx.ITEM_NORMAL
            )
        # Bind tool to function
        if func is None:
            func = self.none
        self.Bind(wx.EVT_TOOL, func, btn)

        return btn

    @staticmethod
    def none():
        """
        Blank function to use when bound function is None
        """
        pass


class PsychopyPlateBtn(platebtn.PlateButton, handlers.ThemeMixin):
    def __init__(self, parent, id=wx.ID_ANY, label='', bmp=None,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.BORDER_NONE, name=wx.ButtonNameStr):
        platebtn.PlateButton.__init__(self, parent, id, label, bmp, pos, size, style, name)
        self.parent = parent
        self.__InitColors()
        self._applyAppTheme()

    def _applyAppTheme(self):
        self.__InitColors()
        self.SetBackgroundColour(wx.Colour(self.parent.GetBackgroundColour()))
        self.SetPressColor(colors.app['txtbutton_bg_hover'])
        self.SetLabelColor(colors.app['text'],
                           colors.app['txtbutton_fg_hover'])

    def __InitColors(self):
        """Initialize the default colors"""
        cols = dict(default=True,
                      hlight=colors.app['txtbutton_bg_hover'],
                      press=colors.app['txtbutton_bg_hover'],
                      htxt=colors.app['text'])
        return cols


class ButtonArray(wx.Window):

    class ArrayBtn(wx.Window):
        def __init__(self, parent, label=""):
            wx.Window.__init__(self, parent)
            self.parent = parent
            # Setup sizer
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SetSizer(self.sizer)
            # Create button
            self.button = wx.Button(self, label=label, style=wx.BORDER_NONE)
            self.sizer.Add(self.button, border=4, flag=wx.LEFT | wx.EXPAND)
            # Create remove btn
            self.removeBtn = wx.Button(self, label="×", size=(24, -1))
            self.sizer.Add(self.removeBtn, border=4, flag=wx.RIGHT | wx.EXPAND)
            # Bind remove btn to remove function
            self.removeBtn.Bind(wx.EVT_BUTTON, self.remove)
            # Bind button to button function
            self.button.Bind(wx.EVT_BUTTON, self.onClick)

            self.SetBackgroundColour(self.parent.GetBackgroundColour())
            self.Layout()

        def remove(self, evt=None):
            self.parent.removeItem(self)

        def onClick(self, evt=None):
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self)
            wx.PostEvent(self.parent, evt)

    def __init__(self, parent, orient=wx.HORIZONTAL,
                 items=(),
                 options=None,
                 itemAlias=_translate("item")):
        # Create self
        wx.Window.__init__(self, parent)
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.parent = parent
        self.itemAlias = itemAlias
        self.options = options
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

    def _applyAppTheme(self, target=None):
        for child in self.sizer.Children:
            if hasattr(child.Window, "_applyAppTheme"):
                child.Window._applyAppTheme()

    @property
    def items(self):
        items = {}
        for child in self.sizer.Children:
            if not child.Window == self.addBtn:
                items[child.Window.button.Label] = child.Window
        return items

    @items.setter
    def items(self, value):
        if isinstance(value, str):
            value = [value]
        if value is None or value is numpy.nan:
            value = []
        assert isinstance(value, (list, tuple))

        value.reverse()

        self.clear()
        for item in value:
            self.addItem(item)

    def newItem(self, evt=None):
        msg = _translate("Add {}...").format(self.itemAlias)
        if self.options is None:
            _dlg = wx.TextEntryDialog(self.parent, message=msg)
        else:
            _dlg = wx.SingleChoiceDialog(self.parent, msg, "Input Text", choices=self.options)

        if _dlg.ShowModal() != wx.ID_OK:
            return
        if self.options is None:
            self.addItem(_dlg.GetValue())
        else:
            self.addItem(_dlg.GetStringSelection())

    def addItem(self, item):
        if not isinstance(item, wx.Window):
            item = self.ArrayBtn(self, label=item)
        self.sizer.Insert(0, item, border=3, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.RIGHT)
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


class SortCtrl(wx.Window):
    class SortItem(wx.Window):
        def __init__(self, parent,
                     item,
                     showSelect=False, selected=True,
                     showFlip=False
                     ):
            # Create self
            wx.Window.__init__(self, parent, style=wx.BORDER_NONE)
            self.SetBackgroundColour("white")
            self.parent = parent
            # Make sure we've been given a SortTerm
            assert isinstance(item, SortTerm)
            self.item = item
            # Setup sizer
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SetSizer(self.sizer)
            # Add tickbox (if select)
            self.selectCtrl = wx.CheckBox(self)
            self.selectCtrl.Bind(wx.EVT_CHECKBOX, self.onSelect)
            self.selectCtrl.SetValue(selected)
            self.selectCtrl.Show(showSelect)
            self.sizer.Add(self.selectCtrl, border=6, flag=wx.ALL | wx.EXPAND)
            # Add label
            self.labelObj = wx.StaticText(self, label=self.item.label)
            self.sizer.Add(self.labelObj, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
            # Add flip button
            self.flipBtn = wx.Button(self, size=(16, 8), label="⇵", style=wx.BORDER_NONE)
            self.flipBtn.SetBackgroundColour(self.GetBackgroundColour())
            self.flipBtn.Bind(wx.EVT_BUTTON, self.flip)
            self.flipBtn.Show(showFlip)
            self.sizer.Add(self.flipBtn, border=6, flag=wx.ALL | wx.EXPAND)
            # Add ctrls sizer
            self.ctrlsSizer = wx.BoxSizer(wx.VERTICAL)
            self.sizer.Add(self.ctrlsSizer, border=6, flag=wx.ALL | wx.EXPAND)
            # Add up button
            self.upBtn = wx.Button(self, size=(16, 8), label="▲", style=wx.BORDER_NONE)
            self.upBtn.SetBackgroundColour(self.GetBackgroundColour())
            self.upBtn.Bind(wx.EVT_BUTTON, self.moveUp)
            self.ctrlsSizer.Add(self.upBtn, border=0, flag=wx.ALL | wx.EXPAND)
            # Add stretch spacer inbetween
            self.ctrlsSizer.AddStretchSpacer(1)
            # Add up button
            self.downBtn = wx.Button(self, size=(16, 8), label="▼", style=wx.BORDER_NONE)
            self.downBtn.SetBackgroundColour(self.GetBackgroundColour())
            self.downBtn.Bind(wx.EVT_BUTTON, self.moveDown)
            self.ctrlsSizer.Add(self.downBtn, border=0, flag=wx.ALL | wx.EXPAND)
            # Do initial select
            self.onSelect()

        @property
        def label(self):
            return self.item.label

        @property
        def value(self):
            return self.item.value

        def flip(self, evt=None):
            # Flip state
            self.item.ascending = not self.item.ascending
            # Change label
            self.labelObj.SetLabel(self.label)

        def moveUp(self, evt=None):
            # Get own index
            i = self.parent.items.index(self)
            # Insert popped self before previous position
            self.parent.items.insert(max(i-1, 0), self.parent.items.pop(i))
            # Layout
            self.parent.Layout()

        def moveDown(self, evt=None):
            # Get own index
            i = self.parent.items.index(self)
            # Insert popped self before previous position
            self.parent.items.insert(min(i+1, len(self.parent.items)), self.parent.items.pop(i))
            # Layout
            self.parent.Layout()

        @property
        def selected(self):
            return self.selectCtrl.GetValue()

        def onSelect(self, evt=None):
            self.Enable(self.selected)

        def Enable(self, enable=True):
            self.labelObj.Enable(enable)

        def Disable(self):
            self.Enable(False)

    def __init__(self, parent,
                 items,
                 showSelect=False, selected=True,
                 showFlip=False,
                 orient=wx.VERTICAL):
        wx.Window.__init__(self, parent)
        # Make sure we've been given an array
        if not isinstance(items, (list, tuple)):
            items = [items]
        # Setup sizer
        self.sizer = wx.BoxSizer(orient)
        self.SetSizer(self.sizer)
        # If given a bool for select, apply it to all items
        if isinstance(selected, bool):
            selected = [selected] * len(items)
        assert isinstance(selected, (list, tuple)) and len(selected) == len(items)
        # Setup items
        self.items = []
        for i, item in enumerate(items):
            self.items.append(self.SortItem(self,
                                            item=item,
                                            showSelect=showSelect, selected=selected[i],
                                            showFlip=showFlip))
            self.sizer.Add(self.items[i], border=6, flag=wx.ALL | wx.EXPAND)
        # Layout
        self.Layout()

    def GetValue(self):
        items = []
        for item in self.items:
            if item.selected:
                items.append(item.item)
        return items

    def Layout(self):
        # Get order of items in reverse
        items = self.items.copy()
        items.reverse()
        # Remove each item
        for item in items:
            self.sizer.Remove(self.sizer.Children.index(self.sizer.GetItem(item)))
        # Add items back in oder
        for i, item in enumerate(items):
            self.sizer.Prepend(item, border=6, flag=wx.ALL | wx.EXPAND)
            item.upBtn.Show(i != len(items)-1)
            item.downBtn.Show(i != 0)
        # Disable appropriate buttons
        # Do base layout
        wx.Window.Layout(self)


class ImageCtrl(wx.lib.statbmp.GenStaticBitmap):
    def __init__(self, parent, bitmap, size=(128, 128)):
        wx.lib.statbmp.GenStaticBitmap.__init__(self, parent, ID=wx.ID_ANY, bitmap=wx.Bitmap(), size=size)
        self.parent = parent
        self.iconCache = icons.iconCache
        # Set bitmap
        self.SetBitmap(bitmap)
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddStretchSpacer(1)
        self.SetSizer(self.sizer)
        # Add edit button
        self.editBtn = wx.Button(self, size=(24, 24), label=chr(int("270E", 16)))
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
            self.path = bitmap
            bitmap = wx.Bitmap(bitmap)
        # Sub in blank bitmaps
        if not bitmap.IsOk():
            bitmap = icons.ButtonIcon(stem="user_none", size=128).bitmap
        # Store full size bitmap
        self._fullBitmap = bitmap
        # Resize bitmap
        buffer = bitmap.ConvertToImage()
        buffer = buffer.Scale(*self.Size, quality=wx.IMAGE_QUALITY_HIGH)
        scaledBitmap = wx.Bitmap(buffer)
        # Set image
        wx.lib.statbmp.GenStaticBitmap.SetBitmap(self, scaledBitmap)

    @property
    def path(self):
        """
        If current bitmap is from a file, returns the filepath. Otherwise, returns None.
        """
        if hasattr(self, "_path"):
            return self._path

    @path.setter
    def path(self, value):
        self._path = value

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
    def __init__(self, parent, dlgtype="file", value=""):
        wx.TextCtrl.__init__(self, parent, value=value, size=(-1, 24))
        # Store type
        self.dlgtype = dlgtype
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.sizer.AddStretchSpacer(1)
        # Add button
        self.fileBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
        self.fileBtn.SetBackgroundColour(self.GetBackgroundColour())
        self.fileBtn.SetBitmap(icons.ButtonIcon(stem="folder", size=16).bitmap)
        self.sizer.Add(self.fileBtn, border=4, flag=wx.ALL)
        # Bind browse function
        self.fileBtn.Bind(wx.EVT_BUTTON, self.browse)

    def browse(self, evt=None):
        file = Path(self.GetValue())
        # Sub in a / for blank paths to force the better folder navigator
        if file == Path():
            file = Path("/")
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
        # Replace backslashes with forward slashes
        value = value.replace("\\", "/")
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


def sanitize(inStr):
    """
    Process a string to remove any sensitive information, i.e. OAUTH keys
    """
    # Key-value pairs of patterns with what to replace them with
    patterns = {
        "https\:\/\/oauth2\:[\d\w]{64}@gitlab\.pavlovia\.org\/.*\.git": "[[OAUTH key hidden]]" # Remove any oauth keys
    }
    # Replace each pattern
    for pattern, repl in patterns.items():
        inStr = re.sub(pattern, repl, inStr)

    return inStr


class HoverMixin:
    """
    Mixin providing methods to handle hover on/off events for a wx.Window based class.
    """
    IsHovered = False

    def SetupHover(self):
        """
        Helper method to setup hovering for this object
        """
        # Bind both hover on and hover off events to the OnHover method
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnHover)

    def OnHover(self, evt=None):
        """
        Method to handle hover events for buttons. To use, bind both `wx.EVT_ENTER_WINDOW` and `wx.EVT_LEAVE_WINDOW` events to this method.
        """
        if evt is None:
            # If calling without event, style according to last IsHovered measurement
            if self.IsHovered:
                self.SetForegroundColour(self.ForegroundColourHover)
                self.SetBackgroundColour(self.BackgroundColourHover)
            else:
                self.SetForegroundColour(self.ForegroundColourNoHover)
                self.SetBackgroundColour(self.BackgroundColourNoHover)
        elif evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # If hovered over currently, use hover colours
            self.SetForegroundColour(self.ForegroundColourHover)
            self.SetBackgroundColour(self.BackgroundColourHover)
            # and mark as hovered
            self.IsHovered = True
        else:
            # Otherwise, use regular colours
            self.SetForegroundColour(self.ForegroundColourNoHover)
            self.SetBackgroundColour(self.BackgroundColourNoHover)
            # and mark as unhovered
            self.IsHovered = False
        # Refresh
        self.Refresh()

    @property
    def ForegroundColourNoHover(self):
        if hasattr(self, "_ForegroundColourNoHover"):
            return self._ForegroundColourNoHover
        return colors.app['text']

    @ForegroundColourNoHover.setter
    def ForegroundColourNoHover(self, value):
        self._ForegroundColourNoHover = value

    @property
    def BackgroundColourNoHover(self):
        if hasattr(self, "_BackgroundColourNoHover"):
            return self._BackgroundColourNoHover
        return colors.app['frame_bg']

    @BackgroundColourNoHover.setter
    def BackgroundColourNoHover(self, value):
        self._BackgroundColourNoHover = value

    @property
    def ForegroundColourHover(self):
        if hasattr(self, "_ForegroundColourHover"):
            return self._ForegroundColourHover
        return colors.app['txtbutton_fg_hover']

    @ForegroundColourHover.setter
    def ForegroundColourHover(self, value):
        self._ForegroundColourHover = value

    @property
    def BackgroundColourHover(self):
        if hasattr(self, "_BackgroundColourHover"):
            return self._BackgroundColourHover
        return colors.app['txtbutton_bg_hover']

    @BackgroundColourHover.setter
    def BackgroundColourHover(self, value):
        self._BackgroundColourHover = value


class ToggleButton(wx.ToggleButton, HoverMixin):
    """
    Extends wx.ToggleButton to give methods for handling color changes relating to hover events and value setting.
    """
    @property
    def BackgroundColourNoHover(self):
        if self.GetValue():
            # Return a darker color if selected
            return colors.app['docker_bg']
        else:
            # Return the default color otherwise
            return HoverMixin.BackgroundColourNoHover.fget(self)


class ToggleButtonArray(wx.Window, handlers.ThemeMixin):

    def __init__(self, parent, labels=None, values=None, multi=False, ori=wx.HORIZONTAL):
        wx.Window.__init__(self, parent)
        self.parent = parent
        self.multi = multi
        # Setup sizer
        self.sizer = wx.BoxSizer(ori)
        self.SetSizer(self.sizer)
        # Alias values and labels
        if labels is None:
            labels = values
        if values is None:
            values = labels
        if values is None and labels is None:
            values = labels = []
        # Make buttons
        self.buttons = {}
        for i, val in enumerate(values):
            self.buttons[val] = ToggleButton(self, style=wx.BORDER_NONE)
            self.buttons[val].SetupHover()
            self.buttons[val].SetLabelText(labels[i])
            self.buttons[val].Bind(wx.EVT_TOGGLEBUTTON, self.processToggle)
            self.sizer.Add(self.buttons[val], border=6, proportion=1, flag=wx.ALL | wx.EXPAND)

    def processToggle(self, evt):
        obj = evt.GetEventObject()
        if self.multi:
            # Toggle self
            self.SetValue(self.GetValue())
        else:
            # Selectself and deselect other buttons
            for key, btn in self.buttons.items():
                if btn == obj:
                    self.SetValue(key)

    def SetValue(self, value):
        if not isinstance(value, (list, tuple)):
            value = [value]
        if not self.multi:
            assert len(value) == 1, "When multi is False, ToggleButtonArray value must be a single value"
        # Set corresponding button's value to be True and all others to be False
        for key, btn in self.buttons.items():
            btn.SetValue(key in value)
        # Restyle
        self._applyAppTheme()
        # Emit event
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def GetValue(self):
        # Return key of button(s) whose value is True
        values = []
        for key, btn in self.buttons.items():
            if btn.GetValue():
                values.append(key)
        # If single select, only return first value
        if not self.multi:
            values = values[0]
        return values

    def _applyAppTheme(self, target=None):
        # Set panel background
        self.SetBackgroundColour(colors.app['panel_bg'])
        # Use OnHover event to set buttons to their default colors
        for btn in self.buttons.values():
            btn.OnHover()


def sanitize(inStr):
    """
    Process a string to remove any sensitive information, i.e. OAUTH keys
    """
    # Key-value pairs of patterns with what to replace them with
    patterns = {
        "https\:\/\/oauth2\:[\d\w]{64}@gitlab\.pavlovia\.org\/.*\.git": "[[OAUTH key hidden]]" # Remove any oauth keys
    }
    # Replace each pattern
    for pattern, repl in patterns.items():
        inStr = re.sub(pattern, repl, inStr)

    return inStr
