#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import time
import wx

import git  # will be lazy due to psychopy.__init__


class SyncFrame(wx.Frame):
    def __init__(self, parent, id, project):
        title = "{} / {}".format(project.group, project.title)
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        wx.Frame.__init__(self, parent=None, id=id, style=style,
                          title=title)
        self.parent = parent
        self.project = project

        # create the sync panel and start sync(!)
        self.syncPanel = SyncStatusPanel(parent=self, id=wx.ID_ANY)
        self.progHandler = ProgressHandler(syncPanel=self.syncPanel)
        self.Fit()
        self.Show()
        wx.Yield()


class SyncStatusPanel(wx.Panel):
    def __init__(self, parent, id, *args, **kwargs):
        # init super classes
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        # set self properties
        self.parent = parent
        self.statusMsg = wx.TextCtrl(self, -1, size=(250,150),
                                     value="Synchronising...",
                                     style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.progBar = wx.Gauge(self, -1, range=1, size=(200, -1))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.statusMsg, 1, wx.ALL | wx.CENTER | wx.EXPAND,
                           border=10)
        # self.mainSizer.Add(self.progBar, 1, wx.ALL | wx.CENTER, border=10)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.mainSizer)
        self.Layout()

    def reset(self):
        self.progBar.SetRange(1)
        self.progBar.SetValue(0)

    def setStatus(self, status):
        self.statusMsg.SetValue(status)
        self.Refresh()
        self.Layout()
        wx.Yield()

    def statusAppend(self, newText):
        text = self.statusMsg.GetValue() + newText
        self.setStatus(text)


class ProgressHandler(git.remote.RemoteProgress):
    """We can't override the update() method so we have to create our own
    subclass for this"""

    def __init__(self, syncPanel, *args, **kwargs):
        git.remote.RemoteProgress.__init__(self, *args, **kwargs)
        self.syncPanel = syncPanel
        self.frame = syncPanel.parent
        self.t0 = None

    def setStatus(self, msg):
        self.syncPanel.statusMsg.SetLabel(msg)

    def update(self, op_code=0, cur_count=1, max_count=None, message=''):
        """Update the statusMsg and progBar for the syncPanel
        """
        if not self.t0:
            self.t0 = time.time()
        if op_code in ['10', 10]:  # indicates complete
            label = "Successfully synced"
        else:
            label = self._cur_line.split(':')[1]
            # logging.info("{:.5f}: {}"
            #              .format(time.time() - self.t0, self._cur_line))
            label = self._cur_line
        self.setStatus(label)
        try:
            maxCount = int(max_count)
        except:
            maxCount = 1
        try:
            currCount = int(cur_count)
        except:
            currCount = 1

        self.syncPanel.progBar.SetRange(maxCount)
        self.syncPanel.progBar.SetValue(currCount)
        self.syncPanel.Update()
        self.syncPanel.mainSizer.Layout()
        wx.Yield()
        time.sleep(0.001)
