#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from past.builtins import basestring

from .project import DetailsPanel
from .functions import logInPavlovia

from ._base import BaseFrame
from psychopy.localization import _translate
from psychopy.projects import pavlovia

import wx
from pkg_resources import parse_version
from wx.lib import scrolledpanel as scrlpanel

if parse_version(wx.__version__) < parse_version('4.0.0a1'):
    import wx.lib.hyperlink as wxhl
else:
    import wx.lib.agw.hyperlink as wxhl


class SearchFrame(wx.Dialog):

    def __init__(self, app, parent=None, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=None):
        if style is None:
            style = (wx.DEFAULT_DIALOG_STYLE | wx.CENTER |
                     wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        title = _translate("Search for projects online")
        self.frameType = 'ProjectSearch'
        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)
        self.app = app
        self.project = None
        self.parent = parent
        self.mainPanel = wx.Panel(self, wx.ID_ANY)

        # to show detail of current selection
        self.detailsPanel = DetailsPanel(parent=self)

        # create list of my projects (no search?)
        self.myProjectsPanel = ProjectListPanel(self.mainPanel,
                                                frame=self)

        # create list of searchable public projects
        self.publicProjectsPanel = ProjectListPanel(self.mainPanel,
                                                    frame=self)
        self.publicProjectsPanel.setContents('')

        # sizers: on the left we have search boxes
        searchQuerySizer = wx.BoxSizer(wx.HORIZONTAL)
        searchQuerySizer.Add(wx.StaticText(self.mainPanel, -1, _translate("Search Public:")),
                             flag=wx.ALIGN_CENTER_VERTICAL)
        self.searchTextCtrl = wx.TextCtrl(self.mainPanel, -1, "",
                                          style=wx.TE_PROCESS_ENTER)
        self.searchTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        searchQuerySizer.Add(self.searchTextCtrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        tagsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagsSizer.Add(wx.StaticText(self.mainPanel, -1, _translate("Tags:")),
                      flag=wx.ALIGN_CENTER_VERTICAL)
        self.tagsTextCtrl = wx.TextCtrl(self.mainPanel, -1, "psychopy,",
                                        style=wx.TE_PROCESS_ENTER)
        self.tagsTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        tagsSizer.Add(self.tagsTextCtrl, flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.StaticText(self.mainPanel, wx.ID_ANY, _translate("My Projects")),
                      # proportion=1,
                      # flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=5)
        leftSizer.Add(self.myProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)
        leftSizer.Add(searchQuerySizer)
        leftSizer.Add(tagsSizer)
        leftSizer.Add(self.publicProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(leftSizer, 1, flag=wx.EXPAND | wx.ALL, border=5)
        self.mainSizer.Add(self.detailsPanel, 1, flag=wx.EXPAND | wx.ALL, border=5)
        self.mainPanel.SetSizerAndFit(self.mainSizer)
        self.Fit()

        if self.parent:
            self.CenterOnParent()
        self.Show()  # show the window before doing search/updates
        self.updateUserProjs()  # update the info in myProjectsPanel

    def updateUserProjs(self):
        if not pavlovia.currentSession.user:
            self.myProjectsPanel.setContents("no user")
        else:
            self.myProjectsPanel.setContents(
                _translate("Searching projects for user {} ...")
                    .format(pavlovia.currentSession.user.username))
            self.Update()
            wx.Yield()
            myProjs = pavlovia.currentSession.findUserProjects()
            self.myProjectsPanel.setContents(myProjs)

    def onSearch(self, evt):
        searchStr = self.searchTextCtrl.GetValue()
        tagsStr = self.tagsTextCtrl.GetValue()
        session = pavlovia.currentSession
        self.publicProjectsPanel.setContents(_translate("searching..."))
        self.publicProjectsPanel.Update()
        wx.Yield()
        projs = session.findProjects(search_str=searchStr, tags=tagsStr)
        self.publicProjectsPanel.setContents(projs)


class ProjectListPanel(wx.Panel):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """

    def __init__(self, parent, frame=None):
        wx.Panel.__init__(self, parent, -1, size=(450, 200))
        self.parent = parent
        self.frame = frame
        self.projList = []
        # self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # self.SetSizer(self.mainSizer)  # don't do Fit
        # self.mainSizer.Fit(self)

        self.SetAutoLayout(True)
        # self.SetupScrolling()

    def setContents(self, projects):
        self.DestroyChildren()  # start with a clean slate

        if projects == 'no user':
            msg = _translate("Log in to search your own projects")
            loginBtn = wx.Button(self, wx.ID_ANY, label=msg)
            loginBtn.Bind(wx.EVT_BUTTON, self.onLoginClick)
            # self.mainSizer.Add(loginBtn, flag=wx.ALL | wx.CENTER, border=5)
        elif isinstance(projects, basestring):
            txt = wx.StaticText(self, -1, projects)
            # just text for a window so display
            # self.mainSizer.Add(txt, flag=wx.EXPAND | wx.ALL, border=5)
        else:
            # a list of projects
            self.projView = wx.ListCtrl(parent=self,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

            # Give it some columns.
            # The ID col we'll customize a bit:
            self.projView.InsertColumn(0, 'owner')
            self.projView.InsertColumn(1, 'name')
            self.projView.InsertColumn(2, 'description')
            self.projList = []
            for index, thisProj in enumerate(projects):
                if not hasattr(thisProj, 'id'):
                    continue
                self.projView.Append([thisProj.owner, thisProj.name,
                                      thisProj.description])
                self.projList.append(thisProj)
            # set the column sizes *after* adding the items
            self.projView.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.projView.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.projView.SetColumnWidth(2, wx.LIST_AUTOSIZE)
            # self.mainSizer.Add(self.projView,
            #                    flag=wx.EXPAND | wx.ALL,
            #                    proportion=1, border=5, )
            self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                      self.onChangeSelection)

        self.FitInside()

    def onLoginClick(self, event):
        logInPavlovia(parent=self.parent)

    def onChangeSelection(self, event):
        proj = self.projList[event.GetIndex()]
        self.frame.detailsPanel.setProject(proj)
