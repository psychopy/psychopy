#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import wx

from ._base import PavloviaMiniBrowser, PavloviaCommitDialog
from psychopy.projects import pavlovia  # NB pavlovia will set gitpython path
from psychopy.localization import _translate

try:
    import wx.adv as wxhl  # in wx 4
except ImportError:
    wxhl = wx  # in wx 3.0.2

if pavlovia.haveGit:
    import git


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
        return pavlovia.getCurrentSession().user


def logOutPavlovia(parent, event=None):
    """Opens the built-in browser dialog to login to pavlovia

    Returns
    -------
    None (user closed window without logging on) or a gitlab.User object
    """
    # also log out of gitlab session in python
    pavlovia.logout()
    # create minibrowser so we can logout of the session
    dlg = PavloviaMiniBrowser(parent=parent, logoutOnly=True)
    dlg.logout()
    dlg.Destroy()


def showCommitDialog(parent, project, initMsg="", infoStream=None):
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

    changeInfo = _translate("Changes to commit:\n")
    for categ in ['untracked', 'changed', 'deleted', 'renamed']:
        changes = changeDict[categ]
        if categ == 'untracked':
            categ = 'New'
        if changes:
            changeInfo += _translate("\t{}: {} files\n").format(categ.title(), len(changes))
    
    dlg = PavloviaCommitDialog(parent, id=wx.ID_ANY, title=_translate("Committing changes"), changeInfo=changeInfo)

    retVal = dlg.ShowCommitDlg()
    commitMsg = dlg.getCommitMsg()
    dlg.Destroy()

    if retVal == wx.ID_CANCEL:
        return -1

    project.stageFiles(changeList)  # NB not needed in dulwich
    project.commit(commitMsg)
    return 1

def noGitWarning(parent):
    """Raise a simpler warning dialog that the user needs to install git first"""
    dlg = wx.Dialog(parent=parent, style=wx.ICON_ERROR | wx.OK | wx.STAY_ON_TOP)

    errorBitmap = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX)
    errorBitmapCtrl = wx.StaticBitmap(dlg, -1)
    errorBitmapCtrl.SetBitmap(errorBitmap)

    msg = wx.StaticText(dlg, label=_translate(
            "You need to install git to use Pavlovia projects"))
    link = wxhl.HyperlinkCtrl(dlg, url="https://git-scm.com/")
    OK = wx.Button(dlg, wx.ID_OK, label="OK")
    msgsSizer = wx.BoxSizer(wx.VERTICAL)
    msgsSizer.Add(msg, 1, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, border=5)
    msgsSizer.Add(link, 1, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, border=5)
    msgsAndIcon = wx.BoxSizer(wx.HORIZONTAL)
    msgsAndIcon.Add(errorBitmapCtrl, 0, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)
    msgsAndIcon.Add(msgsSizer, 1, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND,
                    border=5)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add(msgsAndIcon, 0, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)
    mainSizer.Add(OK, 0, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

    dlg.SetSizerAndFit(mainSizer)
    dlg.Layout()
    dlg.ShowModal()
