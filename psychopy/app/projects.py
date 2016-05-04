# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

import os
import time
import wx
import wx.lib.scrolledpanel as scrlpanel
from wx import richtext

try:
    import pyosf
    from pyosf import constants
    constants.PROJECT_NAME = "PsychoPy"
    havePyosf = True
except ImportError:
    havePyosf = False
from . import wxIDs
from psychopy import logging, web, prefs
from psychopy.app import dialogs
from .localization import _translate

# Projects FileHistory sub-menu
idBase = wx.NewId()
projHistory = wx.FileHistory(maxFiles=10, idBase=idBase)
projHistory.idBase = idBase
for filename in prefs.appData['projects']['fileHistory']:
    projHistory.AddFileToHistory(filename)

usersList = wx.FileHistory(maxFiles=10, idBase=wx.NewId())


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
        ProjectsMenu.appData = self.app.prefs.appData['projects']

        global projHistory
        self.projHistory = projHistory  # so we can treat as local from here
        global usersList
        self.userList = usersList


        self.Append(wxIDs.projsAbout, "Tell me more...")
        wx.EVT_MENU(parent, wxIDs.projsAbout,  self.onAbout)
        if not havePyosf:
            self.Append(wx.NewId(), "Requires pyosf (not installed)")
            ProjectsMenu.knownUsers = {}
        else:
            if self.app.osf_session is None:
                # create a default (anonymous) session with osf
                self.app.osf_session = pyosf.Session()

            ProjectsMenu.knownUsers = pyosf.TokenStorage()  # a dict name:token

        # sub-menu to open previous or new projects
        self.projsSubMenu = wx.Menu()
        self.projsSubMenu.Append(wxIDs.projsOpen,
                                 "From file...\t{}"
                                 .format(keys['projectsOpen']))
        wx.EVT_MENU(parent, wxIDs.projsOpen,  self.onOpenFile)
        self.projsSubMenu.AppendSeparator()
        self.projHistory.UseMenu(self.projsSubMenu)
        try:
            self.projHistory.AddFilesToMenu(self.projsSubMenu)
        except:
            self.projHistory.AddFilesToThisMenu(self.projsSubMenu)
        parent.Bind(wx.EVT_MENU_RANGE, self.onProjFromHistory,
                    id=self.projHistory.idBase,
                    id2=self.projHistory.idBase+9)
        self.AppendSubMenu(self.projsSubMenu, "Open")

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        if ProjectsMenu.appData['user'] and \
                ProjectsMenu.appData['user'] in self.knownUsers:
            self.setUser(ProjectsMenu.appData['user'])
        for name in self.knownUsers:
            self.addToSubMenu(name, self.userMenu, self.onSetUser)
        self.userMenu.AppendSeparator()
        self.userMenu.Append(wxIDs.projsNewUser,
                             "Log in...\t{}".format(keys['projectsLogIn']))
        wx.EVT_MENU(parent, wxIDs.projsNewUser,  self.onLogIn)
        self.AppendSubMenu(self.userMenu, "User")

        # search
        self.Append(wxIDs.projsSearch,
                    "Search OSF\t{}".format(keys['projectFind']))
        wx.EVT_MENU(parent, wxIDs.projsSearch,  self.onSearch)

        self.Append(wxIDs.projsSync, "Sync\t{}".format(keys['projectsSync']))
        wx.EVT_MENU(parent, wxIDs.projsSync,  self.onSync)

    def addToSubMenu(self, name, menu, function):
        thisId = wx.NewId()
        menu.Append(thisId, name)
        wx.EVT_MENU(self.parent, thisId, function)

    def addFileToHistory(self, filename):
        self.projHistory.AddFileToHistory(filename)

    def onProjFromHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - self.projHistory.idBase
        path = self.projHistory.GetHistoryFile(fileNum)
        self.openProj(path)

    def onAbout(self, event):
        logging.info("")
        pass  # TODO: go to web page

    def onSetUser(self, event):
        user = self.userMenu.GetLabelText(event.GetId())
        self.setUser(user)

    def setUser(self, user):
        if user == self._user:
            return  # nothing to do here. Move along please.
        self._user = user
        self.app.osf_session = pyosf.Session(user)

        ProjectsMenu.appData['user'] = user
        if self.searchDlg is not None:
            self.searchDlg.updateUserProjs()

    def onSync(self, event):
        logging.info("")
        pass  # TODO: project sync and enable/disable

    def onSearch(self, event):
        ProjectsMenu.searchDlg = SearchFrame(app=self.parent.app)
        ProjectsMenu.searchDlg.Show()

    def onLogIn(self, event):
        # check knownusers list
        users = ProjectsMenu.knownUsers.keys()
        dlg = LogInDlg(app=self.app)
        dlg.Show()
        if self.app.osf_session.authenticated:
            username = self.app.osf_session.username
            # check whether we need to add this to users menu
            if (username not in users) and \
                    (username in ProjectsMenu.knownUsers):
                # it wasn't there, but is now. Add to menu
                self.addUserToSubMenu(username)

    def onOpenFile(self, event):
        """Open project file from dialog
        """
        dlg = wx.FileDialog(parent=None, message=("Open local project file"),
                            style=wx.FD_OPEN,
                            wildcard="Project files (*.psyproj)|*.psyproj")
        if dlg.ShowModal() == wx.ID_OK:
            projFile = dlg.GetPath()
            self.openProj(projFile)

    def openProj(self, projFile):
        # create a sync frame to put that in
        syncFrame = ProjectSyncFrame(parent=self.app, id=-1)
        syncFrame.setProjFile(projFile)
        self.updateProjHist(projFile)

    def updateProjHist(self, projFile):
        # add it back to the history so it will be moved up the list
        self.projHistory.AddFileToHistory(projFile)  # the menu item
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
                           title="Log in to Open Science Framework")
        self.session = app.osf_session
        self.app = app

        self.fieldsSizer = wx.GridBagSizer(vgap=5, hgap=5)

        if web.haveInternetAccess():
            self.status = wx.StaticText(self, label="Status: Ready")
        else:
            self.status = wx.StaticText(self, label="No internet access")
        self.fieldsSizer.Add(self.status,
                             pos=(0, 0), span=(1, 2),
                             flag=wx.ALIGN_CENTER, border=10)

        # user info
        self.fieldsSizer.Add(wx.StaticText(self, label="OSF Username (email)"),
                             pos=(1, 0), flag=wx.ALIGN_RIGHT)
        self.username = wx.TextCtrl(self)
        self.username.SetToolTipString("Your username on OSF "
                                       "(the email address you used)")
        self.fieldsSizer.Add(self.username,
                             pos=(1, 1), flag=wx.ALIGN_LEFT)
        # pass info
        self.fieldsSizer.Add(wx.StaticText(self, label="Password"),
                             pos=(2, 0), flag=wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(self,
                                    style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.password.SetToolTipString("Your password on OSF "
                                       "(will be checked securely with https)")
        self.fieldsSizer.Add(self.password,
                             pos=(2, 1), flag=wx.ALIGN_LEFT)
        # remember me
        self.fieldsSizer.Add(wx.StaticText(self, label="Remember me"),
                             pos=(3, 0), flag=wx.ALIGN_RIGHT)
        self.rememberMe = wx.CheckBox(self, True)
        self.rememberMe.SetToolTipString("We won't store your password - "
                                         "just an authorisation token")
        self.fieldsSizer.Add(self.rememberMe,
                             pos=(3, 1), flag=wx.ALIGN_LEFT)

        # buttons (Log in, Cancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelBtn = wx.Button(
            self, wx.ID_CANCEL, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)
        btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)

        self.okBtn = wx.Button(self, wx.ID_OK, "Login")
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
                                  title="pyosf not found",
                                  message="You need pyosf to log in to "
                                          "Open Science Framework",
                                  )
            return None
        username = self.username.GetValue()
        pword = self.password.GetValue()
        rememberMe = bool(self.rememberMe.GetValue())
        try:
            session = pyosf.Session(username=username,
                                    password=pword, remember_me=rememberMe)
            self.app.osf_session = session
            self.updateStatus("Successful authentication", color=(0, 170, 0))
            time.sleep(0.5)
            self.Destroy()
        except pyosf.AuthError:
            self.updateStatus("Failed to Authenticate. "
                              "Check username/password", color=(255, 0, 0))

    def onCancel(self, event):
        self.Destroy()

    def updateStatus(self, status, color=(0, 0, 0)):
        self.status.SetLabel(status)
        self.status.SetForegroundColour(color)  # set text color
        self.main_sizer.Fit(self)
        self.Update()


class BaseFrame(wx.Frame):
    def makeFileMenu(self):
        # ---_file---#000000#FFFFFF-------------------------------------------
        fileMenu = wx.Menu()
        app = wx.GetApp()
        keyCodes = app.keys

        # add items to file menu
        fileMenu.Append(wx.ID_CLOSE,
                        _translate("&Close View\t%s") % keyCodes['close'],
                        _translate("Close current window"))
        wx.EVT_MENU(self, wx.ID_CLOSE, self.closeFrame)
        # -------------quit
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT,
                        _translate("&Quit\t%s") % keyCodes['quit'],
                        _translate("Terminate the program"))
        wx.EVT_MENU(self, wx.ID_EXIT, app.quit)
        return fileMenu

    def closeFrame(self, event=None, checkSave=True):
        self.Destroy()


class SearchFrame(BaseFrame):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        title = "Search OSF (Open Science Framework)"
        self.frameType = 'OSFsearch'
        wx.Frame.__init__(self, None, -1, title, pos, size, style)
        self.app = app
        self.currentProject = None

        # set up menu bar
        menuBar = wx.MenuBar()
        self.fileMenu = self.makeFileMenu()
        menuBar.Append(self.fileMenu, _translate('&File'))
        self.SetMenuBar(menuBar)

        # to show detail of current selection
        self.detailsPanel = DetailsPanel(parent=self)

        # create list of my projects (no search?)
        self.myProjectsPanel = ProjectListPanel(self, self.detailsPanel)

        # create list of searchable public projects
        self.publicProjectsPanel = ProjectListPanel(self, self.detailsPanel)
        self.publicProjectsPanel.setContents('')

        # sizers: on the left we have search boxes
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.StaticText(self, -1, "My Projects"),
                      flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(self.myProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, -1, "Search Public:"))
        self.searchTextCtrl = wx.TextCtrl(self, -1, "",
                                          style=wx.TE_PROCESS_ENTER)
        self.searchTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        searchSizer.Add(self.searchTextCtrl, flag=wx.EXPAND)
        leftSizer.Add(searchSizer)
        tagsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagsSizer.Add(wx.StaticText(self, -1, "Tags:"))
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
        rightSizer.Add(wx.StaticText(self, -1, "Project Info"),
                       flag=wx.ALL,
                       border=5)
        self.syncButton = wx.Button(self, -1, "Sync...")
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
        if self.currentProject is None:
            raise AttributeError("User pressed the sync button with no "
                                 "searchDlg.currentProject existing. "
                                 "Ask them how they managed that!")
        syncFrame = ProjectSyncFrame(parent=self.app, id=-1,
                                     title=self.currentProject.title)
        syncFrame.setOSFproject(self.currentProject)
        self.Close()  # we're going over to the sync window

    def updateUserProjs(self):
        if self.app.osf_session.user_id is None:
            self.myProjectsPanel.setContents(
                "No user logged in. \n\n"
                "Go to menu item Projects>Users>")
        else:
            self.myProjectsPanel.setContents(
                "Searching projects for user {} ..."
                .format(self.app.osf_session.username))
            self.Update()
            wx.Yield()
            myProjs = self.app.osf_session.find_user_projects()
            self.myProjectsPanel.setContents(myProjs)

    def onSearch(self, evt):
        searchStr = self.searchTextCtrl.GetValue()
        tagsStr = self.tagsTextCtrl.GetValue()
        session = self.app.osf_session
        self.publicProjectsPanel.setContents("searching...")
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

        if type(projects) in [str, unicode]:
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
            self.parent.currentProject = proj
        else:
            self.parent.syncButton.Enable(False)
            self.parent.currentProject = None


class DetailsPanel(richtext.RichTextCtrl):

    def __init__(self, parent, style=wx.VSCROLL | wx.NO_BORDER):
        richtext.RichTextCtrl.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.app = self.parent.app
        self.currentProjID = None

        try:
            Style = richtext.TextAttrEx
        except AttributeError:
            Style = richtext.RichTextAttr

        # style for urls in the text (and bind to method)
        self.urlStyle = Style()
        self.urlStyle.SetTextColour(wx.BLUE)
        self.urlStyle.SetFontUnderlined(True)
        self.Bind(wx.EVT_TEXT_URL, self.OnURL)

        # style for headings
        self.h1 = Style()
        self.h1.SetFontSize(18)
        self.h1.SetFontWeight(2)

    def setProject(self, project):
        self.Clear()

        if project is None:
            return  # we're done

        self.BeginStyle(self.h1)
        self.WriteText(project.title)
        self.EndStyle()

        self.Newline()
        self.BeginBold()
        self.WriteText("URL: ")
        self.EndBold()
        self.BeginStyle(self.urlStyle)
        self.BeginURL(url="https://osf.io/{}".format(project.id))
        self.WriteText("https://osf.io/{}".format(project.id))
        self.EndURL()
        self.EndStyle()

        self.Newline()
        self.BeginBold()
        self.WriteText("Tags: ")
        self.EndBold()
        self.WriteText(", ".join(project.attributes['tags']))

        self.Newline()
        self.BeginBold()
        self.WriteText("Visibility: ")
        self.EndBold()
        if project.attributes['public'] is True:
            visib = "Public"
        else:
            visib = "Private"
        self.WriteText(visib)

        # todo: could add various info here. Is this a fork? What are dates?
        # more info in project.attributes
        # Could also add authors, but that a session.request.get()

        self.Newline()
        self.Newline()

        if project.attributes['description']:
            self.WriteText(project.attributes['description'])

        # store this ID to keep track of the current project
        self.currentProj = project

    def OnURL(self, evt):
        self.app.followLink(url=evt.GetString())


class ProjectSyncFrame(BaseFrame):

    def __init__(self, parent, id, size=(600, 300), *args, **kwargs):
        wx.Frame.__init__(self, parent=None, id=id, size=size, *args, **kwargs)
        self.frameType = 'project'
        self.app = wx.GetApp()
        self.OSFproject = None
        self.syncStatus = None

        menuBar = wx.MenuBar()
        self.fileMenu = self.makeFileMenu()
        menuBar.Append(self.fileMenu, _translate('&File'))
        self.SetMenuBar(menuBar)

        # title
        self.title = wx.StaticText(self, -1, "No project opened",
                                   style=wx.BOLD | wx.ALIGN_CENTER)
        font = wx.Font(18, family=wx.NORMAL, style=wx.NORMAL, weight=wx.BOLD)
        self.title.SetFont(font)
        self.title.SetMinSize((400, -1))
        self.title.Wrap(400)

        # project definition
        projFileSizer = wx.BoxSizer(wx.HORIZONTAL)
        projFileLabel = wx.StaticText(self, -1, "Project file:")
        self.projFilePath = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        projFileBrowseBtn = wx.Button(self, -1, "Browse...")
        projFileBrowseBtn.Bind(wx.EVT_BUTTON, self.onBrowseProjFile)
        projFileSizer.Add(projFileLabel, flag=wx.ALL, border=5)
        projFileSizer.Add(self.projFilePath,
                          flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        projFileSizer.Add(projFileBrowseBtn, flag=wx.ALL, border=5)

        # remote files
        remoteSizer = wx.BoxSizer(wx.HORIZONTAL)
        remoteLabel = wx.StaticText(self, -1, "Remote project:")
        self.remoteURL = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        remoteSizer.Add(remoteLabel, flag=wx.ALL, border=5)
        remoteSizer.Add(self.remoteURL,
                        flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        # local files
        localSizer = wx.BoxSizer(wx.HORIZONTAL)
        localLabel = wx.StaticText(self, -1, "Local files:")
        self.localPath = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        localBrowseBtn = wx.Button(self, -1, "Browse...")
        localBrowseBtn.Bind(wx.EVT_BUTTON, self.onBrowseLocal)
        localSizer.Add(localLabel, flag=wx.ALL, border=5)
        localSizer.Add(self.localPath,
                       flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        localSizer.Add(localBrowseBtn, flag=wx.ALL, border=5)

        # sync controls
        self.syncButton = wx.Button(self, -1, "Sync Now")
        self.syncButton.Bind(wx.EVT_BUTTON, self.onSyncBtn)
        self.status = wx.StaticText(self, -1, "")

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.title,
                           flag=wx.EXPAND | wx.ALL, border=5)
        self.mainSizer.Add(projFileSizer,
                           flag=wx.EXPAND | wx.ALL, border=5)
        self.mainSizer.Add(remoteSizer,
                           flag=wx.EXPAND | wx.ALL, border=5)
        self.mainSizer.Add(localSizer,
                           flag=wx.EXPAND | wx.ALL, border=5)
        # sync controls

        self.mainSizer.Add(wx.StaticLine(self, -1),
                           flag=wx.EXPAND | wx.ALL, border=20)
        self.mainSizer.Add(self.syncButton,
                           flag=wx.EXPAND | wx.ALL, border=5)
        self.mainSizer.Add(self.status,
                           flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizerAndFit(self.mainSizer)
        self.SetAutoLayout(True)
        self.update()

        self.app.trackFrame(self)
        self.Show()

    def loadProjectFile(self, filepath):
        project = pyosf.Project(project_file=filepath)
        self.localPath.SetValue(project.root_path)
        if project.osf:
            self.setOSFproject(project.osf)
        self.project = project
        self.update()

    def setOSFproject(self, OSFproject):
        self.OSFproject = OSFproject
        self.title.SetLabel(OSFproject.title)
        self.remoteURL.SetValue("https://osf.io/{}".format(OSFproject.id))
        self.update()

    def onBrowseLocal(self, evt):
        dlg = wx.DirDialog(self, message=("Root folder of your local files"))
        if dlg.ShowModal() == wx.ID_OK:
            self.localPath.SetValue(dlg.GetPath())
        self.update()

    def onBrowseProjFile(self, evt):
        dlg = wx.FileDialog(self,
                            message=("File to store project info"),
                            style=wx.FD_SAVE,
                            wildcard="Project files (*.psyproj)|*.psyproj")
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            if not newPath.endswith(".psyproj"):
                newPath += ".psyproj"
            self.projFilePath.SetValue(newPath)
        # try to set this project file
        self.setProjFile(newPath)

    def setProjFile(self, projFile):
        """Set the path of the project file. If this loads successfully
        then the project root and OSF project ID will also be updated
        """
        if os.path.isfile(projFile):
            self.projFilePath.SetValue(projFile)
            project = pyosf.Project(project_file=projFile)
            # check this is the same project!
            if self.OSFproject and project.osf.id != self.OSFproject.id:
                raise IOError("The project file relates to a different"
                              "OSF project and cannot be used for this one")
            self.localPath.SetValue(project.root_path)
            if project.osf:
                self.setOSFproject(project.osf)
            self.project = project
        self.update()

    def onSyncBtn(self, evt):
        self.project = pyosf.Project(project_file=self.projFilePath.GetValue(),
                                     root_path=self.localPath.GetValue(),
                                     osf=self.OSFproject)
        # create or reset progress indicators
        if self.syncStatus is None:
            self.syncStatus = SyncStatusPanel(parent=self, id=-1,
                                              project=self.project)
            self.mainSizer.Add(self.syncStatus,
                               flag=wx.ALIGN_CENTER | wx.EXPAND | wx.ALL,
                               border=5)
            self.mainSizer.Fit(self)
        else:
            self.syncStatus.reset()

        self.update(status="Checking for changes")
        wx.Yield()
        changes = self.project.get_changes()
        self.update(status="Applying changes")
        wx.Yield()  # give wx a moment to breath
        # start the threads up/downloading
        changes.apply(threaded=True)
        # to check the status we need the
        while True:
            progress = changes.progress
            if progress == 1:
                self.update("Sync complete")
                changes.finish_sync()
                self.project.save()
                # get rid of progress markers
                self.syncStatus.Destroy()
                self.syncStatus = None
                break
            else:
                self.syncStatus.setProgress(progress)

    def update(self, status=None):
        """Update to a particular status if given or deduce status msg if not
        """
        if status is None:
            if not self.OSFproject:
                status = "No remote project set"
                self.syncButton.Enable(False)
            elif not self.localPath or not self.localPath.GetValue():
                status = "No local folder to sync with"
                self.syncButton.Enable(False)
            else:
                status = "Ready"
                self.syncButton.Enable(True)
        self.status.SetLabel("Status: " + status)
        self.Layout()
        self.Update()


class SyncStatusPanel(wx.Panel):
    def __init__(self, parent, id, project, *args, **kwargs):
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        self.project = project
        self.sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        self.sizer.AddGrowableCol(1)

        upLabel = wx.StaticText(self, -1, "Uploading:")
        self.upProg = wx.Gauge(self, -1, range=1, size=(200, -1))
        downLabel = wx.StaticText(self, -1, "Downloading:")
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
        upDone, upTot = progress['up']
        downDone, downTot = progress['down']
        if upTot == 0:
            self.upProg.SetRange(1)
            self.upProg.SetValue(1)
        else:
            self.upProg.SetRange(upTot)
            self.upProg.SetValue(upDone)
        if downTot == 0:
            self.downProg.SetRange(1)
            self.downProg.SetValue(1)
        else:
            self.downProg.SetRange(downTot)
            self.downProg.SetValue(downDone)
        self.Update()
        wx.Yield()
        time.sleep(0.1)
