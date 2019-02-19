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

import copy
import wx
from pkg_resources import parse_version
from wx.lib import scrolledpanel as scrlpanel
import wx.lib.mixins.listctrl as listmixin

import requests

starChar = u"\u2B50"
forkChar = u"\u2442"


class SearchFrame(wx.Dialog):

    def __init__(self, app, parent=None, style=None,
                 pos=wx.DefaultPosition):
        if style is None:
            style = (wx.DEFAULT_DIALOG_STYLE | wx.CENTER |
                     wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        title = _translate("Search for projects online")
        self.frameType = 'ProjectSearch'
        wx.Dialog.__init__(self, parent, -1, title=title, style=style,
                           size=(800, 500), pos=pos)

        self.app = app
        self.project = None
        self.parent = parent
        # info about last search (NB None means no search but [] or '' means empty)
        self.lastSearchStr = None
        self.lastSearchOwn = None
        self.lastSearchGp = None
        self.lastSearchPub = None

        # self.mainPanel = wx.Panel(self, wx.ID_ANY)
        self.searchLabel = wx.StaticText(self, wx.ID_ANY, _translate('Search:'))
        self.searchCtrl = wx.TextCtrl(self, wx.ID_ANY)
        self.searchCtrl.Bind(wx.EVT_BUTTON, self.onSearch)
        self.searchBtn = wx.Button(self, wx.ID_ANY, _translate("Search"))
        self.searchBtn.Bind(wx.EVT_BUTTON, self.onSearch)
        self.searchBtn.SetDefault()

        self.searchInclPublic = wx.CheckBox(self, wx.ID_ANY,
                                          label="Public")
        self.searchInclPublic.Bind(wx.EVT_CHECKBOX, self.onSearch)
        self.searchInclPublic.SetValue(True)

        self.searchInclGroup = wx.CheckBox(self, wx.ID_ANY,
                                          label="My groups")
        self.searchInclGroup.Bind(wx.EVT_CHECKBOX, self.onSearch)
        self.searchInclGroup.SetValue(True)

        self.searchBuilderOnly = wx.CheckBox(self, wx.ID_ANY,
                                             label="Only Builder")
        self.searchBuilderOnly.Bind(wx.EVT_CHECKBOX, self.onSearch)
        # then the search results
        self.searchResults = ProjectListCtrl(self)

        # on the right
        self.detailsPanel = DetailsPanel(parent=self)

        # sizers layout
        self.searchBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.searchBtnSizer.Add(self.searchCtrl, 1, wx.EXPAND | wx.ALL, 5)
        self.searchBtnSizer.Add(self.searchBtn, 0, wx.EXPAND | wx.ALL, 5)
        self.optionsSizer = wx.WrapSizer()
        self.optionsSizer.AddMany([self.searchInclGroup, self.searchInclPublic,
                                   self.searchBuilderOnly])

        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftSizer.Add(self.searchLabel, 0, wx.EXPAND | wx.ALL, 5)
        self.leftSizer.Add(self.optionsSizer)
        self.leftSizer.Add(self.searchBtnSizer, 0, wx.EXPAND | wx.ALL, 5)
        self.leftSizer.Add(self.searchResults, 1, wx.EXPAND | wx.ALL, 5)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.leftSizer, 1, wx.EXPAND | wx.ALL, 5)
        self.mainSizer.Add(self.detailsPanel, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(self.mainSizer)  # don't fit until search is populated
        if self.parent:
            self.CenterOnParent()
        self.Layout()
        # if projects == 'no user':
        #     msg = _translate("Log in to search your own projects")
        #     loginBtn = wx.Button(self, wx.ID_ANY, label=msg)
        #     loginBtn.Bind(wx.EVT_BUTTON, self.onLoginClick)

    def getSearchOptions(self):
        opts = {}
        opts['inclPublic'] = self.searchInclPublic.GetValue()
        opts['builderOnly'] = self.searchBuilderOnly.GetValue()
        opts['inclGroup'] = self.searchBuilderOnly.GetValue()
        return opts

    def onSearch(self, evt=None):
        opts = self.getSearchOptions()

        searchStr = self.searchCtrl.GetValue()
        newSearch = (searchStr!=self.lastSearchStr)
        self.lastSearchStr = newSearch

        session = pavlovia.getCurrentSession()
        # search own
        if newSearch:
            try:
                self.lastSearchOwn = session.gitlab.projects.list(owned=True, search=searchStr)
            except requests.exceptions.ConnectionError:
                print("Failed to establish a new connection: No internet?")
                return None

        # search my groups
        if opts['inclGroup'] and (newSearch or self.lastSearchGp is None):
            # group projects: owned=False, membership=True
            self.lastSearchGp = session.gitlab.projects.list(
                owned=False, membership=True, search=searchStr)
        elif not opts['inclGroup']:  # set to None (to indicate non-search not simply empty result)
            self.lastSearchGp = None
        elif opts['inclGroup'] and not newSearch:
            pass  # we have last search and we need it so do nothing
        else:
            print("ERROR: During Pavlovia search we found opts['inclGroup']={}, newSearch={}"
                  .format(opts['inclGroup'], newSearch))

        # search public
        if opts['inclPublic'] and (newSearch or self.lastSearchPub is None):
            self.lastSearchPub = session.gitlab.projects.list(owned=False, membership=False,
                                                              search=searchStr)
        elif not opts['inclPublic']:  # set to None (to indicate non-search not simply empty result)
            self.lastSearchPub = None
        elif opts['inclPublic'] and not newSearch:
            pass  # we have last search and we need it so do nothing
        else:
            print("ERROR: During Pavlovia search we found opts['inclPublic']={}, newSearch={}"
                  .format(opts['inclPublic'], newSearch))

        projs = copy.copy(self.lastSearchOwn)
        if opts['inclGroup']:
            projs.extend(self.lastSearchGp)
        if opts['inclPublic']:
            projs.extend(self.lastSearchPub)

        projs = getUniqueByID(projs)
        projs = [pavlovia.PavloviaProject(proj) for proj in projs if proj.id]

        self.searchResults.setContents(projs)
        self.searchResults.Update()
        self.Layout()

    def onLoginClick(self, event):
        user = logInPavlovia(parent=self.parent)

    def Show(self):
        # show the dialog then start search
        wx.Dialog.Show(self)
        wx.Yield()
        self.onSearch()  # trigger the search update


class ProjectListCtrl(wx.ListCtrl, listmixin.ListCtrlAutoWidthMixin):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """

    def __init__(self, parent, frame=None):
        wx.ListCtrl.__init__(self, parent, wx.ID_ANY,
                             style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        listmixin.ListCtrlAutoWidthMixin.__init__(self)
        self.AlwaysShowScrollbars(True)
        self.parent = parent
        if frame is None:
            self.frame = parent
        else:
            self.frame = frame
        self.projList = []
        self.columnNames = [starChar, forkChar, 'Group', 'Name', 'Description']
        self._currentSortCol = 0
        self._currentSortRev = False

        # Give it some columns.
        # The ID col we'll customize a bit:
        for n, columnName in enumerate(self.columnNames):
            if len(columnName) < 3:  # for short names center the text
                self.InsertColumn(n, columnName, wx.LIST_FORMAT_CENTER)
            else:
                self.InsertColumn(n, columnName)
        # set the column sizes *after* adding the items
        for n, columnName in enumerate(self.columnNames):
            self.SetColumnWidth(n, wx.LIST_AUTOSIZE)

        # after creating columns we can create the sort mixin
        # listmixin.ColumnSorterMixin.__init__(self, len(columnList))
        self.SetAutoLayout(True)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.onColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onChangeSelection)

    def setContents(self, projects):
        self.DeleteAllItems()
        # first time around we have a list of PavloviaProjects
        if projects and isinstance(projects[0], pavlovia.PavloviaProject):
            self.projList = []
            for index, thisProj in enumerate(projects):
                if not hasattr(thisProj, 'id'):
                    continue
                data = (thisProj.star_count, thisProj.forks_count,
                        thisProj.group, thisProj.name, thisProj.description)
                proj = {}
                proj[starChar] = thisProj.star_count
                proj[forkChar] = thisProj.forks_count
                proj['Name'] = thisProj.name
                proj['Group'] = thisProj.group
                proj['Description'] = thisProj.description
                proj['id'] = thisProj.id
                self.projList.append(proj)
                self.Append(data)  # append to the wx table
        # subsequent iterations are simple dicts
        else:
            self.projList = projects
            for index, thisProj in enumerate(projects):
                data = (thisProj[starChar], thisProj[forkChar],
                        thisProj['Group'], thisProj['Name'],
                        thisProj['Description'])
                self.Append(data)  # append to the wx table
        self.resizeCols(finalOnly=False)
        self.Update()

    def resizeCols(self, finalOnly):
        # resize the columns
        for n in range(self.ColumnCount):
            if not finalOnly:
                self.SetColumnWidth(n, wx.LIST_AUTOSIZE_USEHEADER)
                if self.GetColumnWidth(n) > 100:
                    self.SetColumnWidth(n, 100)

    def onChangeSelection(self, event):
        proj = self.projList[event.GetIndex()]
        self.frame.detailsPanel.setProject(proj['id'])

    def onColumnClick(self, event=None):
        col = event.Column
        if col == self._currentSortCol:  # toggle direction
            self._currentSortRev = not(self._currentSortRev)
        self._currentSortCol = col
        projs = sortProjects(self.projList, self.columnNames[col],
                             reverse=self._currentSortRev)
        self.setContents(projs)


def sortProjects(seq, name, reverse=False):
    return sorted(seq, key=lambda k: k[name], reverse=reverse)

def getUniqueByID(seq):
    """Very fast function to remove duplicates from a list while preserving order

    Based on sort f8() by Dave Kirby
    benchmarked at https://www.peterbe.com/plog/uniqifiers-benchmark

    Requires Python>=2.7 (requires set())
    """
    # Order preserving
    seen = set()
    return [x for x in seq if x.id not in seen and not seen.add(x.id)]
