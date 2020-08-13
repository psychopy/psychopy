#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx


class SyncStatusPanel(wx.Panel):
    def __init__(self, parent, id, *args, **kwargs):
        # init super classes
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        # set self properties
        self.parent = parent
        self.infoStream = InfoStream(self, -1, size=(250, 150))
        # self.progBar = wx.Gauge(self, -1, range=1, size=(200, -1))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.infoStream, 1, wx.ALL | wx.CENTER | wx.EXPAND,
                           border=10)
        # self.mainSizer.Add(self.progBar, 1, wx.ALL | wx.CENTER, border=10)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.mainSizer)
        self.Layout()

    def setStatus(self, status):
        self.infoStream.SetValue(status)
        self.Refresh()
        self.Layout()
        wx.Yield()

    def statusAppend(self, newText):
        text = self.infoStream.GetValue() + newText
        self.setStatus(text)


class InfoStream(wx.TextCtrl):
    def __init__(self, parent, id, size,
                 value="Synchronising...",
                 style=wx.TE_READONLY | wx.TE_MULTILINE):
        wx.TextCtrl.__init__(self, parent, id,
                             size=size, value=value, style=style)

    def clear(self):
        self.SetValue("")

    def write(self, text):
        if type(text) == bytes:
            text = text.decode('utf-8')
        self.SetValue(self.GetValue() + text)
        wx.Yield()
