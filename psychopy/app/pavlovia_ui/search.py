#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

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

from .. import utils
from ..themes._themes import IconCache

_starred = u"\u2605"
_unstarred = u"\u2606"
forkChar = u"\u2442"


class ListCtrl(wx.ListCtrl, listmixin.ListCtrlAutoWidthMixin):
    """
    A ListCtrl with ListCtrlAutoWidthMixin already mixed in, purely for convenience
    """
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmixin.ListCtrlAutoWidthMixin.__init__(self)


class SearchFrame(wx.Dialog):

    def __init__(self, app, parent=None, style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE | wx.CENTER | wx.TAB_TRAVERSAL | wx.NO_BORDER,
                 pos=wx.DefaultPosition):
        self.frameType = 'ProjectSearch'
        wx.Dialog.__init__(self, parent, -1, title=_translate("Search for projects online"),
                           style=style,
                           size=(1080, 720), pos=pos)
        self.app = app
        self.SetMinSize((800, 500))
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        # Make panels
        self.detailsPanel = DetailsPanel(self)
        self.searchPanel = SearchPanel(self, viewer=self.detailsPanel)
        # Add to sizers
        self.sizer.Add(self.searchPanel, border=12, flag=wx.EXPAND | wx.ALL)
        self.sizer.Add(self.detailsPanel, proportion=1, border=12, flag=wx.EXPAND | wx.ALL)
        # Layout
        self.Layout()


class SearchPanel(wx.Panel):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """

    def __init__(self, parent, viewer,
                 size=(400, -1),
                 style=wx.NO_BORDER
                 ):
        # Init self
        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style
                          )
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        # Add search ctrl
        self.searchCtrl = wx.SearchCtrl(self)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.search)
        self.sizer.Add(self.searchCtrl, border=4, flag=wx.EXPAND | wx.ALL)
        # Add button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, border=4, flag=wx.EXPAND | wx.ALL)
        self.btnSizer.AddStretchSpacer(1)
        # Add sort button
        self.sortBtn = wx.Button(self, label=_translate("Sort..."), style=wx.BORDER_NONE)
        self.sortOrder = ["Stars", "Last edited"]
        self.sortBtn.Bind(wx.EVT_BUTTON, self.sort)
        self.btnSizer.Add(self.sortBtn, border=6, flag=wx.LEFT | wx.RIGHT)
        # Add filter button
        self.filterBtn = wx.Button(self, label=_translate("Filter..."), style=wx.BORDER_NONE)
        self.btnSizer.Add(self.filterBtn, border=6, flag=wx.LEFT | wx.RIGHT)

        # Add project list
        self.projectList = ListCtrl(self, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.projectList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showProject)
        self.sizer.Add(self.projectList, proportion=1, border=4, flag=wx.EXPAND | wx.ALL)
        # Setup project list
        self.projectList.InsertColumn(0, _starred, width=24, format=wx.LIST_FORMAT_CENTER)  # Stars
        self.projectList.InsertColumn(1, _translate('Author'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Author
        self.projectList.InsertColumn(2, _translate('Name'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Name
        self.projectList.InsertColumn(3, _translate('Description'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT | wx.EXPAND)  # Description
        # Setup projects dict
        self.projects = None

        # Link ProjectViewer
        self.viewer = viewer
        self.projectList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.showProject)
        # Layout
        self.Layout()

    def search(self, evt=None):
        # Get search term
        if evt is None:
            term = self.searchCtrl.GetValue()
        elif isinstance(evt, str):
            term = evt
        else:
            term = evt.GetString()
        # Abandom blank search
        if term == "":
            self.projectList.DeleteAllItems()
            self.projects = None
            return
        # Get session
        session = pavlovia.getCurrentSession()
        # Do search
        self.projects = pavlovia.PavloviaSearch(session=session, term=term)

        # Sort values
        if len(self.projects):
            self.projects.sort_values(self.sortOrder)

        # Refresh
        self.refreshCtrl()

    def refreshCtrl(self):
        # Clear list and projects dict
        self.projectList.DeleteAllItems()
        # Skip if empty search
        if len(self.projects) == 0:
            return
        # Populate list and projects dict
        for i, _ in self.projects.iterrows():
            i = self.projectList.Append([
                self.projects['nbStars'][i],
                self.projects['pathWithNamespace'][i].split('/')[0],
                self.projects['name'][i],
                self.projects['description'][i],
            ])

    def sort(self, evt=None):
        # Get list of items
        allItems = ["Stars", "Last edited", "Forks", "Date created", "Name (A-Z)"]
        items = []
        selected = [False] * len(allItems)
        # Set order from .sortOrder
        for item in self.sortOrder:
            items.append(item)
        for item in allItems:
            if item not in items:
                items.append(item)
        # Set selected from .sortOrder
        for i, item in enumerate(items):
            if item in self.sortOrder:
                selected[i] = True
        # Create dlg
        _dlg = SortDlg(self, items=items, selected=selected)
        if _dlg.ShowModal() != wx.ID_OK:
            return
        # Update sort order
        self.sortOrder = _dlg.ctrls.GetValue()
        # Sort
        self.projects.sort_values(self.sortOrder)
        # Refresh
        self.refreshCtrl()

    def showProject(self, evt=None):
        """
        View current project in associated viewer
        """
        if self.projects is not None:
            self.viewer.project = pavlovia.PavloviaProject(self.projects.iloc[self.projectList.GetFocusedItem()])


class SortDlg(wx.Dialog):
    def __init__(self, parent, size=(200, 300),
                 items=("Stars", "Last edited", "Forks", "Date created", "Name (A-Z)"),
                 selected=(True, True, False, False, False)
                 ):
        wx.Dialog.__init__(self, parent, size=size, title="Sort by...", style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT)
        # Setup sizer
        self.contentBox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # Create rearrange control
        self.ctrls = utils.SortCtrl(self,
                                    items=items,
                                    showSelect=True,
                                    selected=selected)
        self.sizer.Add(self.ctrls, border=6, flag=wx.EXPAND | wx.ALL)
        # Add Okay button
        self.sizer.AddStretchSpacer(1)
        self.OkayBtn = wx.Button(self, id=wx.ID_OK, label="Okay")
        self.contentBox.Add(self.OkayBtn, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        # Bind cancel
        self.Bind(wx.EVT_CLOSE, self.onCancel)

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)


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
