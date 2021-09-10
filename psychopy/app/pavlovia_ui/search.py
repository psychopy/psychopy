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
        self.sizer.Add(self.searchCtrl, border=4, flag=wx.EXPAND | wx.ALL)
        # Add sort / filter buttons
        self.filterCtrls = wx.BoxSizer(wx.HORIZONTAL)
        self.filterCtrls.AddStretchSpacer(1)
        self.sortBtn = wx.Button(self, label=_translate("Sort..."), style=wx.BORDER_NONE)
        self.filterCtrls.Add(self.sortBtn, border=6, flag=wx.LEFT | wx.RIGHT)
        self.filterBtn = wx.Button(self, label=_translate("Filter..."), style=wx.BORDER_NONE)
        self.filterCtrls.Add(self.filterBtn, border=6, flag=wx.LEFT | wx.RIGHT)
        self.sizer.Add(self.filterCtrls, border=4, flag=wx.EXPAND | wx.ALL)
        # Add project list
        self.projectList = ListCtrl(self, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.sizer.Add(self.projectList, proportion=1, border=4, flag=wx.EXPAND | wx.ALL)
        # Setup project list
        #self.projectList.InsertColumn(0, '', width=32, format=wx.LIST_FORMAT_CENTER)  # Icon
        self.projectList.InsertColumn(0, _starred, width=24, format=wx.LIST_FORMAT_CENTER)  # Stars
        self.projectList.InsertColumn(1, _translate('Author'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Author
        self.projectList.InsertColumn(2, _translate('Name'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT)  # Name
        self.projectList.InsertColumn(3, _translate('Description'), width=wx.LIST_AUTOSIZE, format=wx.LIST_FORMAT_LEFT | wx.EXPAND)  # Description
        # Setup list to store icons
        #self.icons = wx.ImageList(width=16, height=16)
        #self.projectList.SetImageList(self.icons, wx.IMAGE_LIST_SMALL)

        # Make example item (delete once working)
        #_bmp = self.icons.Add(wx.Bitmap("E:\\My Drive\\My Pavlovia Demos\\pizza\\icon_small.jpg"))
        i = self.projectList.Append([
        #    '',
            1,
            "Demos",
            "Pizza Calculator",
            "This demo helps you work out whether to get a slice of a big pizza or a whole small pizza... Very important science, obviously. Use the sliders on the right to specify the size (diameter in inches) of the big pizza and how much of it you'd be getting. The slider on the left shows you how much pizza you're actually getting, relative to standard pizza sizes (e.g. Small 10\", Medium 12\", Large 14\", etc.) so that you can choose whichever option gives you the most pizza for your money."
        ])
        #self.projectList.GetItem(i).SetImage(_bmp)
        # Make example item (delete once working)
        #_bmp = self.icons.Add(wx.Bitmap("E:\\My Drive\\My Pavlovia Demos\\pizza\\icon_small.jpg"))
        i = self.projectList.Append([
        #    '',
            0,
            "TPronk",
            "Pizza Calculator",
            "This demo helps you work out whether to get a slice of a big pizza or a whole small pizza... Very important science, obviously. Use the sliders on the right to specify the size (diameter in inches) of the big pizza and how much of it you'd be getting. The slider on the left shows you how much pizza you're actually getting, relative to standard pizza sizes (e.g. Small 10\", Medium 12\", Large 14\", etc.) so that you can choose whichever option gives you the most pizza for your money."
        ])
        #self.projectList.GetItem(i).SetImage(_bmp)

        # Link ProjectViewer
        self.viewer = viewer
        self.projectList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.viewProject)
        # Layout
        self.Layout()

    def viewProject(self, evt=None):
        """
        View current project in associated viewer
        """
        return


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
