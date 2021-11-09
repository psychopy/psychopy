#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import tempfile

from .functions import logInPavlovia, logOutPavlovia
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy.app import utils
import requests
import io
from psychopy import prefs
import os
import wx
try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl # <3.0.2


class UserFrame(wx.Dialog):
    def __init__(self, parent,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER | wx.TAB_TRAVERSAL | wx.RESIZE_BORDER,
                 size=(-1, -1)):

        wx.Dialog.__init__(self, parent,
                           style=style,
                           size=size)
        self.app = parent.app
        self.sizer = wx.BoxSizer()
        self.sizer.Add(UserPanel(self), proportion=1, border=12, flag=wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(self.sizer)


class UserPanel(wx.Panel):
    def __init__(self, parent,
                 size=(600, 500),
                 style=wx.NO_BORDER):
        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style)
        self.parent = parent
        self.SetBackgroundColour("white")
        self.session = pavlovia.getCurrentSession()
        iconCache = parent.app.iconCache
        # Setup sizer
        self.contentBox = wx.BoxSizer()
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)
        # Head sizer
        self.headSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headSizer, border=0, flag=wx.EXPAND)
        # Icon
        self.icon = utils.ImageCtrl(self, bitmap=wx.Bitmap(), size=(128, 128))
        self.icon.SetBackgroundColour("#f2f2f2")
        self.icon.Bind(wx.EVT_FILEPICKER_CHANGED, self.updateUser)
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL)
        # Title sizer
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, flag=wx.EXPAND)
        # Full name
        self.fullName = wx.TextCtrl(self, size=(-1, -1), value="---")
        self.fullName.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.fullName.Bind(wx.EVT_TEXT, self.updateUser)
        self.titleSizer.Add(self.fullName, border=6, flag=wx.ALL | wx.EXPAND)
        # Organisation
        self.organisation = wx.TextCtrl(self, size=(-1, -1), value="---")
        self.organisation.Bind(wx.EVT_TEXT, self.updateUser)
        self.titleSizer.Add(self.organisation, border=6, flag=wx.ALL | wx.EXPAND)
        # Spacer
        self.titleSizer.AddStretchSpacer(1)
        # Button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.Add(self.btnSizer, flag=wx.EXPAND)
        # Spacer
        self.btnSizer.AddStretchSpacer(1)
        # Pavlovia link
        self.link = wxhl.HyperLinkCtrl(self, -1,
                                       label="",
                                       URL="https://gitlab.pavlovia.org/",
                                       )
        self.link.SetBackgroundColour(self.GetBackgroundColour())
        self.btnSizer.Add(self.link, border=6, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Login
        self.login = wx.Button(self, label=_translate("Login"), style=wx.BORDER_NONE)
        self.login.SetBitmap(iconCache.getBitmap(name="person_off", size=16))
        self.login.Bind(wx.EVT_BUTTON, self.onLogin)
        self.btnSizer.Add(self.login, border=6, flag=wx.ALL | wx.EXPAND)
        # Logout
        self.logout = wx.Button(self, label=_translate("Logout"), style=wx.BORDER_NONE)
        self.logout.SetBitmap(iconCache.getBitmap(name="person_off", size=16))
        self.logout.Bind(wx.EVT_BUTTON, self.onLogout)
        self.btnSizer.Add(self.logout, border=6, flag=wx.ALL | wx.EXPAND)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Bio
        self.description = wx.TextCtrl(self, size=(-1, -1), value="", style=wx.TE_MULTILINE)
        self.description.SetMaxLength(250)
        self.description.Bind(wx.EVT_TEXT, self.updateUser)
        self.sizer.Add(self.description, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Populate
        self.user = self.user

    @property
    def user(self):
        if not hasattr(self, "_user"):
            self._user = self.session.user
        return self._user

    @user.setter
    def user(self, user):
        self._user = user

        if user is None:
            # Icon
            self.icon.SetBitmap(wx.Bitmap())
            self.icon.Disable()
            # Full name
            self.fullName.SetValue("---")
            self.fullName.Disable()
            # Organisation
            self.organisation.SetValue("---")
            self.organisation.Disable()
            # Link
            self.link.SetLabel("")
            self.link.SetURL("https://pavlovia.org/")
            self.link.Disable()
            # Hide logout and show login
            self.logout.Hide()
            self.login.Show()
            # Description
            self.description.SetValue("")
            self.description.Disable()
        else:
            try:
                content = requests.get(user['avatar_url']).content
                icon = wx.Bitmap(wx.Image(io.BytesIO(content)))
            except requests.exceptions.MissingSchema:
                icon = wx.Bitmap()
            self.icon.SetBitmap(icon)
            self.icon.Enable()
            # Full name
            self.fullName.SetValue(user['name'] or "")
            self.fullName.Enable()
            # Organisation
            self.organisation.SetValue(user['organization'] or "No organization")
            self.organisation.Enable()
            # Link
            self.link.SetLabel(user['username'])
            self.link.SetURL(user['web_url'] or "")
            self.link.Enable()
            # Hide logout and show login
            self.logout.Show()
            self.login.Hide()
            # Description
            self.description.SetValue(user['bio'] or "")
            self.description.Enable()
        self.Layout()

    def onLogout(self, evt=None):
        self.user = logOutPavlovia(self.parent)

    def onLogin(self, evt=None):
        self.user = logInPavlovia(parent=self.parent)

    def updateUser(self, evt=None):
        # Skip if no user
        if self.user is None or evt is None or self.session.user is None:
            return
        # Get object
        obj = evt.GetEventObject()
        # Update full name
        if obj == self.fullName:
            self.user.name = self.fullName.GetValue()
            #self.user.save()
        # Update organisation
        if obj == self.organisation:
            self.user.organization = self.organisation.GetValue()
            #self.user.save()
        # Update bio
        if obj == self.description:
            self.user.bio = self.description.GetValue()
            #self.user.save()
        # Update avatar
        if obj == self.icon:
            # Create temporary image file
            _, temp = tempfile.mkstemp(suffix=".png")
            self.icon.BitmapFull.SaveFile(temp, wx.BITMAP_TYPE_PNG)
            # Load and upload from temp file
            self.user.avatar = open(temp, "rb")
            #self.user.save()
