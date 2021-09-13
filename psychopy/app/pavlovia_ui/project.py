#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys
import time
import os
import traceback

from .functions import (setLocalPath, showCommitDialog, logInPavlovia,
                        noGitWarning)
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy import logging

from psychopy.app.pavlovia_ui import sync

import wx
from wx.lib import scrolledpanel as scrlpanel

from .. import utils

try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl  # <3.0.2

_starred = u"\u2605"
_unstarred = u"\u2606"

class ProjectEditor(wx.Dialog):
    def __init__(self, parent=None, id=wx.ID_ANY, project=None, localRoot="",
                 *args, **kwargs):

        wx.Dialog.__init__(self, parent, id,
                           *args, **kwargs)
        panel = wx.Panel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        # when a project is successfully created these will be populated
        if hasattr(parent, 'filename'):
            self.filename = parent.filename
        else:
            self.filename = None
        self.project = project  # type: pavlovia.PavloviaProject
        self.projInfo = None
        self.parent = parent

        if project:
            # edit existing project
            self.isNew = False
            if project.localRoot and not localRoot:
                localRoot = project.localRoot
        else:
            self.isNew = True

        # create the controls
        nameLabel = wx.StaticText(panel, -1, _translate("Name:"))
        self.nameBox = wx.TextCtrl(panel, -1, size=(400, -1))
        # Path can contain only letters, digits, '_', '-' and '.'.
        # Cannot start with '-', end in '.git' or end in '.atom']
        pavSession = pavlovia.getCurrentSession()

        try:
            username = pavSession.user.username
        except AttributeError as e:
            raise pavlovia.NoUserError("{}: Tried to create project with no user logged in.".format(e))

        gpChoices = [username]
        gpChoices.extend(pavSession.listUserGroups())
        groupLabel = wx.StaticText(panel, -1, _translate("Group/owner:"))
        self.groupBox = wx.Choice(panel, -1, size=(400, -1),
                                  choices=gpChoices)

        descrLabel = wx.StaticText(panel, -1, _translate("Description:"))
        self.descrBox = wx.TextCtrl(panel, -1, size=(400, 200),
                                    style=wx.TE_MULTILINE | wx.SUNKEN_BORDER)

        localLabel = wx.StaticText(panel, -1, _translate("Local folder:"))
        self.localBox = wx.TextCtrl(panel, -1, size=(400, -1),
                                    value=localRoot)
        self.btnLocalBrowse = wx.Button(panel, wx.ID_ANY, _translate("Browse..."))
        self.btnLocalBrowse.Bind(wx.EVT_BUTTON, self.onBrowseLocal)
        localPathSizer = wx.BoxSizer(wx.HORIZONTAL)
        localPathSizer.Add(self.localBox)
        localPathSizer.Add(self.btnLocalBrowse)

        tagsLabel = wx.StaticText(panel, -1,
                                  _translate("Tags (comma separated):"))
        self.tagsBox = wx.TextCtrl(panel, -1, size=(400, 100),
                                   value="PsychoPy, Builder, Coder",
                                   style=wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        publicLabel = wx.StaticText(panel, -1, _translate("Public:"))
        self.publicBox = wx.CheckBox(panel, -1)

        # buttons
        if self.isNew:
            buttonMsg = _translate("Create project on Pavlovia")
        else:
            buttonMsg = _translate("Submit changes to Pavlovia")
        updateBtn = wx.Button(panel, -1, buttonMsg)
        updateBtn.Bind(wx.EVT_BUTTON, self.submitChanges)
        cancelBtn = wx.Button(panel, -1, _translate("Cancel"))
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == "win32":
            btns = [updateBtn, cancelBtn]
        else:
            btns = [cancelBtn, updateBtn]
        btnSizer.AddMany(btns)

        # do layout
        fieldsSizer = wx.FlexGridSizer(cols=2, rows=6, vgap=5, hgap=5)
        fieldsSizer.AddMany([(nameLabel, 0, wx.ALIGN_RIGHT), self.nameBox,
                             (groupLabel, 0, wx.ALIGN_RIGHT), self.groupBox,
                             (localLabel, 0, wx.ALIGN_RIGHT), localPathSizer,
                             (descrLabel, 0, wx.ALIGN_RIGHT), self.descrBox,
                             (tagsLabel, 0, wx.ALIGN_RIGHT), self.tagsBox,
                             (publicLabel, 0, wx.ALIGN_RIGHT), self.publicBox])

        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(fieldsSizer, 0, wx.ALL, 5)
        border.Add(btnSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        panel.SetSizerAndFit(border)
        self.Fit()

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)

    def submitChanges(self, evt=None):
        session = pavlovia.getCurrentSession()
        if not session.user:
            user = logInPavlovia(parent=self.parent)
        if not session.user:
            return
        # get current values
        name = self.nameBox.GetValue()
        namespace = self.groupBox.GetStringSelection()
        descr = self.descrBox.GetValue()
        visibility = self.publicBox.GetValue()
        # tags need splitting and then
        tagsList = self.tagsBox.GetValue().split(',')
        tags = [thisTag.strip() for thisTag in tagsList]
        localRoot = self.localBox.GetValue()
        if not localRoot:
            localRoot = setLocalPath(self.parent, project=None, path="")

        # then create/update
        if self.isNew:
            project = session.createProject(name=name,
                                            description=descr,
                                            tags=tags,
                                            visibility=visibility,
                                            localRoot=localRoot,
                                            namespace=namespace)
            self.project = project
            self.project._newRemote = True
        else:  # we're changing metadata of an existing project. Don't sync
            self.project.pavlovia.name = name
            self.project.pavlovia.description = descr
            self.project.tags = tags
            self.project.visibility = visibility
            self.project.localRoot = localRoot
            self.project.save()  # pushes changed metadata to gitlab
            self.project._newRemote = False

        self.EndModal(wx.ID_OK)
        pavlovia.knownProjects.save()
        self.project.getRepo(forceRefresh=True)
        self.parent.project = self.project

    def onBrowseLocal(self, evt=None):
        newPath = setLocalPath(self, path=self.filename)
        if newPath:
            self.localBox.SetLabel(newPath)
            self.Layout()
            if self.project:
                self.project.localRoot = newPath
        self.Raise()


class DetailsPanel(wx.Panel):

    class StarBtn(wx.Button):
        def __init__(self, parent, iconCache, value=False):
            wx.Button.__init__(self, parent, label=_translate("Star"), style=wx.BORDER_NONE)
            # Setup icons
            self.icons = {
                True: iconCache.getBitmap(name="starred", size=16),
                False: iconCache.getBitmap(name="unstarred", size=16),
            }
            self.SetBitmapDisabled(self.icons[False])  # Always appear empty when disabled
            # Set start value
            self.value = value

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            # Store value
            self._value = bool(value)
            # Change icon
            self.SetBitmap(self.icons[self._value])
            self.SetBitmapCurrent(self.icons[self._value])
            self.SetBitmapFocus(self.icons[self._value])

        def toggle(self):
            print(self.value, not self.value)
            self.value = (not self.value)


    def __init__(self, parent, project=None,
                 size=(600, 500),
                 style=wx.NO_BORDER):

        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style)
        self.SetBackgroundColour("white")
        iconCache = parent.app.iconCache
        # Setup sizer
        self.contentBox = wx.BoxSizer()
        self.SetSizer(self.contentBox)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.contentBox.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)
        # Head sizer
        self.headSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headSizer, border=0, flag=wx.EXPAND)
        # Icon
        self.icon = utils.ImageCtrl(self, bitmap=wx.Bitmap(), size=(128, 128))
        self.icon.SetBackgroundColour("#f2f2f2")
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL)
        # Title sizer
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, flag=wx.EXPAND)
        # Title
        self.title = wx.TextCtrl(self, size=(-1, -1), value="")
        self.title.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.titleSizer.Add(self.title, border=6, flag=wx.ALL | wx.EXPAND)
        # Author
        self.author = wx.StaticText(self, size=(-1, -1), label="by ---")
        self.titleSizer.Add(self.author, border=6, flag=wx.LEFT | wx.RIGHT)
        # Pavlovia link
        self.link = wxhl.HyperLinkCtrl(self, -1,
                                       label="https://pavlovia.org/",
                                       URL="https://pavlovia.org/",
                                       )
        self.link.SetBackgroundColour("white")
        self.titleSizer.Add(self.link, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM)
        # Button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.Add(self.btnSizer, flag=wx.EXPAND)
        # Star button
        self.starLbl = wx.StaticText(self, label="-")
        self.btnSizer.Add(self.starLbl, border=6, flag=wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        self.starBtn = self.StarBtn(self, iconCache=iconCache)
        self.starBtn.Bind(wx.EVT_BUTTON, self.star)
        self.btnSizer.Add(self.starBtn, border=6, flag=wx.ALL | wx.EXPAND)
        # Sync button
        self.syncBtn = wx.Button(self, label=_translate("Sync"), style=wx.BORDER_NONE)
        self.syncBtn.SetBitmap(iconCache.getBitmap(name="view-refresh", size=16))
        self.syncBtn.Bind(wx.EVT_BUTTON, self.sync)
        self.btnSizer.Add(self.syncBtn, border=6, flag=wx.ALL | wx.EXPAND)
        self.btnSizer.AddStretchSpacer(1)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Local root
        self.rootSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.rootSizer, flag=wx.EXPAND)
        self.localRootLabel = wx.StaticText(self, label="Local root:")
        self.rootSizer.Add(self.localRootLabel, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP)
        self.localRoot = utils.FileCtrl(self, dlgtype="dir")
        self.localRoot.Bind(wx.EVT_TEXT, self.setLocalRoot)
        self.rootSizer.Add(self.localRoot, proportion=1, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Description
        self.description = wx.TextCtrl(self, size=(-1, -1), value="", style=wx.TE_MULTILINE)
        self.sizer.Add(self.description, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Visibility
        self.visSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.visSizer, flag=wx.EXPAND)
        self.visLbl = wx.StaticText(self, label=_translate("Visibility:"))
        self.visSizer.Add(self.visLbl, border=6, flag=wx.EXPAND | wx.ALL)
        self.visibility = wx.Choice(self, choices=["Private", "Public"])
        self.visSizer.Add(self.visibility, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # Status
        self.statusSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.statusSizer, flag=wx.EXPAND)
        self.statusLbl = wx.StaticText(self, label=_translate("Status:"))
        self.statusSizer.Add(self.statusLbl, border=6, flag=wx.EXPAND | wx.ALL)
        self.status = wx.Choice(self, choices=["Running", "Piloting", "Inactive"])
        self.statusSizer.Add(self.status, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # Tags
        self.tagSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.tagSizer, flag=wx.EXPAND)
        self.tagLbl = wx.StaticText(self, label=_translate("Tags:"))
        self.tagSizer.Add(self.tagLbl, border=6, flag=wx.EXPAND | wx.ALL)
        self.tags = utils.ButtonArray(self, orient=wx.HORIZONTAL, items=[])
        self.tagSizer.Add(self.tags, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # Populate
        self.project = project

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, project):
        self._project = project

        # Populate fields
        if project is None:
            # Icon
            self.icon.SetBitmap(wx.Bitmap())
            self.icon.Disable()
            # Title
            self.title.SetValue("")
            self.title.Disable()
            # Author
            self.author.SetLabel("by ---")
            self.author.Disable()
            # Link
            self.link.SetLabel("https://pavlovia.org/")
            self.link.Disable()
            # Star button
            self.starBtn.Disable()
            self.starLbl.SetLabel("-")
            self.starLbl.Disable()
            # Sync button
            self.syncBtn.Disable()
            # Local root
            self.localRootLabel.Disable()
            self.localRoot.SetValue("")
            self.localRoot.Disable()
            # Description
            self.description.SetValue("")
            self.description.Disable()
            # Visibility
            self.visibility.SetSelection(wx.NOT_FOUND)
            self.visibility.Disable()
            # Status
            self.status.SetSelection(wx.NOT_FOUND)
            self.status.Disable()
            # Tags
            self.tags.clear()
            self.tags.Disable()
        else:
            # Icon
            self.icon.SetBitmap(project['icon'])
            self.icon.Enable()
            # Title
            self.title.SetValue(project['name'])
            self.title.Enable()
            # Author
            self.author.SetLabel("by %(group)s" % project)
            self.author.Enable()
            # Link
            self.link.SetLabel(project['remoteHTTPS'])
            self.link.Enable()
            # Star button
            self.starBtn.value = bool(project['starred'])
            self.starBtn.Enable()
            self.starLbl.SetLabel(str(project['stars']))
            self.starLbl.Enable()
            # Sync button
            self.syncBtn.Enable()
            # Local root
            self.localRootLabel.Enable(bool(project.localRoot))
            self.localRoot.SetValue(project.localRoot)
            self.localRoot.Enable(bool(project.localRoot))
            # Description
            self.description.SetValue(project['desc'])
            self.description.Enable()
            # Visibility
            self.visibility.SetStringSelection(project['visibility'])
            self.visibility.Enable()
            # Status
            self.status.SetStringSelection(project['status'])
            self.status.Enable()
            # Tags
            self.tags.items = project['tags']
            self.tags.Enable()

    def sync(self, evt=None):
        # If not synced locally, choose a folder
        if not self.localRoot.GetValue():
            self.localRoot.browse()
        # If cancelled, return
        if not self.localRoot.GetValue():
            return
        else:
            self.localRoot.Enable()
        # Do sync (todo:)

    def star(self, evt=None):
        self.starBtn.toggle()
        # Star/unstar project online (todo:)
        # Refresh stars count (todo:)

    def setLocalRoot(self, evt=None):
        # Set local root for this project
        if self.project:
            self.project.localRoot = self.localRoot.GetValue()


class ProjectFrame(wx.Dialog):

    def __init__(self, app, parent=None, style=None,
                 pos=wx.DefaultPosition, project=None):
        if style is None:
            style = (wx.DEFAULT_DIALOG_STYLE | wx.CENTER |
                     wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        if project:
            title = project.title
        else:
            title = _translate("Project info")
        self.frameType = 'ProjectInfo'
        wx.Dialog.__init__(self, parent, -1, title=title, style=style,
                           size=(700, 500), pos=pos)
        self.app = app
        self.project = project
        self.parent = parent

        self.detailsPanel = DetailsPanel(parent=self, project=self.project)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.detailsPanel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(self.mainSizer)

        if self.parent:
            self.CenterOnParent()
        self.Layout()

def syncProject(parent, project=None, closeFrameWhenDone=False):
    """A function to sync the current project (if there is one)

    Returns
    -----------
        1 for success
        0 for fail
        -1 for cancel at some point in the process
    """
    if not pavlovia.haveGit:
        noGitWarning(parent)
        return 0

    isCoder = hasattr(parent, 'currentDoc')

    # Test and reject sync from invalid folders
    if isCoder:
        currentPath = os.path.dirname(parent.currentDoc.filename)
    else:
        currentPath = os.path.dirname(parent.filename)

    currentPath = os.path.normcase(os.path.expanduser(currentPath))
    invalidFolders = [os.path.normcase(os.path.expanduser('~/Desktop')),
                      os.path.normcase(os.path.expanduser('~/My Documents'))]

    if currentPath in invalidFolders:
        wx.MessageBox(("You cannot sync projects from:\n\n"
                      "  - Desktop\n"
                      "  - My Documents\n\n"
                      "Please move your project files to another folder, and try again."),
                      "Project Sync Error",
                      wx.ICON_QUESTION | wx.OK)
        return -1

    if not project and "BuilderFrame" in repr(parent):
        # try getting one from the frame
        project = parent.project  # type: pavlovia.PavloviaProject

    if not project:  # ask the user to create one

        # if we're going to create a project we need user to be logged in
        pavSession = pavlovia.getCurrentSession()
        try:
            username = pavSession.user.username
        except:
            username = logInPavlovia(parent)
        if not username:
            return -1  # never logged in

        # create project dialog
        msg = _translate("This file doesn't belong to any existing project.")
        style = wx.OK | wx.CANCEL | wx.CENTER
        dlg = wx.MessageDialog(parent=parent, message=msg, style=style)
        dlg.SetOKLabel(_translate("Create a project"))
        if dlg.ShowModal() == wx.ID_OK:
            if isCoder:
                if parent.currentDoc:
                    localRoot = os.path.dirname(parent.currentDoc.filename)
                else:
                    localRoot = ''
            else:
                localRoot = os.path.dirname(parent.filename)
            # open the project editor (with no project to create one)
            editor = ProjectEditor(parent=parent, localRoot=localRoot)
            if editor.ShowModal() == wx.ID_OK:
                project = editor.project
            else:
                project = None
        else:
            return -1  # user pressed cancel

    if not project:  # we did our best for them. Give up!
        return 0

    # if project.localRoot doesn't exist, or is empty
    if 'localRoot' not in project or not project.localRoot:
        # we first need to choose a location for the repository
        setLocalPath(parent, project)
        parent.Raise()  # make sure that frame is still visible

    #check that the project does exist remotely
    if not project.pavlovia:
        # project didn't exist at Pavlovia (deleted?)
        recreatorDlg = ProjectRecreator(parent=parent, project=project)
        ok = recreatorDlg.ShowModal()
        if ok > 0:
            project = recreatorDlg.project
        else:
            logging.error("Failed to recreate project to sync with")
            return 0

    # a sync will be necessary so set the target to Runner stdout
    parent.app.showRunner()
    syncFrame = parent.app.runner.stdOut

    if project._newRemote:
        # new remote so this will be a first push
        if project.getRepo(forceRefresh=True) is None:
            # no local repo yet so create one
            project.newRepo(syncFrame)
        # add the local files and commit them
        ok = showCommitDialog(parent=parent, project=project,
                              initMsg="First commit",
                              infoStream=syncFrame)
        if ok == -1:  # cancelled
            syncFrame.Destroy()
            return -1
        syncFrame.setStatus("Pushing files to Pavlovia")
        wx.Yield()
        time.sleep(0.001)
        # git push -u origin master
        try:
            project.firstPush(infoStream=syncFrame)
            project._newRemote = False
        except Exception as e:
            closeFrameWhenDone = False
            syncFrame.statusAppend(traceback.format_exc())
    else:
        # existing remote which we should sync (or clone)
        try:
            ok = project.getRepo(syncFrame)
            if not ok:
                closeFrameWhenDone = False
        except Exception as e:
            closeFrameWhenDone = False
            syncFrame.statusAppend(traceback.format_exc())
        # check for anything to commit before pull/push
        outcome = showCommitDialog(parent, project,
                                   infoStream=syncFrame)
        # 0=nothing to do, 1=OK, -1=cancelled
        if outcome == -1:  # user cancelled
            return -1
        try:
            status = project.sync(syncFrame)
            if status == -1:
                syncFrame.statusAppend("Couldn't sync")
        except Exception:  # not yet sure what errors might occur
            # send the error to panel
            syncFrame.statusAppend(traceback.format_exc())
            return 0

    wx.Yield()
    project._lastKnownSync = time.time()
    if closeFrameWhenDone:
        pass

    return 1


class ForkDlg(wx.Dialog):
    """Simple dialog to help choose the location/name of a forked project"""
    # this dialog is working fine, but the API call to fork to a specific
    # namespace doesn't appear to work
    def __init__(self, project, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)

        existingName = project.name
        session = pavlovia.getCurrentSession()
        groups = [session.user.username]
        groups.extend(session.listUserGroups())
        msg = wx.StaticText(self, label="Where shall we fork to?")
        groupLbl = wx.StaticText(self, label="Group:")
        self.groupField = wx.Choice(self, choices=groups)
        nameLbl = wx.StaticText(self, label="Project name:")
        self.nameField = wx.TextCtrl(self, value=project.name)

        fieldsSizer = wx.FlexGridSizer(cols=2, rows=2, vgap=5, hgap=5)
        fieldsSizer.AddMany([groupLbl, self.groupField,
                             nameLbl, self.nameField])

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(wx.Button(self, id=wx.ID_OK, label="OK"))
        buttonSizer.Add(wx.Button(self, id=wx.ID_CANCEL, label="Cancel"))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(msg, 1, wx.ALL, 5)
        mainSizer.Add(fieldsSizer, 1, wx.ALL, 5)
        mainSizer.Add(buttonSizer, 1, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.SetSizerAndFit(mainSizer)
        self.Layout()


class ProjectRecreator(wx.Dialog):
    """Use this Dlg to handle the case of a missing (deleted?) remote project
    """

    def __init__(self, project, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.project = project
        existingName = project.name
        msgText = _translate("points to a remote that doesn't exist (deleted?).")
        msgText += (" "+_translate("What shall we do?"))
        msg = wx.StaticText(self, label="{} {}".format(existingName, msgText))
        choices = [_translate("(Re)create a project"),
                   "{} ({})".format(_translate("Point to an different location"),
                                    _translate("not yet supported")),
                   _translate("Forget the local git repository (deletes history keeps files)")]
        self.radioCtrl = wx.RadioBox(self, label='RadioBox', choices=choices,
                                     majorDimension=1)
        self.radioCtrl.EnableItem(1, False)
        self.radioCtrl.EnableItem(2, False)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(wx.Button(self, id=wx.ID_OK, label=_translate("OK")),
                      1, wx.ALL, 5)
        buttonSizer.Add(wx.Button(self, id=wx.ID_CANCEL, label=_translate("Cancel")),
                      1, wx.ALL, 5)
        mainSizer.Add(msg, 1, wx.ALL, 5)
        mainSizer.Add(self.radioCtrl, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        mainSizer.Add(buttonSizer, 1, wx.ALL | wx.ALIGN_RIGHT, 1)

        self.SetSizer(mainSizer)
        self.Layout()

    def ShowModal(self):
        if wx.Dialog.ShowModal(self) == wx.ID_OK:
            choice = self.radioCtrl.GetSelection()
            if choice == 0:
                editor = ProjectEditor(parent=self.parent,
                                       localRoot=self.project.localRoot)
                if editor.ShowModal() == wx.ID_OK:
                    self.project = editor.project
                    return 1  # success!
                else:
                    return -1  # user cancelled
            elif choice == 1:
                raise NotImplementedError("We don't yet support redirecting "
                                          "your project to a new location.")
            elif choice == 2:
                raise NotImplementedError("Deleting the local git repo is not "
                                          "yet implemented")
        else:
            return -1
