#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys

import wx
from .. import utils
from . import functions
import re
from pathlib import Path
from psychopy.localization import _translate
from ...tools.stringtools import valid_proj_name


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
        # Sanitize text (remove sensitive info like oauth keys)
        text = utils.sanitize(text)
        # Show
        self.SetValue(self.GetValue() + text)
        wx.Yield()


class CreateDlg(wx.Dialog):
    # List of folders which are invalid paths for a pavlovia project
    invalidFolders = [Path.home() / 'Desktop',
                      Path.home() / 'My Documents',
                      Path.home() / 'Documents']

    def __init__(self, parent, user, name="", path=""):
        wx.Dialog.__init__(self, parent=parent,
                           title=_translate("New project..."),
                           size=(500, 200), style=wx.DEFAULT_DIALOG_STYLE | wx.CLOSE_BOX)
        # If there's no user yet, login
        if user is None:
            user = functions.logInPavlovia(self)

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
        self.nameRootLbl = wx.StaticText(self, label="pavlovia.org /")
        self.nameSizer.Add(self.nameRootLbl, border=3, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Namespace ctrl
        self.namespaceCtrl = wx.Choice(self, choices=[user['username']] + user.session.listUserGroups(namesOnly=True))
        self.namespaceCtrl.SetStringSelection(user['username'])
        self.nameSizer.Add(self.namespaceCtrl, border=3, flag=wx.ALL | wx.EXPAND)
        # Slash
        self.slashLbl = wx.StaticText(self, label="/")
        self.nameSizer.Add(self.slashLbl, border=3, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Name ctrl
        self.nameCtrl = wx.TextCtrl(self, value=str(name))
        self.nameCtrl.Bind(wx.EVT_TEXT, self.validate)
        self.nameSizer.Add(self.nameCtrl, border=3, proportion=1, flag=wx.ALL | wx.EXPAND)

        # Local root label
        self.rootLbl = wx.StaticText(self, label=_translate("Project folder:"))
        self.sizer.Add(self.rootLbl, border=3, flag=wx.ALL | wx.EXPAND)
        # Local root ctrl
        self.rootCtrl = utils.FileCtrl(self, value=str(path), dlgtype="dir")
        self.rootCtrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.validate)
        self.sizer.Add(self.rootCtrl, border=3, flag=wx.ALL | wx.EXPAND)

        # Add dlg buttons
        self.sizer.AddStretchSpacer(1)
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, border=3, flag=wx.ALL | wx.EXPAND)
        self.btnSizer.AddStretchSpacer(1)
        # OK button
        self.OKbtn = wx.Button(self, id=wx.ID_OK, label=_translate("OK"))
        self.OKbtn.Bind(wx.EVT_BUTTON, self.submit)
        # CANCEL button
        self.CANCELbtn = wx.Button(self, id=wx.ID_CANCEL, label=_translate("Cancel"))
        # Add dlg buttons in OS appropriate order
        if sys.platform == "win32":
            btns = [self.OKbtn, self.CANCELbtn]
        else:
            btns = [self.CANCELbtn, self.OKbtn]
        self.btnSizer.Add(btns[0], border=3, flag=wx.ALL)
        self.btnSizer.Add(btns[1], border=3, flag=wx.ALL)

        self.Layout()
        self.validate()

    def validate(self, evt=None):
        # Test name
        name = self.nameCtrl.GetValue()
        nameValid = bool(valid_proj_name.fullmatch(name))
        # Test path
        path = Path(self.rootCtrl.GetValue())
        pathValid = path.is_dir() and path not in self.invalidFolders
        # Combine
        valid = nameValid and pathValid
        # Enable/disable Okay button
        self.OKbtn.Enable(valid)

        return valid

    def submit(self, evt=None):
        self.project = self.session.createProject(**self.GetValue())
        if self.project is not None:
            self.project.refresh()
            evt.Skip()

    def GetValue(self):
        return {
            "name": self.nameCtrl.GetValue(),
            "localRoot": self.rootCtrl.GetValue(),
            "namespace": self.namespaceCtrl.GetStringSelection()
        }