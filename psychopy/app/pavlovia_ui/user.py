#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from .functions import logInPavlovia, logOutPavlovia
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy import prefs

import os
import wx
try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl # <3.0.2

resources = prefs.paths['resources']


class UserEditor(wx.Dialog):
    defStyle = wx.DEFAULT_DIALOG_STYLE #| wx.RESIZE_BORDER
    def __init__(self, parent=None, id=wx.ID_ANY, style=defStyle,
                 *args, **kwargs):

        wx.Dialog.__init__(self, parent, id,
                           *args, style=style, **kwargs)
        self.SetWindowStyle(wx.STAY_ON_TOP)  # this will be a modal dialog

        panel = wx.Panel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        pavSession = pavlovia.getCurrentSession()
        if pavSession.user:
            pavSession.gitlab.auth()
            self.user = pavSession.user
        else:
            self.user = logInPavlovia(parent=parent)
            if not self.user:
                return  # they were given a login but cancelled
        if type(self.user) != pavlovia.User:
            self.user = pavlovia.User(gitlabData=self.user)

        # create the controls
        userField = wxhl.HyperLinkCtrl(panel, id=wx.ID_ANY,
                                       label=self.user.url, URL=self.user.url)
        logoutBtn = wx.Button(panel, label="Logout")
        logoutBtn.Bind(wx.EVT_BUTTON, self.onLogout)
        nameLabel = wx.StaticText(panel, id=wx.ID_ANY, label=_translate("Full name:"))
        self.nameField = wx.StaticText(panel, wx.ID_ANY, self.user.name)
        if self.user.avatar:
            userBitmap = wx.Bitmap(self.user.avatar)
        else:
            userBitmap = wx.Bitmap(os.path.join(resources, "user128invisible.png"))
        # self.avatarBtn = wx.Button(panel, wx.ID_ANY, name="Avatar")
        # self.avatarBtn.SetBitmap(userBitmap)
        self.avatarBtn = wx.BitmapButton(panel, wx.ID_ANY,
                                         bitmap=userBitmap, name="Avatar")
        # self.avatarBtn.SetBitmap(userBitmap)

        org = self.user.organization or ""
        orgLabel = wx.StaticText(panel, wx.ID_ANY, _translate("Organization:"))
        self.orgField = wx.StaticText(panel, wx.ID_ANY, org, size=(300, -1))

        bio = self.user.bio or ""
        self.bioLabel = wx.StaticText(panel, wx.ID_ANY, _translate("Bio (250 chrs):"))
        self.bioField = wx.StaticText(panel, wx.ID_ANY, bio,
                                    style=wx.TE_MULTILINE)
        # submit/cancel
        buttonMsg = _translate("OK")
        updateBtn = wx.Button(panel, id=wx.ID_OK, label=buttonMsg)
        updateBtn.Bind(wx.EVT_BUTTON, self.submitChanges)
        # cancelBtn = wx.Button(panel, id=wx.ID_CANCEL, label=_translate("Cancel"))
        # cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)

        # layout
        userAndLogout = wx.BoxSizer(wx.VERTICAL)
        userAndLogout.Add(userField, 1, wx.ALL | wx.CENTER | wx.ALIGN_CENTER_VERTICAL, 5)
        userAndLogout.Add(logoutBtn, 0, wx.ALL | wx.CENTER | wx.ALIGN_CENTER_VERTICAL , 5)
        topRow = wx.BoxSizer(wx.HORIZONTAL)
        topRow.Add(userAndLogout, 1, wx.ALL | wx.CENTER, 5)
        topRow.Add(self.avatarBtn, 0, wx.ALL | wx.RIGHT, 5)

        fieldsSizer = wx.FlexGridSizer(cols=2, rows=5, vgap=10, hgap=10)
        fieldsSizer.AddMany([
            (nameLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (self.nameField,0, wx.EXPAND),
            (orgLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (self.orgField,0, wx.EXPAND),
            (self.bioLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (self.bioField, 1, wx.EXPAND),
        ])

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(updateBtn, flag=wx.ALIGN_RIGHT)

        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(topRow, 0, wx.ALL| wx.EXPAND, 5)
        border.Add(fieldsSizer, 1, wx.ALL | wx.EXPAND, 10)
        border.Add(btnSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        panel.SetSizerAndFit(border)
        self.Fit()

    def onLogout(self, evt=None):
        logOutPavlovia(self.parent)
        self.user = None
        self.Close()

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)

    def submitChanges(self, evt=None):
        # print("updating gitlab.pavlovia.org users from within PsychoPy not yet working")
        # isDirty = False
        # toCheck = {'name': self.nameField.GetValue,
        #            'organization': self.orgField.GetValue,
        #            'bio': self.bioField.GetValue,
        #            }
        # for field in toCheck:
        #     newVal = toCheck[field]()
        #     prev = getattr(self.user, field)
        #     if prev != newVal and not (prev is None and newVal==""):
        #         setattr(self.user, field, newVal)
        #         isDirty = True
        # if isDirty:
        #     # currently gives an error:
        #     # https://github.com/python-gitlab/python-gitlab/issues/547
        #     self.user.save()
        self.EndModal(wx.ID_OK)

    def onSetAvatar(self, event=None):
        print("Uploading a user image (avatar) from within PsychoPy is not yet supported. "
              "You can do that by going to the gitlab.pavlovia.org profile settings.")

    def onURL(self, evt):
        print(dir(evt))
