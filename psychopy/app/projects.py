#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import os
import time

import wx
import wx.lib.scrolledpanel as scrlpanel
from past.builtins import basestring

try:
    import wx.adv as wxhl  # in wx 4
except ImportError:
    wxhl = wx  # in wx 3.0.2

from psychopy import logging, web, prefs
from psychopy.app import dialogs
from psychopy.projects import projectCatalog, projectsFolder
from psychopy.localization import _translate
import requests.exceptions

try:
    import pyosf
    from pyosf import constants
    constants.PROJECT_NAME = "PsychoPy"
    havePyosf = True
    if pyosf.__version__ < "1.0.3":
        logging.warn("pyosf is version {} whereas PsychoPy expects 1.0.3+"
                     .format(pyosf.__version__))
except ImportError:
    havePyosf = False


usersList = wx.FileHistory(maxFiles=10, idBase=12300)

# Projects FileHistory sub-menu
idBase=12400
projHistory = wx.FileHistory(maxFiles=16, idBase=idBase)
projHistory.idBase = idBase
for key in projectCatalog:
    projHistory.AddFileToHistory(key)


class ProjectsMenu(wx.Menu):
    app = None
    appData = None
    _user = None
    knownUsers = None
    searchDlg = None

    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        ProjectsMenu.app = parent.app
        keys = self.app.keys
        # from prefs fetch info about prev usernames and projects
        ProjectsMenu.appData = self.app.prefs.appData['projects']

        global projHistory
        self.projHistory = projHistory  # so we can treat as local from here
        global usersList
        self.userList = usersList

        item = self.Append(wx.ID_ANY, _translate("Tell me more..."))
        parent.Bind(wx.EVT_MENU, self.onAbout, id=item.GetId())
        if not havePyosf:
            self.Append(wx.ID_ANY,
                        _translate("Requires pyosf (not installed)"))
            ProjectsMenu.knownUsers = {}
        else:
            if self.app.osf_session is None:
                # create a default (anonymous) session with osf
                self.app.osf_session = pyosf.Session()

            ProjectsMenu.knownUsers = pyosf.TokenStorage()  # a dict name:token

        # sub-menu to open previous or new projects
        self.projsSubMenu = wx.Menu()
        item = self.projsSubMenu.Append(wx.ID_ANY,
                                 _translate("From file...\t{}")
                                 .format(keys['projectsOpen']))
        parent.Bind(wx.EVT_MENU,  self.onOpenFile, id=item.GetId())
        self.projsSubMenu.AppendSeparator()
        self.projHistory.UseMenu(self.projsSubMenu)
        try:
            self.projHistory.AddFilesToMenu(self.projsSubMenu)
        except:
            self.projHistory.AddFilesToThisMenu(self.projsSubMenu)
        parent.Bind(wx.EVT_MENU_RANGE, self.onProjFromHistory,
                    id=self.projHistory.idBase,
                    id2=self.projHistory.idBase+9)
        self.AppendSubMenu(self.projsSubMenu, _translate("Open"))

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        if ProjectsMenu.appData['user'] and \
                ProjectsMenu.appData['user'] in self.knownUsers:
            self.setUser(ProjectsMenu.appData['user'])
        for name in self.knownUsers:
            self.addToSubMenu(name, self.userMenu, self.onSetUser)
        self.userMenu.AppendSeparator()
        item = self.userMenu.Append(wx.ID_ANY,
                             _translate("Log in...\t{}")
                             .format(keys['projectsLogIn']))
        parent.Bind(wx.EVT_MENU, self.onLogIn, id=item.GetId())
        self.AppendSubMenu(self.userMenu, _translate("User"))

        # search
        item = self.Append(wx.ID_ANY,
                    _translate("Search OSF\t{}")
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

    def addFileToHistory(self, filename):
        key = projectCatalog.addFile(filename)
        self.projHistory.AddFileToHistory(key)

    def onProjFromHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - self.projHistory.idBase
        projString = self.projHistory.GetHistoryFile(fileNum)
        projID, projName = projString.split(": ")
        projString, project = projectCatalog.projFromId(projID)
        self.openProj(project)

    def onAbout(self, event):
        wx.GetApp().followLink(event)

    def onSetUser(self, event):
        user = self.userMenu.GetLabelText(event.GetId())
        self.setUser(user)

    def setUser(self, user):
        if user == self._user:
            return  # nothing to do here. Move along please.
        self._user = user
        try:
            self.app.osf_session = pyosf.Session(user)
        except pyosf.AuthError:
            print("failed to authenticate - probably need 2FA")
        except requests.exceptions.ConnectionError:
            logging.warn("Connection error trying to connect to pyosf")
        except requests.exceptions.ReadTimeout:
            logging.warn("Timed out while trying to connect to pyosf")

        ProjectsMenu.appData['user'] = user
        if self.searchDlg:
            self.searchDlg.updateUserProjs()

    # def onSync(self, event):
    #    logging.info("")
    #    pass  # TODO: create quick-sync from menu item

    def onSearch(self, event):
        ProjectsMenu.searchDlg = SearchFrame(app=self.parent.app)
        ProjectsMenu.searchDlg.Show()

    def onLogIn(self, event):
        # check knownusers list
        users = list(ProjectsMenu.knownUsers.keys())
        dlg = LogInDlg(app=self.app)
        dlg.Show()
        if self.app.osf_session.authenticated:
            username = self.app.osf_session.username
            # check whether we need to add this to users menu
            if (username not in users) and \
                    (username in ProjectsMenu.knownUsers):
                # it wasn't there, but is now. Add to menu
                self.addUserToSubMenu(username)

    def onNew(self, event):
        """Create a new project for OSF
        """
        if self.app.osf_session.user_id:
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

    def openProj(self, project):
        # create a sync frame to put that in
        projFrame = ProjectFrame(parent=self.app, id=-1)
        projFrame.setProject(project)
        # also update history with file path
        projectFile = project.project_file
        self.updateProjHist(projectFile)

    def updateProjHist(self, projFile):
        # add it back to the history so it will be moved up the list
        key = projectCatalog.addFile(projFile)
        self.projHistory.AddFileToHistory(key)
        projList = ProjectsMenu.appData['fileHistory']  # the saved history
        if projFile not in projList:
            projList.insert(0, projFile)
            if len(projList) > 10:
                ProjectsMenu.appData['fileHistory'] = projList[:10]


class LogInDlg(wx.Dialog):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        wx.Dialog.__init__(self, None,
                           title=_translate(
                           "Log in to Open Science Framework"))
        self.session = app.osf_session
        self.app = app

        self.fieldsSizer = wx.GridBagSizer(vgap=5, hgap=5)

        if web.haveInternetAccess():
            self.status = wx.StaticText(self,
                                        label=_translate("Status: Ready"))
        else:
            self.status = wx.StaticText(self,
                                        label=_translate("No internet access"))
        self.fieldsSizer.Add(self.status,
                             pos=(0, 0), span=(1, 2),
                             flag=wx.ALIGN_CENTER, border=10)

        # user info
        self.fieldsSizer.Add(wx.StaticText(
            self,
            label=_translate("OSF Username (email)")),
                             pos=(1, 0), flag=wx.ALIGN_RIGHT)
        self.username = wx.TextCtrl(self)
        self.username.SetToolTip(_translate("Your username on OSF "
                                            "(the email address you used)"))
        self.fieldsSizer.Add(self.username,
                             pos=(1, 1), flag=wx.ALIGN_LEFT)
        # pass info
        self.fieldsSizer.Add(wx.StaticText(self, label=_translate("Password")),
                             pos=(2, 0), flag=wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(self,
                                    style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.password.SetToolTip(
            _translate("Your password on OSF "
                       "(will be checked securely with https)"))
        self.fieldsSizer.Add(self.password,
                             pos=(2, 1), flag=wx.ALIGN_LEFT)
        # remember me
        self.fieldsSizer.Add(wx.StaticText(
            self, label=_translate("Remember me")),
            pos=(3, 0), flag=wx.ALIGN_RIGHT)
        self.rememberMe = wx.CheckBox(self, True)
        self.rememberMe.SetToolTip(_translate("We won't store your password - "
                                              "just an authorisation token"))
        self.fieldsSizer.Add(self.rememberMe,
                             pos=(3, 1), flag=wx.ALIGN_LEFT)

        # buttons (Log in, Cancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelBtn = wx.Button(
            self, wx.ID_CANCEL, _translate('Cancel'))
        self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)
        btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)

        self.okBtn = wx.Button(self, wx.ID_OK, _translate("Login"))
        self.okBtn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.onLogin, id=wx.ID_OK)
        btnSizer.Add(self.okBtn, wx.ALIGN_RIGHT)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.fieldsSizer, 0, wx.ALL, 5)
        self.main_sizer.Add(btnSizer, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizerAndFit(self.main_sizer)

    def onLogin(self, event):
        """
        Check credentials and login
        """
        if not havePyosf:
            dialogs.MessageDialog(parent=self.parent, type='Warning',
                                  title=_translate("pyosf not found"),
                                  message=_translate("You need pyosf to "
                                          "log in to Open Science Framework"),
                                  )
            return None
        username = self.username.GetValue()
        pword = self.password.GetValue()
        rememberMe = bool(self.rememberMe.GetValue())
        try:
            session = pyosf.Session(username=username,
                                    password=pword, remember_me=rememberMe)
            self.app.osf_session = session
            self.updateStatus(_translate("Successful authentication"),
                              color=(0, 170, 0))
            time.sleep(0.5)
            self.Destroy()
        except pyosf.AuthError:
            self.updateStatus(_translate("Failed to Authenticate. "
                              "Check username/password"), color=(255, 0, 0))

    def onCancel(self, event):
        self.Destroy()

    def updateStatus(self, status, color=(0, 0, 0)):
        self.status.SetLabel(status)
        self.status.SetForegroundColour(color)  # set text color
        self.main_sizer.Fit(self)
        self.Update()


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
        title = _translate("Search OSF (Open Science Framework)")
        self.frameType = 'OSFsearch'
        BaseFrame.__init__(self, None, -1, title, pos, size, style)
        self.app = app
        self.currentOSFProject = None

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

        aTable = wx.AcceleratorTable([(0,  wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      ])
        self.SetAcceleratorTable(aTable)
        self.Show()  # show the window before doing search/updates
        self.updateUserProjs()  # update the info in myProjectsPanel

    def onSyncButton(self, event):
        if self.currentOSFProject is None:
            raise AttributeError("User pressed the sync button with no "
                                 "searchDlg.currentOSFProject existing. "
                                 "Ask them how they managed that!")
        projFrame = ProjectFrame(parent=self.app, id=-1,
                                 title=self.currentOSFProject.title)
        projFrame.setProject(self.currentOSFProject,
                             name=self.currentOSFProject.id)
        self.Close()  # we're going over to the project window

    def updateUserProjs(self):
        if self.app.osf_session.user_id is None:
            self.myProjectsPanel.setContents(
                _translate("No user logged in. \n\n"
                "Go to menu item Projects>Users>"))
        else:
            self.myProjectsPanel.setContents(
                _translate("Searching projects for user {} ...")
                .format(self.app.osf_session.username))
            self.Update()
            wx.Yield()
            myProjs = self.app.osf_session.find_user_projects()
            self.myProjectsPanel.setContents(myProjs)

    def onSearch(self, evt):
        searchStr = self.searchTextCtrl.GetValue()
        tagsStr = self.tagsTextCtrl.GetValue()
        session = self.app.osf_session
        self.publicProjectsPanel.setContents(_translate("searching..."))
        self.publicProjectsPanel.Update()
        wx.Yield()
        projs = session.find_projects(search_str=searchStr, tags=tagsStr)
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
            self.projView.InsertColumn(0, 'id')
            self.projView.InsertColumn(1, 'title')
            for index, thisProj in enumerate(projects):
                self.knownProjects[thisProj.id] = thisProj
                self.projView.Append([thisProj.id, thisProj.title])
            # set the column sizes *after* adding the items
            self.projView.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.projView.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.mainSizer.Add(self.projView,
                               flag=wx.EXPAND | wx.ALL,
                               proportion=1, border=5,)
            self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                      self.onChangeSelection)

        self.FitInside()

    def onChangeSelection(self, event):
        projId = event.GetText()
        proj = self.knownProjects[projId]
        self.parent.detailsPanel.setProject(proj)
        if 'write' in proj.attributes['current_user_permissions']:
            self.parent.syncButton.Enable(True)
            self.parent.currentOSFProject = proj
        else:
            self.parent.syncButton.Enable(False)
            self.parent.currentOSFProject = None


class DetailsPanel(scrlpanel.ScrolledPanel):

    def __init__(self, parent, noTitle=False,
                 style=wx.VSCROLL | wx.NO_BORDER):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.app = self.parent.app
        self.currentProj = None
        self.noTitle = noTitle

        if not noTitle:
            self.title = wx.StaticText(parent=self, id=-1,
                                       label="", style=wx.ALIGN_CENTER)
            font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            self.title.SetFont(font)
        self.url = wxhl.HyperlinkCtrl(parent=self, id=-1,
                                    label="https://osf.io",
                                    url="https://osf.io",
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
        if project is None:
            return  # we're done

        if not self.noTitle:
            self.title.SetLabel(project.title)
        self.url.SetLabel("https://osf.io/{}".format(project.id))
        self.url.SetURL("https://osf.io/{}".format(project.id))
        self.description.SetLabel(project.attributes['description'])

        if project.attributes['public'] is True:
            visib = "Public"
        else:
            visib = "Private"
        self.visibility.SetLabel(_translate("Visibility: {}").format(visib))
        tags = project.attributes['tags']
        while None in tags:
            tags.remove(None)
        self.tags.SetLabel(_translate("Tags:")+" "+", ".join(tags))

        # store this ID to keep track of the current project
        self.currentProj = project
        self.SendSizeEvent()

    def onResize(self, evt=None):
        if self.currentProj is None:
            return
        w, h = self.GetSize()
        self.description.SetLabel(self.currentProj.attributes['description'])
        self.description.Wrap(w-20)
        if not self.noTitle:
            self.title.SetLabel(self.currentProj.title)
            self.title.Wrap(w-20)
        self.Layout()


class ProjectFrame(BaseFrame):

    def __init__(self, parent, id, size=(400, 300), *args, **kwargs):
        BaseFrame.__init__(self, parent=None, id=id, size=size,
                           *args, **kwargs)
        self.frameType = 'project'
        self.app = wx.GetApp()
        self.app.trackFrame(self)
        self.OSFproject = None
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
                        flag=wx.EXPAND | wx.ALL, proportion=1)
        self.mainSizer.Add(columnSizer, proportion=1,
                           flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(self.mainSizer)
        self.SetAutoLayout(True)
        self.update()

        self.app.trackFrame(self)
        self.Show()

    def onBrowseLocal(self, evt):
        dlg = wx.DirDialog(self,
                           message=_translate("Root folder of your local files"))
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            self.localPath.SetLabel(newPath)
            if self.project:
                self.project.root_path = newPath
        self.update()

    def setProject(self, project, name=None):
        """Sets the current pyosf.Project (which then sets OSF remote project)

        :params:

            - project can be a pysof.Project object or a filename to load

        If this loads successfully then the project root and OSF project ID
        will also be updated
        """
        if isinstance(project, pyosf.Project):
            self._setLocalProject(project)
            try:
                self._setOSFproject(project.osf)
            except pyosf.DeletedError:
                print("OSF Project <{}> no longer exists online"
                      .format(project.project_id))
        elif isinstance(project, pyosf.remote.OSFProject):
            self._setOSFproject(project)
            projStr, localProj = projectCatalog.projFromId(project.id)
            if localProj is None:  # create a project for it
                projPath = "%s/%s.psyproj" % (projectsFolder, name)
                localProj = pyosf.Project(project_file=projPath, osf=project,
                                          autosave=False)
            self._setLocalProject(localProj)
        elif os.path.isfile(project):
            self.projFilePath = project
            project = pyosf.Project(project_file=project)
            # check this is the same project !
            if self.OSFproject and project.osf.id != self.OSFproject.id:
                raise IOError("The project file relates to a different"
                              "OSF project and cannot be used for this one")
            self.project = project  # do this after checking that it's valid
        self.update()

    def _setOSFproject(self, OSFproject):
        """This is run when we get a project from the search dialog (rather
        than from a previously loaded project file)
        """
        self.OSFproject = OSFproject
        self.title.SetLabel(OSFproject.title)
        self.projDetails.setProject(OSFproject)  # update the dialog box
        self.update()

    def _setLocalProject(self, project):
        self.project = project
        self.projFilePath = project.project_file
        if self.project.root_path:
            self.localPath.SetLabel(self.project.root_path)  # update the gui
        if self.project.name:
            self.SetTitle("{}: {}".format(project.project_id, project.name))
            self.nameCtrl.SetValue(project.name)
        else:
            self.SetTitle("{}".format(project.project_id))

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
            if not self.OSFproject:
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

    def updateProjectFields(self):
        if not self.project:
            self.project = pyosf.Project(osf = self.OSFproject)
        name = self.nameCtrl.GetValue()
        if name != '':
            self.project.name = name
        else:
            self.project.name = self.OSFproject.id
        self.project.username = self.OSFproject.session.username
        self.project.project_id = self.OSFproject.id
        projPath = "%s/%s.psyproj" % (projectsFolder, self.project.name)
        self.project.project_file = projPath
        self.project.autosave=True
        self.project.save()
        key = projectCatalog.addFile(self.project.project_file)
        projHistory.AddFileToHistory(key)

class ProjectEditor(BaseFrame):
    def __init__(self, parent=None, id=-1, projId="", *args, **kwargs):
        BaseFrame.__init__(self, None, -1, *args, **kwargs)
        panel = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL)
        # when a project is succesffully created these will be populated
        self.OSFproject = None
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
                                    style = wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        tagsLabel = wx.StaticText(panel, -1,
                                  _translate("Tags (comma separated):"))
        self.tagsBox = wx.TextCtrl(panel, -1, size=(400, 100),
                                   value="PsychoPy, Builder, Coder",
                                   style = wx.TE_MULTILINE | wx.SUNKEN_BORDER)
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
        session = wx.GetApp().osf_session
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
            OSFproject = session.create_project(title=d['title'],
                                                descr=d['descr'],
                                                tags=d['tags'],
                                                public=d['public'])

            projFrame = ProjectFrame(parent=None, id=-1, title=d['title'])
            projFrame.setProject(OSFproject)
            projFrame.nameCtrl.SetValue(d['name'])
            projFrame.Show()
        else:  # to be done
            OSFproject = session.update_project(id, title=d['title'],
                                                descr=d['descr'],
                                                tags=d['tags'],
                                                public=d['public'])
        # store in self in case we're being watched
        self.OSFproject = OSFproject
        self.projInfo = d
        self.Destroy()  # kill the dialog


class SyncStatusPanel(wx.Panel):
    def __init__(self, parent, id, project, *args, **kwargs):
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        self.project = project

        self.sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        self.sizer.AddGrowableCol(1)

        upLabel = wx.StaticText(self, -1, _translate("Uploading:"))
        self.upProg = wx.Gauge(self, -1, range=1, size=(200, -1))
        downLabel = wx.StaticText(self, -1, _translate("Downloading:"))
        self.downProg = wx.Gauge(self, -1, range=1, size=(200, -1))
        self.sizer.AddMany([upLabel, self.upProg,
                            downLabel, self.downProg])
        self.SetSizerAndFit(self.sizer)

    def reset(self):
        self.upProg.SetRange(1)
        self.upProg.SetValue(0)
        self.downProg.SetRange(1)
        self.downProg.SetValue(0)

    def setProgress(self, progress):
        if type(progress)==dict:
            upDone, upTot = progress['up']
            downDone, downTot = progress['down']
        if progress == 1 or upTot == 0:
            self.upProg.SetRange(1)
            self.upProg.SetValue(1)
        else:
            self.upProg.SetRange(upTot)
            self.upProg.SetValue(upDone)
        if progress == 1 or downTot == 0:
            self.downProg.SetRange(1)
            self.downProg.SetValue(1)
        else:
            self.downProg.SetRange(downTot)
            self.downProg.SetValue(downDone)
        self.Update()
        wx.Yield()
        time.sleep(0.1)
