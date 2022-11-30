#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import io
import sys
import tempfile
import time
import os
import traceback
from pathlib import Path

import gitlab
import requests
from .functions import (setLocalPath, showCommitDialog, logInPavlovia,
                        noGitWarning)
from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy import logging

from psychopy.app.pavlovia_ui import sync, functions

import wx
from wx.lib import scrolledpanel as scrlpanel

from .. import utils
from ..themes import icons
from ...projects.pavlovia import PavloviaProject

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
        def __init__(self, parent, value=False):
            wx.Button.__init__(self, parent, label=_translate("Star"))
            # Setup icons
            self.icons = {
                True: icons.ButtonIcon(stem="starred", size=16).bitmap,
                False: icons.ButtonIcon(stem="unstarred", size=16).bitmap,
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
            self.value = (not self.value)

    def __init__(self, parent, project=None,
                 size=(650, 550),
                 style=wx.NO_BORDER):

        wx.Panel.__init__(self, parent, -1,
                          size=size,
                          style=style)
        self.SetBackgroundColour("white")
        self.parent = parent
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
        self.icon.Bind(wx.EVT_FILEPICKER_CHANGED, self.updateProject)
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL)
        self.icon.SetToolTip(_translate(
            "An image to represent this project, this helps it stand out when browsing on Pavlovia."
        ))
        # Title sizer
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, flag=wx.EXPAND)
        # Title
        self.title = wx.TextCtrl(self,
                                 size=(-1, 30 if sys.platform == 'darwin' else -1),
                                 value="")
        self.title.Bind(wx.EVT_KILL_FOCUS, self.updateProject)
        self.title.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.titleSizer.Add(self.title, border=6, flag=wx.ALL | wx.EXPAND)
        self.title.SetToolTip(_translate(
            "Title of the project. Unlike the project name, this isn't used as a filename anywhere; so you can "
            "add spaces, apostrophes and emojis to your heart's content! 🦕✨"
        ))
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
        self.link.SetToolTip(_translate(
            "Click to view the project in Pavlovia."
        ))
        # Button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.Add(self.btnSizer, flag=wx.EXPAND)
        # Star button
        self.starLbl = wx.StaticText(self, label="-")
        self.btnSizer.Add(self.starLbl, border=6, flag=wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        self.starBtn = self.StarBtn(self)
        self.starBtn.Bind(wx.EVT_BUTTON, self.star)
        self.btnSizer.Add(self.starBtn, border=6, flag=wx.ALL | wx.EXPAND)
        self.starBtn.SetToolTip(_translate(
            "'Star' this project to get back to it easily. Projects you've starred will appear first in your searches "
            "and projects with more stars in total will appear higher in everyone's searches."
        ))
        # Fork button
        self.forkLbl = wx.StaticText(self, label="-")
        self.btnSizer.Add(self.forkLbl, border=6, flag=wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        self.forkBtn = wx.Button(self, label=_translate("Fork"))
        self.forkBtn.SetBitmap(icons.ButtonIcon(stem="fork", size=16).bitmap)
        self.forkBtn.Bind(wx.EVT_BUTTON, self.fork)
        self.btnSizer.Add(self.forkBtn, border=6, flag=wx.ALL | wx.EXPAND)
        self.forkBtn.SetToolTip(_translate(
            "Create a copy of this project on your own Pavlovia account so that you can make changes without affecting "
            "the original project."
        ))
        # Create button
        self.createBtn = wx.Button(self, label=_translate("Create"))
        self.createBtn.SetBitmap(icons.ButtonIcon(stem="plus", size=16).bitmap)
        self.createBtn.Bind(wx.EVT_BUTTON, self.create)
        self.btnSizer.Add(self.createBtn, border=6, flag=wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        self.createBtn.SetToolTip(_translate(
            "Create a Pavlovia project for the current experiment."
        ))
        # Sync button
        self.syncBtn = wx.Button(self, label=_translate("Sync"))
        self.syncBtn.SetBitmap(icons.ButtonIcon(stem="view-refresh", size=16).bitmap)
        self.syncBtn.Bind(wx.EVT_BUTTON, self.sync)
        self.btnSizer.Add(self.syncBtn, border=6, flag=wx.ALL | wx.EXPAND)
        self.syncBtn.SetToolTip(_translate(
            "Synchronise this project's local files with their online counterparts. This will 'pull' changes from "
            "Pavlovia and 'push' changes from your local files."
        ))
        # Get button
        self.downloadBtn = wx.Button(self, label=_translate("Download"))
        self.downloadBtn.SetBitmap(icons.ButtonIcon(stem="download", size=16).bitmap)
        self.downloadBtn.Bind(wx.EVT_BUTTON, self.sync)
        self.btnSizer.Add(self.downloadBtn, border=6, flag=wx.ALL | wx.EXPAND)
        self.downloadBtn.SetToolTip(_translate(
            "'Clone' this project, creating local copies of all its files and tracking any changes you make so that "
            "they can be applied when you next 'sync' the project."
        ))
        # Sync label
        self.syncLbl = wx.StaticText(self, size=(-1, -1), label="---")
        self.btnSizer.Add(self.syncLbl, border=6, flag=wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        self.syncLbl.SetToolTip(_translate(
            "Last synced at..."
        ))
        self.btnSizer.AddStretchSpacer(1)
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Local root
        self.rootSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.rootSizer, flag=wx.EXPAND)
        self.localRootLabel = wx.StaticText(self, label="Local root:")
        self.rootSizer.Add(self.localRootLabel, border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        self.localRoot = utils.FileCtrl(self, dlgtype="dir")
        self.localRoot.Bind(wx.EVT_FILEPICKER_CHANGED, self.updateProject)
        self.rootSizer.Add(self.localRoot, proportion=1, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM)
        self.localRoot.SetToolTip(_translate(
            "Folder in which local files are stored for this project. Changes to files in this folder will be tracked "
            "and applied to the project when you 'sync', so make sure the only files in this folder are relevant!"
        ))
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Description
        self.description = wx.TextCtrl(self, size=(-1, -1), value="", style=wx.TE_MULTILINE)
        self.description.Bind(wx.EVT_KILL_FOCUS, self.updateProject)
        self.sizer.Add(self.description, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.description.SetToolTip(_translate(
            "Description of the project to be shown on Pavlovia. Note: This is different than a README file!"
        ))
        # Sep
        self.sizer.Add(wx.StaticLine(self, -1), border=6, flag=wx.EXPAND | wx.ALL)
        # Visibility
        self.visSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.visSizer, flag=wx.EXPAND)
        self.visLbl = wx.StaticText(self, label=_translate("Visibility:"))
        self.visSizer.Add(self.visLbl, border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        self.visibility = wx.Choice(self, choices=["Private", "Public"])
        self.visibility.Bind(wx.EVT_CHOICE, self.updateProject)
        self.visSizer.Add(self.visibility, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        self.visibility.SetToolTip(_translate(
            "Visibility of the current project; whether its visible only to its creator (Private) or to any user "
            "(Public)."
        ))
        # Status
        self.statusSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.statusSizer, flag=wx.EXPAND)
        self.statusLbl = wx.StaticText(self, label=_translate("Status:"))
        self.statusSizer.Add(self.statusLbl, border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        self.status = wx.Choice(self, choices=["Running", "Piloting", "Inactive"])
        self.status.Bind(wx.EVT_CHOICE, self.updateProject)
        self.statusSizer.Add(self.status, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        self.status.SetToolTip(_translate(
            "Project status; whether it can be run to collect data (Running), run by its creator without saving "
            "data (Piloting) or cannot be run (Inactive)."
        ))
        # Tags
        self.tagSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.tagSizer, flag=wx.EXPAND)
        self.tagLbl = wx.StaticText(self, label=_translate("Keywords:"))
        self.tagSizer.Add(self.tagLbl, border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        self.tags = utils.ButtonArray(self, orient=wx.HORIZONTAL, items=[], itemAlias=_translate("tag"))
        self.tags.Bind(wx.EVT_LIST_INSERT_ITEM, self.updateProject)
        self.tags.Bind(wx.EVT_LIST_DELETE_ITEM, self.updateProject)
        self.tagSizer.Add(self.tags, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        self.tags.SetToolTip(_translate(
            "Keywords associated with this project, helping others to find it. For example, if your experiment is "
            "useful to psychophysicists, you may want to add the keyword 'psychophysics'."
        ))
        # Populate
        if project is not None:
            project.refresh()
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
            self.icon.SetBackgroundColour("#f2f2f2")
            self.icon.Disable()
            # Title
            self.title.SetValue("")
            self.title.Disable()
            # Author
            self.author.SetLabel("by --- on ---")
            self.author.Disable()
            # Link
            self.link.SetLabel("---/---")
            self.link.SetURL("https://pavlovia.org/")
            self.link.Disable()
            # Star button
            self.starBtn.Disable()
            self.starBtn.value = False
            # Star label
            self.starLbl.SetLabel("-")
            self.starLbl.Disable()
            # Fork button
            self.forkBtn.Disable()
            # Fork label
            self.forkLbl.SetLabel("-")
            self.forkLbl.Disable()
            # Create button
            self.createBtn.Show()
            self.createBtn.Enable(bool(self.session.user))
            # Sync button
            self.syncBtn.Hide()
            # Get button
            self.downloadBtn.Hide()
            # Sync label
            self.syncLbl.SetLabel("---")
            self.syncLbl.Disable()
            # Local root
            self.localRootLabel.Disable()
            wx.TextCtrl.SetValue(self.localRoot, "")  # use base method to avoid callback
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
        elif project.project is None:
            # If project has been deleted, prompt to unlink
            dlg = wx.MessageDialog(
                self,
                message=_translate(
                    "Could not find GitLab project with id {}.\n"
                    "\n"
                    "Please check that the project exists on Pavlovia, that you are logged in as the correct user in "
                    "the PsychoPy app, and that your account has access to the project."
                ).format(project.id),
                style=wx.ICON_ERROR
            )
            dlg.ShowModal()
            self.project = None
        else:
            # Refresh project to make sure it has info
            if not hasattr(project, "_info"):
                project.refresh()
            # Icon
            if 'avatarUrl' in project.info:
                try:
                    content = requests.get(project['avatar_url']).content
                    icon = wx.Bitmap(wx.Image(io.BytesIO(content)))
                except requests.exceptions.MissingSchema:
                    icon = wx.Bitmap()
            else:
                icon = wx.Bitmap()
            self.icon.SetBitmap(icon)
            self.icon.SetBackgroundColour("#f2f2f2")
            self.icon.Enable(project.editable)
            # Title
            self.title.SetValue(project['name'])
            self.title.Enable(project.editable)
            # Author
            self.author.SetLabel(f"by {project['path_with_namespace'].split('/')[0]} on {project['created_at']:%d %B %Y}")
            self.author.Enable()
            # Link
            self.link.SetLabel(project['path_with_namespace'])
            self.link.SetURL("https://pavlovia.org/" + project['path_with_namespace'])
            self.link.Enable()
            # Star button
            self.starBtn.value = project.starred
            self.starBtn.Enable(bool(project.session.user))
            # Star label
            self.starLbl.SetLabel(str(project['star_count']))
            self.starLbl.Enable()
            # Fork button
            self.forkBtn.Enable(bool(project.session.user) and not project.owned)
            # Fork label
            self.forkLbl.SetLabel(str(project['forks_count']))
            self.forkLbl.Enable()
            # Create button
            self.createBtn.Hide()
            # Sync button
            self.syncBtn.Show(bool(project.localRoot) or (not project.editable))
            self.syncBtn.Enable(project.editable)
            # Get button
            self.downloadBtn.Show(not bool(project.localRoot) and project.editable)
            self.downloadBtn.Enable(project.editable)
            # Sync label
            self.syncLbl.SetLabel(f"{project['last_activity_at']:%d %B %Y, %I:%M%p}")
            self.syncLbl.Show(bool(project.localRoot) or (not project.editable))
            self.syncLbl.Enable(project.editable)
            # Local root
            wx.TextCtrl.SetValue(self.localRoot, project.localRoot or "")  # use base method to avoid callback
            self.localRootLabel.Enable(project.editable)
            self.localRoot.Enable(project.editable)
            # Description
            self.description.SetValue(project['description'])
            self.description.Enable(project.editable)
            # Visibility
            self.visibility.SetStringSelection(project['visibility'])
            self.visibility.Enable(project.editable)
            # Status
            self.status.SetStringSelection(str(project['status2']).title())
            self.status.Enable(project.editable)
            # Tags
            self.tags.items = project['keywords']
            self.tags.Enable(project.editable)

        # Layout
        self.Layout()

    @property
    def session(self):
        # Cache session if not cached
        if not hasattr(self, "_session"):
            self._session = pavlovia.getCurrentSession()
        # Return cached session
        return self._session

    def create(self, evt=None):
        """
        Create a new project
        """
        dlg = sync.CreateDlg(self, user=self.session.user)
        dlg.ShowModal()
        self.project = dlg.project

    def sync(self, evt=None):
        # If not synced locally, choose a folder
        if not self.localRoot.GetValue():
            self.localRoot.browse()
        # If cancelled, return
        if not self.localRoot.GetValue():
            return
        self.project.localRoot = self.localRoot.GetValue()
        # Enable ctrl now that there is a local root
        self.localRoot.Enable()
        self.localRootLabel.Enable()
        # Get filename if available
        if hasattr(self.GetTopLevelParent(), "filename"):
            file = self.parent.filename
        else:
            file = ""
        # Do sync
        syncProject(self, self.project, file=file)
        # Update project
        self.project.refresh()
        # Update last sync date & show
        self.syncLbl.SetLabel(f"{self.project['last_activity_at']:%d %B %Y, %I:%M%p}")
        self.syncLbl.Show()
        self.syncLbl.Enable()
        # Switch buttons to show Sync rather than Download/Create
        self.createBtn.Hide()
        self.downloadBtn.Hide()
        self.syncBtn.Show()
        self.syncBtn.Enable()

    def fork(self, evt=None):
        # Do fork
        try:
            proj = self.project.fork()
        except gitlab.GitlabCreateError as e:
            # If project already exists, ask user if they want to view it rather than create again
            dlg = wx.MessageDialog(self, f"{e.error_message}\n\nOpen forked project?", style=wx.YES_NO)
            if dlg.ShowModal() == wx.ID_YES:
                # If yes, show forked project
                projData = requests.get(
                    f"https://pavlovia.org/api/v2/experiments/{self.project.session.user['username']}/{self.project.info['pathWithNamespace'].split('/')[1]}"
                ).json()
                self.project = PavloviaProject(projData['experiment']['gitlabId'])
                return
            else:
                # If no, return
                return
        # Switch to new project
        self.project = proj
        # Sync
        dlg = wx.MessageDialog(self, "Fork created! Sync it to a local folder?", style=wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            self.sync()

    def star(self, evt=None):
        # Toggle button
        self.starBtn.toggle()
        # Star/unstar project
        self.updateProject(evt)
        # todo: Refresh stars count

    def updateProject(self, evt=None):
        # Skip if no project
        if self.project is None or evt is None:
            return
        # Get object
        obj = evt.GetEventObject()

        # Update project attribute according to supplying object
        if obj == self.title and self.project.editable:
            self.project['name'] = self.title.Value
            self.project.save()
        if obj == self.icon:
            # Create temporary image file
            _, temp = tempfile.mkstemp(suffix=".png")
            self.icon.BitmapFull.SaveFile(temp, wx.BITMAP_TYPE_PNG)
            # Load and upload from temp file
            self.project['avatar'] = open(temp, "rb")
            self.project.save()
            # Delete temp file
            #os.remove(temp)
        if obj == self.starBtn:
            self.project.starred = self.starBtn.value
            self.starLbl.SetLabel(str(self.project.info['nbStars']))
        if obj == self.localRoot:
            if Path(self.localRoot.Value).is_dir():
                self.project.localRoot = self.localRoot.Value
            else:
                dlg = wx.MessageDialog(self,
                                       message=_translate(
                                           "Could not find folder {directory}, please select a different "
                                           "local root.".format(directory=self.localRoot.Value)
                                       ),
                                       caption="Directory not found",
                                       style=wx.ICON_ERROR)
                self.localRoot.SetValue("")
                self.project.localRoot = ""
                dlg.ShowModal()
            # Set project again to trigger a refresh
            self.project = self.project
        if obj == self.description and self.project.editable:
            self.project['description'] = self.description.Value
            self.project.save()
        if obj == self.visibility and self.project.editable:
            self.project['visibility'] = self.visibility.GetStringSelection().lower()
            self.project.save()
        if obj == self.status and self.project.editable:
            retval = self.session.session.put(
                f"https://pavlovia.org/api/v2/experiments/{self.project.id}",
                json={'status2': self.status.GetStringSelection().upper()}
            )
        if obj == self.tags and self.project.editable:
            retval = self.session.session.put(
                f"https://pavlovia.org/api/v2/experiments/{self.project.id}",
                json={"keywords": self.tags.GetValue()}
            )


class ProjectFrame(wx.Dialog):

    def __init__(self, app, parent=None, style=None,
                 pos=wx.DefaultPosition, project=None):
        if style is None:
            style = (wx.DEFAULT_DIALOG_STYLE | wx.CENTER |
                     wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        if project:
            title = project['name']
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
        self.mainSizer.Add(self.detailsPanel, proportion=1, border=12, flag=wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)

        if self.parent:
            self.CenterOnParent()
        self.Layout()


def syncProject(parent, project, file="", closeFrameWhenDone=False):
    """A function to sync the current project (if there is one)

    Returns
    -----------
        1 for success
        0 for fail
        -1 for cancel at some point in the process
    """
    # Error catch logged out
    session = pavlovia.getCurrentSession()
    if not session or not session.user:
        # If not logged in, prompt to login
        dlg = wx.MessageDialog(None, message=_translate(
            "You are not logged in to Pavlovia. Please log in to sync project."
        ), style=wx.ICON_AUTH_NEEDED | wx.OK | wx.CANCEL)
        dlg.SetOKLabel(_translate("Login..."))
        if dlg.ShowModal() == wx.ID_OK:
            # If they click Login, open login screen
            user = functions.logInPavlovia(None)
            # If they cancelled out of login screen, cancel sync
            if not user:
                return
        else:
            # If they cancel out of login prompt, cancel sync
            return
    # If not in a project, make one
    if project is None:
        msgDlg = wx.MessageDialog(parent,
                               message=_translate("This file doesn't belong to any existing project."),
                               style=wx.OK | wx.CANCEL | wx.CENTER)
        msgDlg.SetOKLabel(_translate("Create a project"))
        if msgDlg.ShowModal() == wx.ID_OK:
            # Get start path and name from builder/coder if possible
            if file:
                file = Path(file)
                name = file.stem
                path = file.parent
            else:
                name = path = ""
            # Open dlg to create new project
            createDlg = sync.CreateDlg(parent,
                                       user=pavlovia.getCurrentSession().user,
                                       name=name,
                                       path=path)
            if createDlg.ShowModal() == wx.ID_OK and createDlg.project is not None:
                project = createDlg.project
            else:
                return
        else:
            return
    # If no local root or dead local root, prompt to make one
    if not project.localRoot or not Path(project.localRoot).is_dir():
        defaultRoot = Path(file).parent
        if not project.localRoot:
            # If there is no local root at all, prompt user to make one
            msg = _translate("Project root folder is not yet specified, specify project root now?")
        elif not Path(project.localRoot).is_dir():
            # If there is a local root but the folder is gone, prompt user to change it
            msg = _translate("Project root folder does not exist, change project root now?")
        # Ask user if they want to
        dlg = wx.MessageDialog(parent, message=msg, style=wx.OK | wx.CANCEL)
        # Get response
        if dlg.ShowModal() == wx.ID_OK:
            # Attempt to get folder of current file
            if file and defaultRoot.is_dir():
                # If we have a reference to the current folder, use it
                project.localRoot = defaultRoot
            else:
                # Otherwise, ask designer to specify manually
                dlg = wx.DirDialog(parent, message=_translate("Specify folder..."), defaultPath=str(defaultRoot))
                if dlg.ShowModal() == wx.ID_OK:
                    project.localRoot = str(dlg.GetPath())
                else:
                    # If cancelled, cancel sync
                    return
        else:
            # If they don't want to specify, cancel sync
            return
    # Assign project to parent frame
    parent.project = project
    # If there is (now) a project, do sync
    if project is not None:
        # Show sync dlg
        dlg = sync.SyncDialog(parent, project)
        # Commit changes
        committed = functions.showCommitDialog(parent, project, initMsg="", infoStream=dlg.status)
        # Cancel sync if commit cancelled
        if committed == -1:
            dlg.status.write(_translate(
                "\n"
                "Sync cancelled by user."
            ))
            dlg.OKbtn.Enable(True)
            return
        # Do sync
        dlg.sync()


class ForkDlg(wx.Dialog):
    """Simple dialog to help choose the location/name of a forked project"""
    # this dialog is working fine, but the API call to fork to a specific
    # namespace doesn't appear to work
    def __init__(self, project, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)

        existingName = project.name
        session = pavlovia.getCurrentSession()
        groups = [session.user['username']]
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
