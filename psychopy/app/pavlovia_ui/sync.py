#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from .. import utils
import re
from pathlib import Path
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


class CreateDlg(wx.Dialog):
    def __init__(self, parent, user):
        wx.Dialog.__init__(self, parent=parent,
                           title=_translate("New project..."),
                           size=(500, 200), style=wx.DEFAULT_DIALOG_STYLE | wx.CLOSE_BOX)
        self.user = user
        self.session = parent.session
        self.project = None

        # Setup sizer
        self.frame = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.frame)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.frame.Add(self.sizer, border=6, proportion=1, flag=wx.ALL | wx.EXPAND)

        # Name label
        self.nameLbl = wx.StaticText(self, label=_translate("Project name:"))
        self.sizer.Add(self.nameLbl, border=3, flag=wx.ALL | wx.EXPAND)
        # Name ctrls
        self.nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.nameSizer, border=3, flag=wx.ALL | wx.EXPAND)
        # URL prefix
        self.nameRootLbl = wx.StaticText(self, label=f"pavlovia.org/{user['username']}/")
        self.nameSizer.Add(self.nameRootLbl, border=3, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Name ctrl
        self.nameCtrl = wx.TextCtrl(self)
        self.nameCtrl.Bind(wx.EVT_TEXT, self.validate)
        self.nameSizer.Add(self.nameCtrl, border=3, proportion=1, flag=wx.ALL | wx.EXPAND)

        # Local root label
        self.rootLbl = wx.StaticText(self, label=_translate("Project folder:"))
        self.sizer.Add(self.rootLbl, border=3, flag=wx.ALL | wx.EXPAND)
        # Local root ctrl
        self.rootCtrl = utils.FileCtrl(self, dlgtype="dir")
        self.rootCtrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.validate)
        self.sizer.Add(self.rootCtrl, border=3, flag=wx.ALL | wx.EXPAND)

        # Add OK button
        self.sizer.AddStretchSpacer(1)
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, border=3, flag=wx.ALL | wx.EXPAND)
        self.btnSizer.AddStretchSpacer(1)
        self.OKbtn = wx.Button(self, label=_translate("Okay"))
        self.OKbtn.Bind(wx.EVT_BUTTON, self.submit)
        self.SetAffirmativeId(wx.ID_OK)
        self.btnSizer.Add(self.OKbtn, border=3, flag=wx.ALL)

        self.Layout()
        self.validate()

    def validate(self, evt=None):
        # Test name
        name = self.nameCtrl.GetValue()
        nameValid = bool(re.fullmatch("\w+", name))
        # Test path
        path = Path(self.rootCtrl.GetValue())
        pathValid = path.is_dir()
        # Combine
        valid = nameValid and pathValid
        # Enable/disable Okay button
        self.OKbtn.Enable(valid)

        return valid

    def submit(self, evt=None):
        self.project = self.session.createProject(**self.GetValue())
        self.Close()

    def GetValue(self):
        return {"name": self.nameCtrl.GetValue(), "localRoot": self.rootCtrl.GetValue()}