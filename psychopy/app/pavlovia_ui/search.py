#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
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
from ..themes import icons

_starred = u"\u2605"
_unstarred = u"\u2606"
_fork = u"\u2442"


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
        self.SetMinSize((980, 520))
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
    class FilterLabel(wx.StaticText):
        """
        A label to show what filters and sorting are applied to the current search
        """
        def update(self):
            # Get parent object
            parent = self.GetParent()
            # Add me mode
            mineLbl = ""
            if parent._mine:
                mineLbl += "Editable by me. "
            # Add sort params
            sortLbl = ""
            if len(parent.sortOrder):
                sortLbl += "Sort by: "
                sortLbl += " then ".join([item.label.lower() for item in parent.sortOrder])
                sortLbl += ". "
            # Add filter params
            filterLbl = ""
            for key, values in parent.filterTerms.items():
                if values:
                    if isinstance(values, str):
                        values = [values]
                    filterLbl += f"{key}: "
                    filterLbl += " or ".join(values)
                    filterLbl += ". "
            # Construct full label
            label = mineLbl + sortLbl + filterLbl
            # Apply label
            self.SetLabel(label)
            # Show or hide self according to label
            self.Show(bool(label))
            parent.Layout()

        def hoverOn(self, evt=None):
            self.Wrap(self.GetParent().GetSize()[0] - 12)
            self.GetParent().Layout()

        def hoverOff(self, evt=None):
            self.SetLabel(self.GetLabel().replace("\n", " "))
            self.GetParent().Layout()

    def __init__(self, parent, viewer,
                 size=(400, -1),
                 style=wx.NO_BORDER
                 ):
        # Init self
        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style
                          )
        self.session = pavlovia.getCurrentSession()
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
        # Add "me mode" button
        self.mineBtn = wx.ToggleButton(self, size=(64, -1), label=_translate("Me"))
        self.mineBtn.SetBitmap(icons.ButtonIcon(stem="person_off", size=16).bitmap)
        self.mineBtn.SetBitmapFocus(icons.ButtonIcon(stem="person_on", size=16).bitmap)
        self.mineBtn.SetBitmapPressed(icons.ButtonIcon(stem="person_on", size=16).bitmap)
        self._mine = False
        self.mineBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onMineBtn)
        self.mineBtn.Enable(self.session.userID is not None)
        self.btnSizer.Add(self.mineBtn, border=6, flag=wx.EXPAND | wx.RIGHT | wx.TOP | wx.BOTTOM)
        self.btnSizer.AddStretchSpacer(1)
        # Add sort button
        self.sortBtn = wx.Button(self, label=_translate("Sort..."))
        self.sortOrder = []
        self.sortBtn.Bind(wx.EVT_BUTTON, self.sort)
        self.btnSizer.Add(self.sortBtn, border=6, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM)
        # Add filter button
        self.filterBtn = wx.Button(self, label=_translate("Filter..."))
        self.filterTerms = {
            "Status": [],
            "Platform": [],
            "Keywords": [],
        }
        self.filterOptions = {
            "Author": None,
            "Status": ["running", "piloting", "inactive"],
            "Platform": ["psychojs", "jspsych", "labjs", "opensesame", "other"],
            "Visibility": ["public", "private"],
            "Keywords": None,
        }
        self.filterBtn.Bind(wx.EVT_BUTTON, self.filter)
        self.btnSizer.Add(self.filterBtn, border=6, flag=wx.LEFT | wx.TOP | wx.BOTTOM)
        # Add filter label
        self.filterLbl = self.FilterLabel(self, style=wx.ST_ELLIPSIZE_END)
        self.filterLbl.Bind(wx.EVT_ENTER_WINDOW, self.filterLbl.hoverOn)
        self.filterLbl.Bind(wx.EVT_LEAVE_WINDOW, self.filterLbl.hoverOff)
        self.sizer.Add(self.filterLbl, border=6, flag=wx.LEFT | wx.RIGHT)
        self.filterLbl.update()
        # Add project list
        self.projectList = ListCtrl(self, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.projectList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showProject)
        self.sizer.Add(self.projectList, proportion=1, border=4, flag=wx.EXPAND | wx.ALL)
        # Setup project list
        self.projectList.InsertColumn(0, _starred, width=36, format=wx.LIST_FORMAT_CENTER)  # Stars
        #self.projectList.InsertColumn(1, _translate('Status'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Status
        self.projectList.InsertColumn(2, _translate('Author'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Author
        self.projectList.InsertColumn(3, _translate('Name'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Name
        # Setup projects dict
        self.projects = None

        # Link ProjectViewer
        self.viewer = viewer
        self.projectList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.showProject)
        # Layout
        self.Layout()

        # Initial search
        self.search()

    def search(self, evt=None):
        # Get search term
        if evt is None:
            term = self.searchCtrl.GetValue()
        elif isinstance(evt, str):
            term = evt
        else:
            term = evt.GetString()
        # Do search
        self.projects = pavlovia.PavloviaSearch(term=term, filterBy=self.filterTerms, mine=self._mine)

        # Sort values
        if len(self.projects):
            self.projects.sort_values(self.sortOrder)

        # Refresh
        self.refreshCtrl()

    def refreshCtrl(self):
        # Clear list and projects dict
        self.projectList.DeleteAllItems()
        # Skip if not searched yet
        if self.projects is None:
            return
        # Skip if empty search
        if len(self.projects) == 0:
            return
        # Populate list and projects dict
        for i, _ in self.projects.iterrows():
            i = self.projectList.Append([
                self.projects['nbStars'][i],
                #self.projects['status'][i],
                self.projects['pathWithNamespace'][i].split('/')[0],
                self.projects['name'][i],
            ])

    def sort(self, evt=None):
        # Create temporary arrays
        items = copy.deepcopy(self.sortOrder)
        selected = []
        # Append missing items to copy
        for item in pavlovia.PavloviaSearch.sortTerms:
            if item in self.sortOrder:
                selected.append(True)
            else:
                items.append(copy.deepcopy(item))
                selected.append(False)
        # Create dlg
        _dlg = SortDlg(self, items=items, selected=selected)
        if _dlg.ShowModal() != wx.ID_OK:
            return
        # Update sort order
        self.sortOrder = _dlg.ctrls.GetValue()
        # Sort
        if self.projects is not None:
            self.projects.sort_values(self.sortOrder)
        # Refresh
        self.refreshCtrl()
        self.filterLbl.update()

    def filter(self, evt=None):
        # Open filter dlg
        _dlg = FilterDlg(self,
                         terms=self.filterTerms,
                         options=self.filterOptions)
        # Skip if cancelled
        if _dlg.ShowModal() != wx.ID_OK:
            return
        # Update filters if Okayed
        self.filterTerms = _dlg.GetValue()
        # Update filter label
        self.filterLbl.update()
        # Re-search
        self.search()

    def showProject(self, evt=None):
        """
        View current project in associated viewer
        """
        if self.projects is not None:
            proj = self.projects.iloc[self.projectList.GetFocusedItem()]
            # Set project to None while waiting
            self.viewer.project = None
            # Set project
            self.viewer.project = pavlovia.PavloviaProject(proj)

    def onMineBtn(self, evt=None):
        # If triggered manually with a bool, do setting
        if isinstance(evt, bool):
            self.mineBtn.Value = evt
        # Apply "mine" filter
        self._mine = self.mineBtn.Value
        # Clear and disable filters & search todo: This is a stop gap, remove once the Pavlovia API can accept searches and filters WITHIN a designer
        self.filterBtn.Enable(not self._mine)
        self.searchCtrl.Enable(not self._mine)
        if self._mine:
            self.filterTerms = {key: [] for key in self.filterTerms}
            self.searchCtrl.Value = ""
        # Update
        self.filterLbl.update()
        self.search()


class SortDlg(wx.Dialog):
    def __init__(self, parent, size=(200, 400),
                 items=pavlovia.PavloviaSearch.sortTerms,
                 selected=False):
        wx.Dialog.__init__(self, parent, size=size, title="Sort by...", style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT)
        # Setup sizer
        self.contentBox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # Create rearrange control
        self.ctrls = utils.SortCtrl(self,
                                    items=items,
                                    showFlip=True,
                                    showSelect=True, selected=selected)
        self.sizer.Add(self.ctrls, border=6, flag=wx.EXPAND | wx.ALL)
        # Add Okay button
        self.sizer.AddStretchSpacer(1)
        self.OkayBtn = wx.Button(self, id=wx.ID_OK, label="Okay")
        self.contentBox.Add(self.OkayBtn, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        # Bind cancel
        self.Bind(wx.EVT_CLOSE, self.onCancel)

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)


class FilterDlg(wx.Dialog):
    class KeyCtrl(wx.Window):
        def __init__(self, parent,
                     key, value,
                     options=None,
                     selected=True):
            # Init self
            wx.Window.__init__(self, parent, size=(-1, -1))
            self.SetBackgroundColour(parent.GetBackgroundColour())
            # Create master sizer
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)
            # Create title sizer
            self.titleSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer.Add(self.titleSizer, border=0, flag=wx.ALL | wx.EXPAND)
            # Add tickbox
            self.selectCtrl = wx.CheckBox(self)
            self.selectCtrl.Bind(wx.EVT_CHECKBOX, self.onSelect)
            self.selectCtrl.SetValue(selected)
            self.titleSizer.Add(self.selectCtrl, border=6, flag=wx.ALL | wx.EXPAND)
            # Add label
            self.key = key
            self.label = wx.StaticText(self, label=f"{key}:")
            self.titleSizer.Add(self.label, proportion=1, border=6, flag=wx.ALL | wx.EXPAND | wx.TEXT_ALIGNMENT_LEFT)
            # Add ctrl
            if options is None:
                self.ctrl = wx.TextCtrl(self, value=",".join(value))
            else:
                self.ctrl = wx.CheckListBox(self, choices=options)
                self.ctrl.SetCheckedStrings(value)
            self.sizer.Add(self.ctrl, border=6, flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
            # Layout
            self.Layout()
            # Enable
            self.Enable(selected)

        @property
        def selected(self):
            return self.selectCtrl.Value

        @selected.setter
        def selected(self, value):
            self.selectCtrl.Value = value

        def onSelect(self, evt=None):
            self.Enable(self.selected)

        def Enable(self, enable=True):
            # Select button always enabled
            self.selectCtrl.Enable(True)
            # Enable/disable children
            self.label.Enable(enable)
            self.ctrl.Enable(enable)
            if not enable and isinstance(self.ctrl, wx.CheckListBox):
                # If disabled, every option should be checked and none selected
                self.ctrl.SetCheckedStrings(self.ctrl.GetStrings())
                self.ctrl.SetSelection(-1)

        def Disable(self):
            self.Enable(False)

        def GetValue(self):
            # If deselected, return blank
            if not self.selected:
                return []
            # Otherwise, get ctrl value
            if isinstance(self.ctrl, wx.CheckListBox):
                # List of checked strings for check lists
                return self.ctrl.GetCheckedStrings()
            else:
                # String split by commas for text ctrl
                if self.ctrl.GetValue():
                    return self.ctrl.GetValue().split(",")
                else:
                    # Substitute [''] for [] so it's booleanised to False
                    return []

    def __init__(self, parent, size=(250, 400),
                 terms={},
                 options={}):
        wx.Dialog.__init__(self, parent, size=size,
                           title="Filter by...", style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT)
        # Setup sizer
        self.contentBox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # Add dict ctrl
        self.ctrls = {}
        for key in terms:
            self.ctrls[key] = self.KeyCtrl(self, key,
                                           terms[key], selected=bool(terms[key]),
                                           options=options[key])
            self.sizer.Add(self.ctrls[key], border=6, flag=wx.EXPAND | wx.ALL)
        # Add Okay button
        self.sizer.AddStretchSpacer(1)
        self.OkayBtn = wx.Button(self, id=wx.ID_OK, label=_translate("OK"))
        self.contentBox.Add(self.OkayBtn, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        # Bind cancel
        self.Bind(wx.EVT_CLOSE, self.onCancel)

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)

    def GetValue(self):
        # Create blank dict
        value = {}
        # Update dict keys with value from each ctrl
        for key, ctrl in self.ctrls.items():
            value[key] = ctrl.GetValue()

        return value


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
