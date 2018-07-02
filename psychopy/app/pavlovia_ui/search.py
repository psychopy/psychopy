#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from past.builtins import basestring
import wx
from wx.lib import scrolledpanel as scrlpanel

from .project import DetailsPanel
from ._base import BaseFrame
from psychopy.localization import _translate
from psychopy.projects import pavlovia


class SearchFrame(BaseFrame):

    def __init__(self, app, parent=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=None):
        if style is None:
            style = (wx.DEFAULT_DIALOG_STYLE | wx.CENTER |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        title = _translate("Search for projects online")
        self.frameType = 'ProjectSearch'
        BaseFrame.__init__(self, parent, -1, title, pos, size, style)
        self.app = app
        self.project = None
        self.parent = parent

        # to show detail of current selection
        self.detailsPanel = DetailsPanel(parent=self)

        # create list of my projects (no search?)
        self.myProjectsPanel = ProjectListPanel(self, self.detailsPanel)

        # create list of searchable public projects
        self.publicProjectsPanel = ProjectListPanel(self, self.detailsPanel)
        self.publicProjectsPanel.setContents('')

        # sizers: on the left we have search boxes
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.StaticText(self, -1, _translate("My Projects")),
                      flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(self.myProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, -1, _translate("Search Public:")))
        self.searchTextCtrl = wx.TextCtrl(self, -1, "",
                                          style=wx.TE_PROCESS_ENTER)
        self.searchTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        searchSizer.Add(self.searchTextCtrl, flag=wx.EXPAND)
        leftSizer.Add(searchSizer)
        tagsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagsSizer.Add(wx.StaticText(self, -1, _translate("Tags:")))
        self.tagsTextCtrl = wx.TextCtrl(self, -1, "psychopy,",
                                        style=wx.TE_PROCESS_ENTER)
        self.tagsTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        tagsSizer.Add(self.tagsTextCtrl, flag=wx.EXPAND)
        leftSizer.Add(tagsSizer)
        leftSizer.Add(self.publicProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(leftSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.mainSizer.Add(self.detailsPanel, flag=wx.EXPAND, proportion=1,
                           border=5)
        self.SetSizerAndFit(self.mainSizer)

        aTable = wx.AcceleratorTable([(0, wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      ])
        self.SetAcceleratorTable(aTable)
        if self.parent:
            self.CenterOnParent()
        self.Show()  # show the window before doing search/updates
        self.updateUserProjs()  # update the info in myProjectsPanel

    def updateUserProjs(self):
        if not pavlovia.currentSession.user:
            self.myProjectsPanel.setContents(
                    _translate("No user logged in"))
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


class ProjectListPanel(scrlpanel.ScrolledPanel):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """

    def __init__(self, parent, detailsPanel):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, size=(450, 200),
                                         style=wx.SUNKEN_BORDER)
        self.parent = parent
        self.projList = []
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)  # don't do Fit
        self.mainSizer.Fit(self)

        self.SetAutoLayout(True)
        self.SetupScrolling()

    def setContents(self, projects):
        self.DestroyChildren()  # start with a clean slate

        if isinstance(projects, basestring):
            # just text for a window so display
            self.mainSizer.Add(
                    wx.StaticText(self, -1, projects),
                    flag=wx.EXPAND | wx.ALL, border=5,
            )
        else:
            # a list of projects
            self.projView = wx.ListCtrl(parent=self,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

            # Give it some columns.
            # The ID col we'll customize a bit:
            self.projView.InsertColumn(0, 'owner')
            self.projView.InsertColumn(1, 'name')
            self.projView.InsertColumn(1, 'description')
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
            self.mainSizer.Add(self.projView,
                               flag=wx.EXPAND | wx.ALL,
                               proportion=1, border=5, )
            self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                      self.onChangeSelection)

        self.FitInside()

    def onChangeSelection(self, event):
        proj = self.projList[event.GetIndex()]
        self.parent.detailsPanel.setProject(proj)
        self.project = proj