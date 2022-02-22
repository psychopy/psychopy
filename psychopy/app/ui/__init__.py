#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for graphical user interface elements for the main application.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.lib.agw.aui as aui

# default values
DEFAULT_FRAME_SIZE = wx.Size(800, 600)
DEFAULT_FRAME_TITLE = u"PsychoPy"
# flags for AUI
DEFAULT_AUI_STYLE_FLAGS = aui.AUI_MGR_DEFAULT | aui.AUI_MGR_RECTANGLE_HINT


class BaseAuiFrame(wx.Frame):
    """Base class for AUI managed frames.

    Takes the same same arguments as `wx.Frame`. This frame is AUI managed which
    allows for sub-windows to be attached to it. No application logic should be
    implemented in this class, only its sub-classes.

    """
    def __init__(self,
                 parent,
                 id_=wx.ID_ANY,
                 title=DEFAULT_FRAME_TITLE,
                 pos=wx.DefaultPosition,
                 size=DEFAULT_FRAME_SIZE,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL):
        wx.Frame.__init__(self, parent, id=id_, title=title, pos=pos, size=size,
                          style=style)

        # defaults for window
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        # create the AUI manager and attach it to this window
        self.m_mgr = aui.AuiManager(self, agwFlags=DEFAULT_AUI_STYLE_FLAGS)
        self.m_mgr.Update()

        self.Centre(wx.BOTH)

        # events associated with this window
        self.Bind(aui.EVT_AUI_PANE_ACTIVATED, self.onAuiPaneActivate)
        self.Bind(aui.EVT_AUI_PANE_BUTTON, self.onAuiPaneButton)
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.onAuiPaneClose)
        self.Bind(aui.EVT_AUI_PANE_MAXIMIZE, self.onAuiPaneMaximize)
        self.Bind(aui.EVT_AUI_PANE_RESTORE, self.onAuiPaneRestore)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_IDLE, self.onIdle)

    def __del__(self):
        # called when tearing down the window
        self.m_mgr.UnInit()

    # --------------------------------------------------------------------------
    # Class properties and methods
    #

    @property
    def manager(self):
        """Handle of the AUI manager for this frame (`wx.aui.AuiManager`).
        """
        return self.getAuiManager()

    def getAuiManager(self):
        """Get the AUI manager instance for this window.

        Returns
        -------
        wx.aui.AuiManager
            Handle for the AUI manager instance associated with this window.

        """
        return self.m_mgr

    # --------------------------------------------------------------------------
    # Events for the Coder Frame
    #

    def onAuiPaneActivate(self, event):
        event.Skip()

    def onAuiPaneButton(self, event):
        event.Skip()

    def onAuiPaneClose(self, event):
        event.Skip()

    def onAuiPaneMaximize(self, event):
        event.Skip()

    def onAuiPaneRestore(self, event):
        event.Skip()

    def onClose(self, event):
        event.Skip()

    def onIdle(self, event):
        event.Skip()


if __name__ == "__main__":
    pass
