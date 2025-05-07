#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import io

import wx
import requests

from psychopy import logging
from .. import dialogs
from ..themes import icons
from .functions import logInPavlovia
from psychopy.app.pavlovia_ui.project import syncProject
from .search import SearchFrame
from .project import ProjectEditor
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy.app.pavlovia_ui import sync


class PavloviaMenu(wx.Menu):
    app = None
    appData = None
    currentUser = None
    knownUsers = None
    searchDlg = None

    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent  # is a BuilderFrame
        PavloviaMenu.app = parent.app
        keys = self.app.keys
        # from prefs fetch info about prev usernames and projects
        PavloviaMenu.appData = self.app.prefs.appData['projects']

        # item = self.Append(wx.ID_ANY, _translate("Tell me more..."))
        # parent.Bind(wx.EVT_MENU, self.onAbout, id=item.GetId())
        # parent.Bind(wx.EVT_MENU, self.onAbout, id=item.GetId())

        PavloviaMenu.knownUsers = pavlovia.knownUsers

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        lastPavUser = PavloviaMenu.appData['pavloviaUser']
        if pavlovia.knownUsers and (lastPavUser not in pavlovia.knownUsers):
            lastPavUser = None
        # if lastPavUser and not PavloviaMenu.currentUser:
        #     self.setUser(PavloviaMenu.appData['pavloviaUser'])
        if self.knownUsers is not None:
            for name in self.knownUsers:
                self.addToSubMenu(name, self.userMenu, self.onSetUser)

        self.userMenu.AppendSeparator()
        self.loginBtn = self.userMenu.Append(wx.ID_ANY,
                                    _translate("Log in to Pavlovia...\t{}")
                                    .format(keys['pavlovia_logIn']))
        parent.Bind(wx.EVT_MENU, self.onLogInPavlovia, id=self.loginBtn.GetId())
        self.AppendSubMenu(self.userMenu, _translate("User"))

        # search
        self.searchBtn = self.Append(wx.ID_ANY,
                           _translate("Search Pavlovia\t{}")
                           .format(keys['projectsFind']))
        parent.Bind(wx.EVT_MENU, self.onSearch, id=self.searchBtn.GetId())

        # new
        self.newBtn = self.Append(wx.ID_ANY,
                           _translate("New...\t{}").format(keys['projectsNew']))
        parent.Bind(wx.EVT_MENU, self.onNew, id=self.newBtn.GetId())

        self.syncBtn = self.Append(wx.ID_ANY,
                           _translate("Sync\t{}").format(keys['projectsSync']))
        parent.Bind(wx.EVT_MENU, self.onSync, id=self.syncBtn.GetId())

    def addToSubMenu(self, name, menu, function):
        item = menu.Append(wx.ID_ANY, name)
        self.parent.Bind(wx.EVT_MENU, function, id=item.GetId())

    def onAbout(self, event):
        wx.GetApp().followLink(event)

    def onSetUser(self, event):
        user = self.userMenu.GetLabelText(event.GetId())
        self.setUser(user)

    def setUser(self, user=None):
        if PavloviaMenu.appData:
            if user is None and PavloviaMenu.appData['pavloviaUser']:
                user = PavloviaMenu.appData['pavloviaUser']

        if user in [PavloviaMenu.currentUser, None]:
            return  # nothing to do here. Move along please.

        PavloviaMenu.currentUser = user
        PavloviaMenu.appData['pavloviaUser'] = user
        if user in pavlovia.knownUsers:
            token = pavlovia.knownUsers[user]['token']
            try:
                pavlovia.login(token)
            except requests.exceptions.ConnectionError:
                logging.warning("Tried to log in to Pavlovia but no network "
                                "connection")
                return
        else:
            if hasattr(self, 'onLogInPavlovia'):
                self.onLogInPavlovia()

        if PavloviaMenu.searchDlg:
            PavloviaMenu.searchDlg.updateUserProjs()

    def onSync(self, event):
        syncProject(parent=self.parent, project=self.parent.project)

    def onSearch(self, event):
        PavloviaMenu.searchDlg = SearchFrame(app=self.parent.app)
        PavloviaMenu.searchDlg.Show()

    def onLogInPavlovia(self, event=None):
        logInPavlovia(parent=self.parent)

    def onNew(self, event):
        """Create a new project
        """
        # Get session
        session = pavlovia.getCurrentSession()
        # If logged in, create project
        if session.user:
            dlg = sync.CreateDlg(self.parent, user=session.user)
            dlg.ShowModal()
        # Otherwise, prompt user to log in
        else:
            infoDlg = dialogs.MessageDialog(parent=None, type='Info',
                                            message=_translate(
                                                    "You need to log in"
                                                    " to create a project"))
            infoDlg.Show()
