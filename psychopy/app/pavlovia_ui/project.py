#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
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

try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl  # <3.0.2


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
        self.project = project  # type: PavloviaProject
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
        btnSizer.AddMany([updateBtn, cancelBtn])

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


class DetailsPanel(scrlpanel.ScrolledPanel):

    def __init__(self, parent, noTitle=False,
                 style=wx.VSCROLL | wx.NO_BORDER,
                 project={}):

        scrlpanel.ScrolledPanel.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.project = project  # type: PavloviaProject
        self.noTitle = noTitle
        self.localFolder = ''
        self.syncPanel = None

        if not noTitle:
            self.title = wx.StaticText(parent=self, id=-1,
                                       label="", style=wx.ALIGN_CENTER)
            font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            self.title.SetFont(font)

        # if we've synced before we should know the local location
        self.localFolderCtrl = wx.StaticText(
            parent=self, id=wx.ID_ANY,
            label=_translate("Local root: "))
        self.browseLocalBtn = wx.Button(parent=self, id=wx.ID_ANY,
                                        label=_translate("Browse..."))
        self.browseLocalBtn.Bind(wx.EVT_BUTTON, self.onBrowseLocalFolder)

        # remote attributes
        self.url = wxhl.HyperLinkCtrl(parent=self, id=-1,
                                      label="https://pavlovia.org",
                                      URL="https://pavlovia.org",
                                      )
        self.description = wx.StaticText(parent=self, id=-1,
                                         label=_translate(
                                             "Select a project for details"))
        self.tags = wx.StaticText(parent=self, id=-1,
                                  label="")
        self.visibility = wx.StaticText(parent=self, id=-1,
                                        label="")

        self.syncButton = wx.Button(self, -1, _translate("Sync..."))
        self.syncButton.Enable(False)
        self.syncButton.Bind(wx.EVT_BUTTON, self.onSyncButton)
        self.syncPanel = sync.SyncStatusPanel(parent=self, id=wx.ID_ANY)

        # layout
        # sizers: on the right we have detail
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        # self.sizer.Add(wx.StaticText(self, -1, _translate("Project Info")),
        #                flag=wx.ALL,
        #                border=5)
        if not noTitle:
            self.sizer.Add(self.title, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.sizer.Add(self.url, border=5,
                       flag=wx.ALL | wx.ALIGN_CENTER)
        self.sizer.Add(self.localFolderCtrl, border=5,
                             flag=wx.ALL | wx.EXPAND),
        self.sizer.Add(self.browseLocalBtn, border=5,
                             flag=wx.ALL | wx.ALIGN_LEFT)
        self.sizer.Add(self.tags, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.visibility, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                       flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.description, border=10, flag=wx.ALL | wx.EXPAND)

        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                       flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.syncButton,
                       flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        self.sizer.Add(self.syncPanel, border=5, proportion=1,
                       flag=wx.ALL | wx.RIGHT | wx.EXPAND)

        if self.project:
            self.setProject(self.project)
            self.syncPanel.setStatus(_translate("Ready to sync"))
        else:
            self.syncPanel.setStatus(
                    _translate("This file doesn't belong to a project yet"))

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.sizer)
        self.SetupScrolling()
        self.Bind(wx.EVT_SIZE, self.onResize)


    def setProject(self, project, localRoot=''):
        if not isinstance(project, pavlovia.PavloviaProject):
            project = pavlovia.getCurrentSession().getProject(project)
        if project is None:
            return  # we're done
        self.project = project

        if not self.noTitle:
            # use the id (namespace/name) but give space around /
            self.title.SetLabel(project.id.replace("/", " / "))

        # url
        self.url.SetLabel(self.project.web_url)
        self.url.SetURL(self.project.web_url)

        # public / private
        if hasattr(project.attributes, 'description') and project.attributes['description']:
            self.description.SetLabel(project.attributes['description'])
        else:
            self.description.SetLabel('')
        if not hasattr(project, 'visibility'):
            visib = _translate("User not logged in!")
        elif project.visibility in ['public', 'internal']:
            visib = "Public"
        else:
            visib = "Private"
        self.visibility.SetLabel(_translate("Visibility: {}").format(visib))

        # do we have a local location?
        localFolder = project.localRoot
        if not localFolder:
            localFolder = _translate("<not yet synced>")
        self.localFolderCtrl.SetLabel(_translate("Local root: {}").format(localFolder))

        # Check permissions: login, fork or sync
        perms = project.permissions

        # we've got the permissions value so use it
        if not pavlovia.getCurrentSession().user:
            self.syncButton.SetLabel(_translate('Log in to sync...'))
        elif not perms or perms < pavlovia.permissions['developer']:
            self.syncButton.SetLabel(_translate('Fork + sync...'))
        else:
            self.syncButton.SetLabel(_translate('Sync...'))
        self.syncButton.Enable(True)  # now we have a project we should enable

        while None in project.tags:
            project.tags.remove(None)
        self.tags.SetLabel(_translate("Tags:") + " " + ", ".join(project.tags))
        # call onResize to get correct wrapping of description box and title
        self.onResize()

    def onResize(self, evt=None):
        if self.project is None:
            return
        w, h = self.GetSize()
        # if it hasn't been created yet then we won't have attributes
        if hasattr(self.project, 'attributes') and self.project.attributes['description'] is not None:
                self.description.SetLabel(self.project.attributes['description'])
                self.description.Wrap(w - 20)
        # noTitle in some uses of the detailsPanel
        if not self.noTitle and 'name' in self.project:
            self.title.SetLabel(self.project.name)
            self.title.Wrap(w - 20)
        self.Layout()

    def onSyncButton(self, event):
        if not pavlovia.haveGit:
            noGitWarning(parent=self.parent)
            return 0

        if self.project is None:
            raise AttributeError("User pressed the sync button with no "
                                 "current project existing.")

        # log in first if needed
        if not pavlovia.getCurrentSession().user:
            logInPavlovia(parent=self.parent)
            return

        # fork first if needed
        perms = self.project.permissions
        if not perms or perms < pavlovia.permissions['developer']:
            # specifying the group to fork to has no effect so don't use it
            # dlg = ForkDlg(parent=self.parent, project=self.project)
            # if dlg.ShowModal() == wx.ID_CANCEL:
            #     return
            # else:
            #     newGp = dlg.groupField.GetStringSelection()
            #     newName = dlg.nameField.GetValue()
            fork = self.project.forkTo()  # logged-in user
            self.setProject(fork.id)

        # if project.localRoot doesn't exist, or is empty
        if 'localRoot' not in self.project or not self.project.localRoot:
            # we first need to choose a location for the repository
            newPath = setLocalPath(self, self.project)
            if newPath:
                self.localFolderCtrl.SetLabel(
                    label=_translate("Local root: {}").format(newPath))
            self.project.local = newPath
            self.Layout()
            self.Raise()

        self.syncPanel.setStatus(_translate("Synchronizing..."))
        self.project.sync(infoStream=self.syncPanel.infoStream)
        self.parent.Raise()

    def onBrowseLocalFolder(self, evt):
        self.localFolder = setLocalPath(self, self.project)
        if self.localFolder:
            self.localFolderCtrl.SetLabel(
                label=_translate("Local root: {}").format(self.localFolder))
        self.localFolderCtrl.Wrap(self.GetSize().width)
        self.Layout()
        self.parent.Raise()



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

        # on the right
        self.detailsPanel = DetailsPanel(parent=self, project=self.project)
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
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
            return

    # a sync will be necessary so can create syncFrame
    syncFrame = sync.SyncFrame(parent=parent, id=wx.ID_ANY, project=project)

    if project._newRemote:
        # new remote so this will be a first push
        if project.getRepo(forceRefresh=True) is None:
            # no local repo yet so create one
            project.newRepo(syncFrame)
        # add the local files and commit them
        ok = showCommitDialog(parent=parent, project=project,
                              initMsg="First commit",
                              infoStream=syncFrame.syncPanel.infoStream)
        if ok == -1:  # cancelled
            syncFrame.Destroy()
            return -1
        syncFrame.syncPanel.setStatus("Pushing files to Pavlovia")
        wx.Yield()
        time.sleep(0.001)
        # git push -u origin master
        try:
            project.firstPush(infoStream=syncFrame.syncPanel.infoStream)
            project._newRemote = False
        except Exception as e:
            closeFrameWhenDone = False
            syncFrame.syncPanel.statusAppend(traceback.format_exc())
    else:
        # existing remote which we should sync (or clone)
        try:
            ok = project.getRepo(syncFrame.syncPanel.infoStream)
            if not ok:
                closeFrameWhenDone = False
        except Exception as e:
            closeFrameWhenDone = False
            syncFrame.syncPanel.statusAppend(traceback.format_exc())
        # check for anything to commit before pull/push
        outcome = showCommitDialog(parent, project,
                                   infoStream=syncFrame.syncPanel.infoStream)
        # 0=nothing to do, 1=OK, -1=cancelled
        if outcome == -1:  # user cancelled
            syncFrame.Destroy()
            return -1
        try:
            status = project.sync(syncFrame.syncPanel.infoStream)
            if status == -1:
                syncFrame.syncPanel.statusAppend("Couldn't sync")
        except Exception:  # not yet sure what errors might occur
            # send the
            closeFrameWhenDone = False
            syncFrame.syncPanel.statusAppend(traceback.format_exc())

    wx.Yield()
    project._lastKnownSync = time.time()
    if closeFrameWhenDone:
        syncFrame.Destroy()

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
                      1, wx.ALL | wx.ALIGN_RIGHT, 5)
        buttonSizer.Add(wx.Button(self, id=wx.ID_CANCEL, label=_translate("Cancel")),
                      1, wx.ALL | wx.ALIGN_RIGHT, 5)
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
