#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
import time
import os

from .sync import SyncFrame
from .functions import setLocalPath, showCommitDialog
from .sync import SyncStatusPanel, ProgressHandler
from psychopy.localization import _translate
from psychopy.projects import pavlovia

import wx
from wx.lib import scrolledpanel as scrlpanel
try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl # <3.0.2

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
        # Cannot start with '-', end in '.git' or end in '.atom'

        descrLabel = wx.StaticText(panel, -1, _translate("Description:"))
        self.descrBox = wx.TextCtrl(panel, -1, size=(400, 200),
                                    style=wx.TE_MULTILINE | wx.SUNKEN_BORDER)

        localLabel = wx.StaticText(panel, -1, _translate("Local folder:"))
        self.localBox = wx.TextCtrl(panel, -1, size=(400, -1),
                                    value=localRoot)
        self.btnLocalBrowse = wx.Button(panel, wx.ID_ANY, "Browse...")
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
        fieldsSizer = wx.FlexGridSizer(cols=2, rows=5, vgap=5, hgap=5)
        fieldsSizer.AddMany([(nameLabel, 0, wx.ALIGN_RIGHT), self.nameBox,
                           (localLabel, 0, wx.ALIGN_RIGHT), localPathSizer,
                           (descrLabel, 0, wx.ALIGN_RIGHT), self.descrBox,
                           (tagsLabel, 0, wx.ALIGN_RIGHT), self.tagsBox,
                           (publicLabel, 0, wx.ALIGN_RIGHT), self.publicBox])

        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(fieldsSizer, 0, wx.ALL, 10)
        border.Add(btnSizer, 0, wx.ALIGN_RIGHT)
        panel.SetSizerAndFit(border)
        self.Fit()

    def onCancel(self, evt=None):
        self.EndModal(wx.ID_CANCEL)

    def submitChanges(self, evt=None):
        session = pavlovia.currentSession
        #get current values
        name = self.nameBox.GetValue()
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
                                            localRoot=localRoot)
            self.project = project
            self.project._newRemote = True
        else:  # we're changing metadata of an existing project. Don't sync
            self.project.pavlovia.name = name
            self.project.pavlovia.description = descr
            self.project.tags = tags
            self.project.visibility=visibility
            self.project.localRoot = localRoot
            self.project.save()  # pushes changed metadata to gitlab
            self.project._newRemote = False

        self.EndModal(wx.ID_OK)
        pavlovia.knownProjects.save()

    def onBrowseLocal(self, evt=None):
        newPath = setLocalPath(self, path=self.filename)
        if newPath:
            self.localBox.SetLabel(newPath)
            self.project.localRoot = newPath
            self.Layout()


class DetailsPanel(scrlpanel.ScrolledPanel):

    def __init__(self, parent, noTitle=False,
                 style=wx.VSCROLL | wx.NO_BORDER):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.app = self.parent.app
        self.project = {}
        self.noTitle = noTitle
        self.localFolder = ''

        # self.syncPanel = SyncStatusPanel(parent=self, id=wx.ID_ANY)
        # self.syncPanel.Hide()

        if not noTitle:
            self.title = wx.StaticText(parent=self, id=-1,
                                       label="", style=wx.ALIGN_CENTER)
            font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            self.title.SetFont(font)

        # if we've synced before we should know the local location
        self.localFolderCtrl = wx.StaticText(
                parent=self, id=wx.ID_ANY,
                label="Local root: ")
        self.browseLocalBtn = wx.Button(parent=self, id=wx.ID_ANY, label="Browse...")
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

        # layout
        # sizers: on the right we have detail
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(wx.StaticText(self, -1, _translate("Project Info")),
                       flag=wx.ALL,
                       border=5)
        if not noTitle:
            self.sizer.Add(self.title, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.sizer.Add(self.url, border=5,
                       flag=wx.ALL | wx.CENTER)
        localFolderSizer = wx.BoxSizer(wx.HORIZONTAL)
        localFolderSizer.Add(self.localFolderCtrl, border=5,
                             flag=wx.ALL | wx.EXPAND),
        localFolderSizer.Add(self.browseLocalBtn, border=5,
                             flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(localFolderSizer, border=5, flag=wx.ALL | wx.EXPAND)

        self.sizer.Add(self.tags, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.visibility, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                       flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.description, border=10, flag=wx.ALL | wx.EXPAND)

        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                       flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.syncButton,
                       flag=wx.ALL | wx.RIGHT, border=5)

        self.SetSizer(self.sizer)
        self.SetupScrolling()
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.onResize)

    def setProject(self, project, localRoot=''):
        if not isinstance(project, pavlovia.PavloviaProject):
            project = pavlovia.currentSession.getProject(project)
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
        self.description.SetLabel(project.attributes['description'])
        if project.visibility in ['public', 'internal']:
            visib = "Public"
        else:
            visib = "Private"
        self.visibility.SetLabel(_translate("Visibility: {}").format(visib))

        # do we have a local location?
        localFolder = project.localRoot
        if not localFolder:
            localFolder = "<not yet synced>"
        self.localFolderCtrl.SetLabel("Local root: {}".format(localFolder))

        # should sync be enabled?
        perms = project.permissions['project_access']
        if type(perms) == dict:
            perms = perms['access_level']
        if (perms is not None) and perms >= pavlovia.permissions['developer']:
            self.syncButton.SetLabel('Sync...')
        else:
            self.syncButton.SetLabel('Fork + sync...')
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
        if hasattr(self.project, 'attributes'):
            self.description.SetLabel(self.project.attributes['description'])
            self.description.Wrap(w - 20)
        # noTitle in some uses of the detailsPanel
        if not self.noTitle and 'name' in self.project:
            self.title.SetLabel(self.project.name)
            self.title.Wrap(w - 20)
        self.Layout()

    def onSyncButton(self, event):
        if self.project is None:
            raise AttributeError("User pressed the sync button with no "
                                 "current project existing.")

        # fork first if needed
        perms = self.project.permissions['project_access']
        if type(perms) == dict:
            perms = perms['access_level']
        if (perms is None) or perms < pavlovia.permissions['developer']:
            # TODO: support forking to another group/namespace?
            fork = self.project.forkTo(username=None)  # logged-in user
            self.setProject(fork.id)

        # if project.localRoot doesn't exist, or is empty
        if 'localRoot' not in self.project or not self.project.localRoot:
            # we first need to choose a location for the repository
            newPath = setLocalPath(self, self.project)
            if newPath:
                self.localFolderCtrl.SetLabel(
                        label="Local root: {}".format(newPath))
            self.project.local = newPath
            self.Layout()

        syncPanel = SyncStatusPanel(parent=self, id=wx.ID_ANY)
        self.sizer.Add(syncPanel, border=5,
                       flag=wx.ALL | wx.RIGHT)
        self.sizer.Layout()
        progHandler = ProgressHandler(syncPanel=syncPanel)
        wx.Yield()
        self.project.sync(syncPanel=syncPanel, progressHandler=progHandler)
        syncPanel.Destroy()
        self.sizer.Layout()

    def onBrowseLocalFolder(self, evt):
        self.localFolder = setLocalPath(self, self.project)
        if self.localFolder:
            self.localFolderCtrl.SetLabel(
                    label="Local root: {}".format(self.localFolder))
        self.Layout()


def syncProject(parent, project=None):
    """A function to sync the current project (if there is one)
    """
    isCoder = hasattr(parent, 'currentDoc')
    if not project and "BuilderFrame" in repr(parent):  # try getting one from the frame
        project = parent.project  # type: pavlovia.PavloviaProject

    if not project:  # ask the user to create one
        msg = ("This file doesn't belong to any existing project.")
        style = wx.OK | wx.CANCEL | wx.CENTER
        dlg = wx.MessageDialog(parent=parent, message=msg, style=style)
        dlg.SetOKLabel("Create a project")
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

    if not project:  # we did our best for them. Give up!
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
    else:
        # existing remote which we should clone
        project.getRepo(syncFrame.syncPanel, syncFrame.progHandler)
        # check for anything to commit before pull/push
        outcome = showCommitDialog(parent, project)
        project.sync(syncFrame.syncPanel, syncFrame.progHandler)

    wx.Yield()
    project._lastKnownSync = time.time()
    syncFrame.Destroy()

    return 1
