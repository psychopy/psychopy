#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import requests

from psychopy import logging
from .. import dialogs
from .functions import logInPavlovia
from psychopy.app.pavlovia_ui.project import syncProject
from .search import SearchFrame
from .project import ProjectEditor
from psychopy.localization import _translate
from psychopy.projects import pavlovia


class PavloviaMenu(wx.Menu):
    app = None
    appData = None
    currentUser = None
    knownUsers = None
    searchDlg = None

    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent  # type: BuilderFrame
        PavloviaMenu.app = parent.app
        keys = self.app.keys
        # from prefs fetch info about prev usernames and projects
        PavloviaMenu.appData = self.app.prefs.appData['projects']

        # item = self.Append(wx.ID_ANY, _translate("Tell me more..."))
        # parent.Bind(wx.EVT_MENU, self.onAbout, id=item.GetId())

        PavloviaMenu.knownUsers = pavlovia.knownUsers

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        lastPavUser = PavloviaMenu.appData['pavloviaUser']
        if pavlovia.knownUsers and (lastPavUser not in pavlovia.knownUsers):
            lastPavUser = None
        if lastPavUser and not PavloviaMenu.currentUser:
            self.setUser(PavloviaMenu.appData['pavloviaUser'])
        for name in self.knownUsers:
            self.addToSubMenu(name, self.userMenu, self.onSetUser)
        self.userMenu.AppendSeparator()
        item = self.userMenu.Append(wx.ID_ANY,
                                    _translate("Log in to Pavlovia...\t{}")
                                    .format(keys['pavlovia_logIn']))
        parent.Bind(wx.EVT_MENU, self.onLogInPavlovia, id=item.GetId())
        self.AppendSubMenu(self.userMenu, _translate("User"))

        # search
        item = self.Append(wx.ID_ANY,
                           _translate("Search Pavlovia\t{}")
                           .format(keys['projectsFind']))
        parent.Bind(wx.EVT_MENU, self.onSearch, id=item.GetId())

        # new
        item = self.Append(wx.ID_ANY,
                           _translate("New...\t{}").format(keys['projectsNew']))
        parent.Bind(wx.EVT_MENU, self.onNew, id=item.GetId())

        item = self.Append(wx.ID_ANY,
                           _translate("Sync\t{}").format(keys['projectsSync']))
        parent.Bind(wx.EVT_MENU, self.onSync, id=item.GetId())

    def addToSubMenu(self, name, menu, function):
        item = menu.Append(wx.ID_ANY, name)
        self.parent.Bind(wx.EVT_MENU, function, id=item.GetId())

    def onAbout(self, event):
        wx.GetApp().followLink(event)

    def onSetUser(self, event):
        user = self.userMenu.GetLabelText(event.GetId())
        self.setUser(user)

    def setUser(self, user):
        if user == PavloviaMenu.currentUser:
            return  # nothing to do here. Move along please.
        PavloviaMenu.currentUser = user
        PavloviaMenu.appData['pavloviaUser'] = user
        if user in pavlovia.knownUsers:
            token = pavlovia.knownUsers[user]['token']
            try:
                pavlovia.getCurrentSession().setToken(token)
            except requests.exceptions.ConnectionError:
                logging.warning("Tried to log in to Pavlovia but no network "
                                "connection")
                return
        else:
            self.onLogInPavlovia()

        if self.searchDlg:
            self.searchDlg.updateUserProjs()

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
        if pavlovia.getCurrentSession().user.username:
            projEditor = ProjectEditor()
            if projEditor.ShowModal() == wx.ID_OK:
                self.parent.project = projEditor.project
                # do a first sync as well
                syncProject(parent=self.parent, project=projEditor.project)
        else:
            infoDlg = dialogs.MessageDialog(parent=None, type='Info',
                                            message=_translate(
                                                    "You need to log in"
                                                    " to create a project"))
            infoDlg.Show()
