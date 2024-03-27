#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import tempfile

from . import PavloviaMiniBrowser
from .functions import logInPavlovia, logOutPavlovia
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy.app import utils
import requests
import io
from psychopy import prefs
import os
import wx
import wx.lib.statbmp

from ..themes import icons
from ...projects.pavlovia import User

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
                 size=(600, 300),
                 style=wx.NO_BORDER):
        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style)
        self.parent = parent
        self.SetBackgroundColour("white")
        self.session = pavlovia.getCurrentSession()
        # Setup sizer
        self.contentBox = wx.BoxSizer()
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)
        # Head sizer
        self.headSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headSizer, border=0, flag=wx.EXPAND)
        # Icon
        self.icon = wx.lib.statbmp.GenStaticBitmap(
            self, ID=wx.ID_ANY,
            bitmap=icons.ButtonIcon(stem="user_none", size=128, theme="light").bitmap,
            size=(128, 128))
        self.icon.SetBackgroundColour("#f2f2f2")
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL)
        # Title sizer
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, flag=wx.EXPAND)
        # Full name
        self.fullName = wx.StaticText(self, size=(-1, -1), label="---", style=wx.ST_ELLIPSIZE_END)
        self.fullName.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.fullName.Bind(wx.EVT_TEXT, self.updateUser)
        self.titleSizer.Add(self.fullName, border=6, flag=wx.ALL | wx.EXPAND)
        # Organisation
        self.organisation = wx.StaticText(self, size=(-1, -1), label="---", style=wx.ST_ELLIPSIZE_END)
        self.organisation.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        )
        self.titleSizer.Add(self.organisation, border=6, flag=wx.ALL | wx.EXPAND)
        # Spacer
        self.titleSizer.AddStretchSpacer(1)
        # Button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.Add(self.btnSizer, border=6, flag=wx.TOP | wx.BOTTOM | wx.EXPAND)
        # Spacer
        self.btnSizer.AddStretchSpacer(1)
        # Pavlovia link
        self.link = wxhl.HyperLinkCtrl(self, -1,
                                       label="",
                                       URL="https://gitlab.pavlovia.org/",
                                       )
        self.link.SetBackgroundColour(self.GetBackgroundColour())
        self.btnSizer.Add(self.link, border=6, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        # Edit
        self.edit = wx.Button(self, label=chr(int("270E", 16)), size=(24, -1))
        self.edit.Bind(wx.EVT_BUTTON, self.onEdit)
        self.btnSizer.Add(self.edit, border=3, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        # Switch user
        self.switch = wx.Button(self, label=_translate("Switch User"))
        self.switch.SetBitmap(icons.ButtonIcon(stem="view-refresh", size=16, theme="light").bitmap)
        self.switch.Bind(wx.EVT_BUTTON, self.onSwitchUser)
        self.btnSizer.Add(self.switch, border=3, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        # Login
        self.login = wx.Button(self, label=_translate("Login"))
        self.login.SetBitmap(icons.ButtonIcon(stem="person_off", size=16, theme="light").bitmap)
        self.login.Bind(wx.EVT_BUTTON, self.onLogin)
        self.btnSizer.Add(self.login, border=3, flag=wx.LEFT | wx.EXPAND)
        # Logout
        self.logout = wx.Button(self, label=_translate("Logout"))
        self.logout.SetBitmap(icons.ButtonIcon(stem="person_off", size=16, theme="light").bitmap)
        self.logout.Bind(wx.EVT_BUTTON, self.onLogout)
        self.btnSizer.Add(self.logout, border=3, flag=wx.LEFT | wx.EXPAND)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Bio
        self.description = wx.StaticText(self, size=(-1, -1), label="", style=wx.TE_MULTILINE)
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
            self.icon.SetBitmap(icons.ButtonIcon(stem="user_none", size=128, theme="light").bitmap)
            self.icon.Disable()
            # Full name
            self.fullName.SetLabelText("---")
            self.fullName.Disable()
            # Organisation
            self.organisation.SetLabelText("---")
            self.organisation.Disable()
            # Link
            self.link.SetLabel("")
            self.link.SetURL("https://pavlovia.org/")
            self.link.Disable()
            # Hide logout/switch and show login
            self.logout.Hide()
            self.switch.Hide()
            self.login.Show()
            # Disable edit
            self.edit.Disable()
            # Description
            self.description.SetLabelText("")
            self.description.Disable()
        else:
            try:
                content = requests.get(user['avatar_url']).content
                buffer = wx.Image(io.BytesIO(content))
                buffer = buffer.Scale(*self.icon.Size, quality=wx.IMAGE_QUALITY_HIGH)
                icon = wx.Bitmap(buffer)
            except requests.exceptions.MissingSchema:
                icon = wx.Bitmap()
            self.icon.SetBitmap(icon)
            self.icon.Enable()
            # Full name
            self.fullName.SetLabelText(user.user.attributes['name'] or "")
            self.fullName.Enable()
            # Organisation
            self.organisation.SetLabelText(user['organization'] or "No organization")
            self.organisation.Enable()
            # Link
            self.link.SetLabel(user['username'])
            self.link.SetURL(user['web_url'] or "")
            self.link.Enable()
            # Hide login and show logout/switch
            self.logout.Show()
            self.switch.Show()
            self.login.Hide()
            # Enable edit
            self.edit.Enable()
            # Description
            self.description.SetLabelText(user['bio'] or "")
            self.description.Wrap(self.Size[0] - 36)
            self.description.Enable()
        self.Layout()

    def onLogout(self, evt=None):
        self.user = logOutPavlovia(self.parent)

    def onLogin(self, evt=None):
        self.user = logInPavlovia(parent=self.parent)

    def onEdit(self, evt=None):
        # Open edit window
        dlg = PavloviaMiniBrowser(parent=self, loginOnly=False)
        dlg.editUserPage()
        dlg.ShowModal()
        # Refresh user on close
        self.user = User(self.user.id)

    def onSwitchUser(self, evt):
        def onSelectUser(evt):
            # Get user from menu
            id = evt.Id
            menu = evt.EventObject
            user = menu.users[id]
            # Logout
            pavlovia.logout()
            # Log back in as new user
            pavlovia.login(user['username'])
            # Update view
            self.user = pavlovia.getCurrentSession().user
            # Update cache
            prefs.appData['projects']['pavloviaUser'] = user['username']

            self.Layout()  # update the size of the button
            self.Fit()

        menu = wx.Menu()
        menu.Bind(wx.EVT_MENU, onSelectUser)
        menu.users = {}
        for key, value in pavlovia.knownUsers.items():
            item = menu.Append(id=wx.ID_ANY, item=key)
            menu.users[item.GetId()] = value
        # Get button position
        btnPos = self.switch.GetRect()
        menuPos = (btnPos[0], btnPos[1] + btnPos[3])
        # Popup menu
        self.PopupMenu(menu, menuPos)

    def updateUser(self, evt=None):
        """
        Disabled for now, as fields are not editable.
        """
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
