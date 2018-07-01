#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import os
import time
import wx

from .sync import SyncFrame
from ._base import PavloviaMiniBrowser
from psychopy.projects import pavlovia
from psychopy.localization import _translate

try:
    import wx.adv as wxhl  # in wx 4
except ImportError:
    wxhl = wx  # in wx 3.0.2


def setLocalPath(parent, project=None, path=""):
    """Open a DirDialog and set the project local folder to that specified

    Returns
    ----------

    None for no change and newPath if this has changed from previous
    """
    if path:
        origPath = path
    elif project and 'localRoot' in project:
        origPath = project.localRoot
    else:
        origPath = ""
    # create the dialog
    dlg = wx.DirDialog(
            parent,
            defaultPath=origPath,
            message=_translate(
                    "Choose/create the root location for the synced project"))
    if dlg.ShowModal() == wx.ID_OK:
        newPath = dlg.GetPath()
        if os.path.isfile(newPath):
            newPath = os.path.split(newPath)[0]
        if newPath != origPath:
            if project:
                project.localRoot = newPath
        return newPath


def logInPavlovia(parent, event=None):
    """Opens the built-in browser dialog to login to pavlovia

    Returns
    -------
    None (user closed window without logging on) or a gitlab.User object
    """
    # check known users list
    dlg = PavloviaMiniBrowser(parent=parent, loginOnly=True)
    dlg.ShowModal()  # with loginOnly=True this will EndModal once logged in
    if dlg.tokenInfo:
        token = dlg.tokenInfo['token']
        pavlovia.login(token, rememberMe=True)  # log in to the current pavlovia session
        return pavlovia.currentSession.user


def syncPavlovia(parent, project=None):
    """A function to sync the current project (if there is one)
    """
    if not project:  # try getting one from the frame
        project = parent.project  # type: pavlovia.PavloviaProject

    if not project:  # ask the user to create one
        msg = ("This file doesn't belong to any existing project.")
        style = wx.OK | wx.CANCEL | wx.CENTER
        dlg = wx.MessageDialog(parent=parent, message=msg, style=style)
        dlg.SetOKLabel("Create a project")
        if dlg.ShowModal()==wx.ID_OK:
            # open the project editor (with no project to create one)
            editor = ProjectEditor(parent=parent)
            if editor.ShowModal() == wx.ID_OK:
                project = editor.project
            else:
                project = None

    if not project: # we did our best for them. Give up!
        return 0

    # if project.localRoot doesn't exist, or is empty
    if 'localRoot' not in project or not project.localRoot:
        # we first need to choose a location for the repository
        setLocalPath(parent, project)
    # a sync will be necessary so can create syncFrame
    syncFrame = SyncFrame(parent=parent, id=wx.ID_ANY, project=project)

    if project._newRemote:
        # new remote, with local files, so init, add, push
        project.newRepo(syncFrame.progHandler)
        # add the local files and commit them
        showCommitDialog(parent=parent, project=project,
                         initMsg="First commit")
        syncFrame.syncPanel.setStatus("Pushing files to Pavlovia")
        wx.Yield()
        time.sleep(0.001)
        # git push -u origin master
        project.firstPush()
    elif not project.repo:
        # existing remote which we should clone
        project.getRepo(syncFrame.syncPanel, syncFrame.progHandler)

        # check for anything to commit before pull/push
        outcome = showCommitDialog(parent, project)
        project.sync(syncFrame.syncPanel, syncFrame.progHandler)

    wx.Yield()
    project._lastKnownSync = time.time()
    syncFrame.Destroy()

    return 1

def showCommitDialog(parent, project, initMsg=""):
    """Brings up a commit dialog (if there is anything to commit

    Returns
    -------
    0 nothing to commit
    1 successful commit
    -1 user cancelled
    """
    changeDict, changeList = project.getChanges()
    # if changeList is empty then nothing to do
    if not changeList:
        return 0

    infoStr="Changes to commit:\n"
    for categ in ['untracked', 'changed', 'deleted', 'renamed']:
        changes = changeDict[categ]
        if categ == 'untracked':
            categ = 'New'
        if changes:
            infoStr += "\t{}: {} files\n".format(categ.title(), len(changes))
    
    dlg = wx.Dialog(parent, id=wx.ID_ANY, title="Committing changes")
    
    updatesInfo = wx.StaticText(dlg, label=infoStr)
    
    commitTitleLbl = wx.StaticText(dlg, label='Summary of changes')
    commitTitleCtrl = wx.TextCtrl(dlg, size=(500, -1), value=initMsg)
    commitTitleCtrl.SetToolTip(wx.ToolTip(_translate(
        "A title summarizing the changes you're making in these files"
        )))
    commitDescrLbl = wx.StaticText(dlg, label='Details of changes\n (optional)')
    commitDescrCtrl = wx.TextCtrl(dlg, size=(500, 200),
                                  style=wx.TE_MULTILINE | wx.TE_AUTO_URL)
    commitDescrCtrl.SetToolTip(wx.ToolTip(_translate(
        "Optional further details about the changes you're making in these files"
        )))
    commitSizer = wx.FlexGridSizer(cols=2, rows=2, vgap=5, hgap=5)
    commitSizer.AddMany([(commitTitleLbl, 0, wx.ALIGN_RIGHT),
                       commitTitleCtrl,
                       (commitDescrLbl, 0, wx.ALIGN_RIGHT),
                       commitDescrCtrl
                       ])

    btnOK  = wx.Button(dlg, wx.ID_OK)
    btnCancel  = wx.Button(dlg, wx.ID_CANCEL)
    buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    buttonSizer.AddMany([btnCancel, btnOK])

    # main sizer and layout
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add(updatesInfo, 0, wx.ALL, border=5)
    mainSizer.Add(commitSizer, 1, wx.ALL | wx.EXPAND, border=5)
    mainSizer.Add(buttonSizer, 0, wx.ALL | wx.ALIGN_RIGHT, border=5)
    dlg.SetSizerAndFit(mainSizer)
    dlg.Layout()
    if dlg.ShowModal() == wx.ID_CANCEL:
        return -1

    commitMsg = commitTitleCtrl.GetValue()
    if commitDescrCtrl.GetValue():
        commitMsg += "\n\n{}".format(commitDescrCtrl.GetValue())
    project.stageFiles(changeList)

    project.commit(commitMsg)
    return 1
