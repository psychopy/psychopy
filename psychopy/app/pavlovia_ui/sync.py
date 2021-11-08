#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from psychopy.tools.versionchooser import _translate


class SyncDialog(wx.Dialog):
    def __init__(self, parent, project):
        wx.Dialog.__init__(self, parent, title="Syncing project...")
        self.project = project
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        # Create status panel
        self.status = InfoStream(self, id=wx.ID_ANY, size=(-1, -1),
                                 value=_translate("Synchronising..."),
                                 style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.sizer.Add(self.status, border=6, proportion=1, flag=wx.ALL | wx.EXPAND)
        # Setup button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, border=6, flag=wx.ALL | wx.EXPAND)
        self.btnSizer.AddStretchSpacer(1)
        # Add buttons
        self.OKbtn = wx.Button(self, label=_translate("Okay"), id=wx.ID_OK)
        self.OKbtn.Disable()
        self.btnSizer.Add(self.OKbtn, border=3, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        # Layout
        self.Layout()
        self.Show()
        # Do sync
        self.project.sync(self.status)
        self.OKbtn.Enable()


class InfoStream(wx.TextCtrl):
    def __init__(self, parent, id, size,
                 value="Synchronising...",
                 style=wx.TE_READONLY | wx.TE_MULTILINE):
        wx.TextCtrl.__init__(self, parent, id,
                             size=size, value=value, style=style)

    def clear(self):
        self.SetValue("")

    def write(self, text):
        if type(text) == bytes:
            text = text.decode('utf-8')
        self.SetValue(self.GetValue() + text)
        wx.Yield()
