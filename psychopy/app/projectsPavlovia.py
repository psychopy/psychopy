#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import os
import time
import copy

import wx
import wx.html2
import wx.lib.scrolledpanel as scrlpanel
from past.builtins import basestring

try:
    import wx.adv as wxhl  # in wx 4
except ImportError:
    wxhl = wx  # in wx 3.0.2

from psychopy import logging, web, prefs
from psychopy.app import dialogs
from psychopy.projects import projectCatalog, projectsFolder, pavlovia
from psychopy.localization import _translate
import requests.exceptions


class PavloviaMenu(wx.Menu):
    app = None
    appData = None
    currentUser = None
    knownUsers = None
    searchDlg = None

    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        PavloviaMenu.app = parent.app
        keys = self.app.keys
        # from prefs fetch info about prev usernames and projects
        PavloviaMenu.appData = self.app.prefs.appData['projects']

        item = self.Append(wx.ID_ANY, _translate("Tell me more..."))
        parent.Bind(wx.EVT_MENU, self.onAbout, id=item.GetId())

        PavloviaMenu.knownUsers = pavlovia.tokenStorage

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        if PavloviaMenu.appData['pavloviaUser'] and not PavloviaMenu.currentUser:
            self.setUser(PavloviaMenu.appData['pavloviaUser'])
        for name in self.knownUsers:
            self.addToSubMenu(name, self.userMenu, self.onSetUser)
        self.userMenu.AppendSeparator()
        item = self.userMenu.Append(wx.ID_ANY,
                                    _translate("Log in to Pavlovia...\t{}")
                                    .format(keys['pavlovia_logIn']))
        parent.Bind(wx.EVT_MENU, self.onLogInPavlovia, id=item.GetId())
        self.AppendSubMenu(self.userMenu, _translate("User"))

        # search
        item = self.Append(wx.ID_ANY,
                           _translate("Search Pavlovia\t{}")
                           .format(keys['projectsFind']))
        parent.Bind(wx.EVT_MENU, self.onSearch, id=item.GetId())

        # new
        item = self.Append(wx.ID_ANY,
                           _translate("New...\t{}").format(keys['projectsNew']))
        parent.Bind(wx.EVT_MENU, self.onNew, id=item.GetId())

        # self.Append(wxIDs.projsSync, "Sync\t{}".format(keys['projectsSync']))
        # parent.Bind(wx.EVT_MENU, self.onSync, id=wxIDs.projsSync)

    def addToSubMenu(self, name, menu, function):
        item = menu.Append(wx.ID_ANY, name)
        self.parent.Bind(wx.EVT_MENU, function, id=item.GetId())

    def onAbout(self, event):
        wx.GetApp().followLink(event)

    def onSetUser(self, event):
        user = self.userMenu.GetLabelText(event.GetId())
        self.setUser(user)

    def setUser(self, user):
        if user == PavloviaMenu.currentUser:
            return  # nothing to do here. Move along please.
        PavloviaMenu.currentUser = user
        PavloviaMenu.appData['pavloviaUser'] = user
        pavlovia.login(user)
        if self.searchDlg:
            self.searchDlg.updateUserProjs()

    # def onSync(self, event):
    #    logging.info("")
    #    pass  # TODO: create quick-sync from menu item

    def onSearch(self, event):
        PavloviaMenu.searchDlg = SearchFrame(app=self.parent.app)
        PavloviaMenu.searchDlg.Show()

    def onLogInPavlovia(self, event):
        # check known users list
        info = {}
        url, state = pavlovia.getAuthURL()
        dlg = OAuthBrowserDlg(self.parent, url, info=info)
        dlg.ShowModal()
        if info and state==info['state']:
            token = info['token']
            pavlovia.login(token)

    def onNew(self, event):
        """Create a new project
        """
        if pavlovia.currentSession.user.username:
            projEditor = ProjectEditor()
            projEditor.Show()
        else:
            infoDlg = dialogs.MessageDialog(parent=None, type='Info',
                                            message=_translate(
                                                "You need to log in"
                                                " to create a project"))
            infoDlg.Show()

    def onOpenFile(self, event):
        """Open project file from dialog
        """
        dlg = wx.FileDialog(parent=None,
                            message=_translate("Open local project file"),
                            style=wx.FD_OPEN,
                            wildcard=_translate(
                                "Project files (*.psyproj)|*.psyproj"))
        if dlg.ShowModal() == wx.ID_OK:
            projFile = dlg.GetPath()
            self.openProj(projFile)


# LogInDlgPavlovia
class OAuthBrowserDlg(wx.Dialog):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
    def __init__(self, parent, url, info,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        wx.Dialog.__init__(self, parent, pos=pos, size=size, style=style)
        self.tokenInfo = info
        # create browser window for authentication
        self.browser = wx.html2.WebView.New(self)
        self.browser.LoadURL(url)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.onNewURL)

        # do layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)
        self.SetSize((700, 700))

    def onNewURL(self, event):
        url = self.browser.CurrentURL
        if 'access_token=' in url:
            self.tokenInfo['token'] = self.getParamFromURL('access_token')
            self.tokenInfo['tokenType'] = self.getParamFromURL('token_type')
            self.tokenInfo['state'] = self.getParamFromURL('state')
            self.EndModal(wx.ID_OK)

    def getParamFromURL(self, paramName):
        url = self.browser.CurrentURL
        return url.split(paramName+'=')[1].split('&')[0]


class BaseFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Center()
        # set up menu bar
        self.menuBar = wx.MenuBar()
        self.fileMenu = self.makeFileMenu()
        self.menuBar.Append(self.fileMenu, _translate('&File'))
        self.SetMenuBar(self.menuBar)

    def makeFileMenu(self):
        fileMenu = wx.Menu()
        app = wx.GetApp()
        keyCodes = app.keys
        # add items to file menu
        fileMenu.Append(wx.ID_CLOSE,
                        _translate("&Close View\t%s") % keyCodes['close'],
                        _translate("Close current window"))
        self.Bind(wx.EVT_MENU, self.closeFrame, id=wx.ID_CLOSE)
        # -------------quit
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT,
                        _translate("&Quit\t%s") % keyCodes['quit'],
                        _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, app.quit, id=wx.ID_EXIT)
        return fileMenu

    def closeFrame(self, event=None, checkSave=True):
        self.Destroy()

    def checkSave(self):
        """If the app asks whether everything is safely saved
        """
        return True  # for OK


class SearchFrame(BaseFrame):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        title = _translate("Search for projects online")
        self.frameType = 'ProjectSearch'
        BaseFrame.__init__(self, None, -1, title, pos, size, style)
        self.app = app
        self.currentProject = None

        # to show detail of current selection
        self.detailsPanel = DetailsPanel(parent=self)

        # create list of my projects (no search?)
        self.myProjectsPanel = ProjectListPanel(self, self.detailsPanel)

        # create list of searchable public projects
        self.publicProjectsPanel = ProjectListPanel(self, self.detailsPanel)
        self.publicProjectsPanel.setContents('')

        # sizers: on the left we have search boxes
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.StaticText(self, -1, _translate("My Projects")),
                      flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(self.myProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, -1, _translate("Search Public:")))
        self.searchTextCtrl = wx.TextCtrl(self, -1, "",
                                          style=wx.TE_PROCESS_ENTER)
        self.searchTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        searchSizer.Add(self.searchTextCtrl, flag=wx.EXPAND)
        leftSizer.Add(searchSizer)
        tagsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagsSizer.Add(wx.StaticText(self, -1, _translate("Tags:")))
        self.tagsTextCtrl = wx.TextCtrl(self, -1, "psychopy,",
                                        style=wx.TE_PROCESS_ENTER)
        self.tagsTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        tagsSizer.Add(self.tagsTextCtrl, flag=wx.EXPAND)
        leftSizer.Add(tagsSizer)
        leftSizer.Add(self.publicProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)

        # sizers: on the right we have detail
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(wx.StaticText(self, -1, _translate("Project Info")),
                       flag=wx.ALL,
                       border=5)
        self.syncButton = wx.Button(self, -1, _translate("Sync..."))
        self.syncButton.Enable(False)
        rightSizer.Add(self.syncButton,
                       flag=wx.ALL, border=5)
        self.syncButton.Bind(wx.EVT_BUTTON, self.onSyncButton)
        rightSizer.Add(self.detailsPanel,
                       proportion=1,
                       flag=wx.EXPAND | wx.ALL,
                       border=10)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(leftSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.mainSizer.Add(rightSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.SetSizerAndFit(self.mainSizer)

        aTable = wx.AcceleratorTable([(0, wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      ])
        self.SetAcceleratorTable(aTable)
        self.Show()  # show the window before doing search/updates
        self.updateUserProjs()  # update the info in myProjectsPanel

    def onSyncButton(self, event):
        if self.currentProject is None:
            raise AttributeError("User pressed the sync button with no "
                                 "current project existing.")
        projFrame = ProjectFrame(parent=self.app, id=-1,
                                 title=self.currentProject.name)
        projFrame.setProject(self.currentProject,
                             name=self.currentProject.id)
        self.Close()  # we're going over to the project window

    def updateUserProjs(self):
        if not pavlovia.currentSession.user:
            self.myProjectsPanel.setContents(
                _translate("No user logged in"))
        else:
            self.myProjectsPanel.setContents(
                _translate("Searching projects for user {} ...")
                    .format(pavlovia.currentSession.user.username))
            self.Update()
            wx.Yield()
            myProjs = pavlovia.currentSession.findUserProjects()
            self.myProjectsPanel.setContents(myProjs)

    def onSearch(self, evt):
        searchStr = self.searchTextCtrl.GetValue()
        tagsStr = self.tagsTextCtrl.GetValue()
        session = pavlovia.currentSession
        self.publicProjectsPanel.setContents(_translate("searching..."))
        self.publicProjectsPanel.Update()
        wx.Yield()
        projs = session.findProjects(search_str=searchStr, tags=tagsStr)
        self.publicProjectsPanel.setContents(projs)


class ProjectListPanel(scrlpanel.ScrolledPanel):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """

    def __init__(self, parent, detailsPanel):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, size=(450, 200),
                                         style=wx.SUNKEN_BORDER)
        self.parent = parent
        self.knownProjects = {}
        self.projList = []
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)  # don't do Fit
        self.mainSizer.Fit(self)

        self.SetAutoLayout(True)
        self.SetupScrolling()

    def setContents(self, projects):
        self.DestroyChildren()  # start with a clean slate

        if isinstance(projects, basestring):
            # just text for a window so display
            self.mainSizer.Add(
                wx.StaticText(self, -1, projects),
                flag=wx.EXPAND | wx.ALL, border=5,
            )
        else:
            # a list of projects
            self.projView = wx.ListCtrl(parent=self,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

            # Give it some columns.
            # The ID col we'll customize a bit:
            self.projView.InsertColumn(0, 'owner')
            self.projView.InsertColumn(1, 'name')
            self.projView.InsertColumn(1, 'description')
            self.projList = []
            for index, thisProj in enumerate(projects):
                if not hasattr(thisProj, 'id'):
                    continue
                self.projView.Append([thisProj.owner, thisProj.name,
                                      thisProj.description])
                self.projList.append(thisProj)
            # set the column sizes *after* adding the items
            self.projView.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.projView.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.projView.SetColumnWidth(2, wx.LIST_AUTOSIZE)
            self.mainSizer.Add(self.projView,
                               flag=wx.EXPAND | wx.ALL,
                               proportion=1, border=5, )
            self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                      self.onChangeSelection)

        self.FitInside()

    def onChangeSelection(self, event):
        proj = self.projList[event.GetIndex()]
        self.parent.detailsPanel.setProject(proj)
        proj = self.parent.detailsPanel.project
        perms = proj.permissions['project_access']
        if type(perms)==dict:
            perms = perms['access_level']
        if perms >= pavlovia.permissions['developer']:
            self.parent.syncButton.Enable(True)
            self.parent.currentPavloviaProject = proj
        else:
            self.parent.syncButton.Enable(False)
            self.parent.currentPavloviaProject = None


class DetailsPanel(scrlpanel.ScrolledPanel):

    def __init__(self, parent, noTitle=False,
                 style=wx.VSCROLL | wx.NO_BORDER):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.app = self.parent.app
        self.project = None
        self.noTitle = noTitle

        if not noTitle:
            self.title = wx.StaticText(parent=self, id=-1,
                                       label="", style=wx.ALIGN_CENTER)
            font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            self.title.SetFont(font)
        self.url = wxhl.HyperlinkCtrl(parent=self, id=-1,
                                      label="https://pavlovia.org",
                                      url="https://pavlovia.org",
                                      style=wxhl.HL_ALIGN_LEFT,
                                      )
        self.description = wx.StaticText(parent=self, id=-1,
                                         label=_translate(
                                             "Select a project for details"))
        self.tags = wx.StaticText(parent=self, id=-1,
                                  label="")
        self.visibility = wx.StaticText(parent=self, id=-1,
                                        label="")
        # layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        if not noTitle:
            self.sizer.Add(self.title, border=5,
                           flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER)
        self.sizer.Add(self.url, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.tags, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.visibility, border=5, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                       flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.description, border=5, flag=wx.ALL | wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetupScrolling()
        self.Bind(wx.EVT_SIZE, self.onResize)

    def setProject(self, project):
        if not isinstance(project, pavlovia.PavloviaProject):
            #e.g. '382' or 382
            project = pavlovia.currentSession.projectFromID(project)
        if project is None:
            return  # we're done

        if not self.noTitle:
            self.title.SetLabel(project.name)
        self.url.SetLabel("{}".format(project.name))
        self.url.SetURL("https://gitlab.pavlovia.org/{}/{}"
                        .format(project.owner, project.name))
        self.description.SetLabel(project.attributes['description'])
        if project.visibility in ['public', 'internal']:
            visib = "Public"
        else:
            visib = "Private"
        self.visibility.SetLabel(_translate("Visibility: {}").format(visib))

        while None in project.tags:
            project.tags.remove(None)
        self.tags.SetLabel(_translate("Tags:") + " " + ", ".join(project.tags))

        # store this ID to keep track of the current project
        self.project = project
        self.SendSizeEvent()

    def onResize(self, evt=None):
        if self.project is None:
            return
        w, h = self.GetSize()
        self.description.SetLabel(self.project.attributes['description'])
        self.description.Wrap(w - 20)
        if not self.noTitle:
            self.title.SetLabel(self.project.name)
            self.title.Wrap(w - 20)
        self.Layout()


class ProjectFrame(BaseFrame):

    def __init__(self, parent, id, size=(400, 300), *args, **kwargs):
        BaseFrame.__init__(self, parent=None, id=id, size=size,
                           *args, **kwargs)
        self.frameType = 'project'
        self.app = wx.GetApp()
        self.app.trackFrame(self)
        self.pavloviaProject = None
        self.project = None
        self.syncStatus = None

        # title
        self.title = wx.StaticText(self, -1, _translate("No project opened"),
                                   style=wx.BOLD | wx.ALIGN_CENTER)
        font = wx.Font(18, family=wx.NORMAL, style=wx.NORMAL, weight=wx.BOLD)
        self.title.SetFont(font)
        self.title.SetMinSize((300, -1))
        self.title.Wrap(300)
        # name box
        nameBox = wx.StaticBox(self, -1, _translate("Name (for PsychoPy use):"))
        nameSizer = wx.StaticBoxSizer(nameBox, wx.VERTICAL)
        self.nameCtrl = wx.TextCtrl(self, -1, "", style=wx.TE_LEFT)
        nameSizer.Add(self.nameCtrl, flag=wx.EXPAND | wx.ALL, border=5)
        # local files
        localsBox = wx.StaticBox(self, -1, _translate("Local Info"))
        localsSizer = wx.StaticBoxSizer(localsBox, wx.VERTICAL)
        localBrowseBtn = wx.Button(self, -1, _translate("Browse..."))
        localBrowseBtn.Bind(wx.EVT_BUTTON, self.onBrowseLocal)
        self.localPath = wx.StaticText(self, -1, "")
        filesSizer = wx.BoxSizer(wx.HORIZONTAL)
        filesSizer.Add(wx.StaticText(self, -1, _translate("Local files:")))
        filesSizer.Add(localBrowseBtn, flag=wx.ALL, border=5)
        localsSizer.Add(filesSizer, flag=wx.ALL, border=5)
        localsSizer.Add(self.localPath, flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                        proportion=1, border=5)

        # sync controls
        syncBox = wx.StaticBox(self, -1, _translate("Sync"))
        self.syncButton = wx.Button(self, -1, _translate("Sync Now"))
        self.syncButton.Bind(wx.EVT_BUTTON, self.onSyncBtn)
        self.syncStatus = SyncStatusPanel(self, id=-1,
                                          project=self.project)
        self.status = wx.StaticText(self, -1, "put status updates here")
        syncSizer = wx.StaticBoxSizer(syncBox, wx.VERTICAL)
        syncSizer.Add(self.syncButton, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)
        syncSizer.Add(self.syncStatus, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)
        syncSizer.Add(self.status, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)

        projBox = wx.StaticBox(self, -1, _translate("Project Info"))
        projSizer = wx.StaticBoxSizer(projBox, wx.VERTICAL)
        self.projDetails = DetailsPanel(parent=self, noTitle=True)
        projSizer.Add(self.projDetails, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)
        # mainSizer with title, then two columns
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.title,
                           flag=wx.ALIGN_CENTER | wx.ALL, border=20)

        # set contents for left and right sizers
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(projSizer, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(nameSizer, flag=wx.EXPAND | wx.ALL,
                       proportion=0, border=5)
        rightSizer.Add(localsSizer, flag=wx.EXPAND | wx.ALL,
                       proportion=0, border=5)
        rightSizer.Add(syncSizer, flag=wx.ALL, border=5)

        columnSizer = wx.BoxSizer(wx.HORIZONTAL)
        columnSizer.Add(leftSizer, border=5,
                        flag=wx.EXPAND | wx.ALL, proportion=1)
        columnSizer.Add(rightSizer, border=5,
                        flag=wx.EXPAND | wx.ALL, proportion=0.75)
        self.mainSizer.Add(columnSizer, proportion=1,
                           flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(self.mainSizer)
        self.SetAutoLayout(True)
        self.update()

        self.app.trackFrame(self)
        self.Show()

    def onBrowseLocal(self, evt):
        dlg = wx.DirDialog(self,
                           message=_translate(
                               "Root folder of your local files"))
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            self.localPath.SetLabel(newPath)
            if self.project:
                self.project.root_path = newPath
        self.update()

    def setProject(self, project, name=None):
        """Sets the current project

        :params:

            - project can be a pysof.Project object or a filename to load

        If this loads successfully then the project root and OSF project ID
        will also be updated
        """
        # check does it still exist locally?
        # does it still exist online?
        self.project = project  # do this after checking that it's valid
        self.update()

    def _setCurrentProject(self, pavProject):
        """This is run when we get a project from the search dialog (rather
        than from a previously loaded project file)
        """
        self.pavProject = pavProject
        self.title.SetLabel(pavProject.name)
        self.projDetails.setProject(pavProject)  # update the dialog box
        self.update()

    def onSyncBtn(self, evt):
        self.updateProjectFields()
        # create or reset progress indicators
        self.syncStatus.reset()
        self.update(status=_translate("Checking for changes"))
        time.sleep(0.01)
        changes = self.project.get_changes()
        self.update(status=_translate("Applying changes"))
        time.sleep(0.01)  # give wx a moment to breath
        # start the threads up/downloading
        changes.apply(threaded=True)
        # to check the status we need the
        while True:
            progress = changes.progress
            self.syncStatus.setProgress(progress)
            time.sleep(0.01)
            if progress == 1:
                self.update(_translate("Sync complete"))
                changes.finish_sync()
                self.project.save()
                break

    def update(self, status=None):
        """Update to a particular status if given or deduce status msg if not
        """
        if status is None:
            if not self.currentProject:
                status = _translate("No remote project set")
                self.syncButton.Enable(False)
            elif not self.localPath or not self.localPath.GetLabel():
                status = _translate("No local folder to sync with")
                self.syncButton.Enable(False)
            else:
                status = _translate("Ready")
                self.syncButton.Enable(True)
        self.status.SetLabel(_translate("Status: ") + status)
        self.Layout()
        self.Update()


class ProjectEditor(BaseFrame):
    def __init__(self, parent=None, id=-1, projId="", *args, **kwargs):
        BaseFrame.__init__(self, None, -1, *args, **kwargs)
        panel = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL)
        # when a project is succesffully created these will be populated
        self.currentProject = None
        self.projInfo = None

        if projId:
            # edit existing project
            self.isNew = False
        else:
            self.isNew = True

        # create the controls
        titleLabel = wx.StaticText(panel, -1, _translate("Title:"))
        self.titleBox = wx.TextCtrl(panel, -1, size=(400, -1))
        nameLabel = wx.StaticText(panel, -1,
                                  _translate("Name \n(for local id):"))
        self.nameBox = wx.TextCtrl(panel, -1, size=(400, -1))
        descrLabel = wx.StaticText(panel, -1, _translate("Description:"))
        self.descrBox = wx.TextCtrl(panel, -1, size=(400, 200),
                                    style=wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        tagsLabel = wx.StaticText(panel, -1,
                                  _translate("Tags (comma separated):"))
        self.tagsBox = wx.TextCtrl(panel, -1, size=(400, 100),
                                   value="PsychoPy, Builder, Coder",
                                   style=wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        publicLabel = wx.StaticText(panel, -1, _translate("Public:"))
        self.publicBox = wx.CheckBox(panel, -1)
        # buttons
        if self.isNew:
            buttonMsg = _translate("Create project on OSF")
        else:
            buttonMsg = _translate("Submit changes to OSF")
        updateBtn = wx.Button(panel, -1, buttonMsg)
        updateBtn.Bind(wx.EVT_BUTTON, self.submitChanges)

        # do layout
        mainSizer = wx.FlexGridSizer(cols=2, rows=6, vgap=5, hgap=5)
        mainSizer.AddMany([(titleLabel, 0, wx.ALIGN_RIGHT), self.titleBox,
                           (nameLabel, 0, wx.ALIGN_RIGHT),
                           (self.nameBox, 0, wx.EXPAND),
                           (descrLabel, 0, wx.ALIGN_RIGHT), self.descrBox,
                           (tagsLabel, 0, wx.ALIGN_RIGHT), self.tagsBox,
                           (publicLabel, 0, wx.ALIGN_RIGHT), self.publicBox,
                           (0, 0), (updateBtn, 0, wx.ALIGN_RIGHT)])
        border = wx.BoxSizer()
        border.Add(mainSizer, 0, wx.ALL, 10)
        panel.SetSizerAndFit(border)
        self.Fit()

    def submitChanges(self, evt=None):
        session = wx.GetApp().pavloviaSession
        d = {}
        d['title'] = self.titleBox.GetValue()
        d['name'] = self.nameBox.GetValue()
        d['descr'] = self.descrBox.GetValue()
        d['public'] = self.publicBox.GetValue()
        # tags need splitting and then
        tagsList = self.tagsBox.GetValue().split(',')
        d['tags'] = []
        for thisTag in tagsList:
            d['tags'].append(thisTag.strip())
        if self.isNew:
            newProject = session.create_project(title=d['title'],
                                                descr=d['descr'],
                                                tags=d['tags'],
                                                public=d['public'])

            projFrame = ProjectFrame(parent=None, id=-1, title=d['title'])
            projFrame.setProject(newProject)
            projFrame.nameCtrl.SetValue(d['name'])
            projFrame.Show()
        else:  # to be done
            newProject = session.update_project(id, title=d['title'],
                                                descr=d['descr'],
                                                tags=d['tags'],
                                                public=d['public'])
        # store in self in case we're being watched
        self.currentProject = newProject
        self.projInfo = d
        self.Destroy()  # kill the dialog

