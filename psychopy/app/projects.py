# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

import os
import time
import wx
import wx.lib.scrolledpanel as scrlpanel
from wx import richtext

from . import wxIDs
from psychopy import logging, web, prefs
from psychopy.app import dialogs
from .localization import _translate
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

usersList = wx.FileHistory(maxFiles=10, idBase=wx.NewId())


class ProjectCatalog(dict):
    """Handles info about known project files (either in project history or in
    the ~/.psychopy/projects folder).
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.refresh()

    def projFromId(self, id):
        for key, item in self.items():
            if item.id == id:
                return key, item

    def projFromName(self, name):
        for key, item in self.items():
            if item.name == name:
                return key, item

    def refresh(self):
        """Search the locations and update the catalog
        """
        # prev used files
        projFiles = set(prefs.appData['projects']['fileHistory'])
        rootPath = os.path.join(prefs.paths['userPrefsDir'], 'projects')
        projFiles.update(glob.glob(rootPath+"/*.proj"))  # like list extend
        self.dict = {}
        for filePath in projFiles:
            thisProj = pyosf.Project(projFile)  # load proj file
            if hasattr(thisProj, 'name'):
                name = thisProj.name
                key = "%s: %s" % (thisProj.id, thisProj.name)
            else:
                name = thisProj.id
                key = "%s: n/a" % (thisProj.id)
            self.dict[key] = thisProj

projectCatalog = ProjectCatalog()

# Projects FileHistory sub-menu
idBase = wx.NewId()
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

        # new
        self.Append(wxIDs.projsNew,
                    "New...\t{}".format(keys['projectsNew']))
        wx.EVT_MENU(parent, wxIDs.projsNew,  self.onNew)

        # self.Append(wxIDs.projsSync, "Sync\t{}".format(keys['projectsSync']))
        # wx.EVT_MENU(parent, wxIDs.projsSync,  self.onSync)

    def addToSubMenu(self, name, menu, function):
        thisId = wx.NewId()
        menu.Append(thisId, name)
        wx.EVT_MENU(self.parent, thisId, function)

    def addFileToHistory(self, filename):
        self.projHistory.AddFileToHistory(filename)

    def onProjFromHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - self.projHistory.idBase
        projName = self.projHistory.GetHistoryFile(fileNum)
        projPath =
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
        try:
            self.app.osf_session = pyosf.Session(user)
        except pyosf.AuthError:
            print("failed to authenticate - probably need 2FA")
        except requests.exceptions.ConnectionError:
            logging.warn("Connection error trying to connect to pyosf")
        ProjectsMenu.appData['user'] = user
        if self.searchDlg is not None:
            self.searchDlg.updateUserProjs()

    # def onSync(self, event):
    #    logging.info("")
    #    pass  # TODO: create quick-sync from menu item

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

    def onNew(self, event):
        """Create a new project for OSF
        """
        if self.app.osf_session.user_id:
            projEditor = ProjectEditor()
            projEditor.Show()
            if projEditor.OSFproj:  # exists if all worked
                projInfo = projEditor.projInfo
                projFrame = ProjectFrame(parent=self.app, id=-1,
                                         title=projInfo['title'])
                projFrame.setOSFproject(projEditor.OSFproj)

        else:
            infoDlg = dialogs.MessageDialog(parent=None, type='Info',
                                            message="You need to log in"
                                            " to create a project")
            infoDlg.Show()

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
        projFrame = ProjectFrame(parent=self.app, id=-1)
        projFrame.setProjFile(projFile)
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
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
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
        projFrame = ProjectFrame(parent=self.app, id=-1,
                                     title=self.currentProject.title)
        projFrame.setOSFproject(self.currentProject)
        self.Close()  # we're going over to the project window

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
        self.url = wx.HyperlinkCtrl(parent=self, id=-1,
                                    label="https://osf.io",
                                    style=wx.HL_ALIGN_LEFT,
                                    )
        self.description = wx.StaticText(parent=self, id=-1,
                                         label="Select a project for details")
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
        self.visibility.SetLabel("Visibility: {}".format(visib))
        tags = project.attributes['tags']
        while None in tags:
            tags.remove(None)
        self.tags.SetLabel("Tags: "+", ".join(tags))

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
        self.OSFproject = None  # updates with loadProjectFile
        self.project = None
        self.syncStatus = None

        # title
        self.title = wx.StaticText(self, -1, "No project opened",
                                   style=wx.BOLD | wx.ALIGN_CENTER)
        font = wx.Font(18, family=wx.NORMAL, style=wx.NORMAL, weight=wx.BOLD)
        self.title.SetFont(font)
        self.title.SetMinSize((300, -1))
        self.title.Wrap(300)
        # local files
        localSizer = wx.BoxSizer(wx.HORIZONTAL)
        localLabel = wx.StaticText(self, -1, "Local files:")
        self.localPath = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        localBrowseBtn = wx.Button(self, -1, "Browse...")
        localBrowseBtn.Bind(wx.EVT_BUTTON, self.onBrowseLocal)
        # layout
        localSizer.Add(localLabel, flag=wx.ALL, border=5)
        localSizer.Add(self.localPath,
                       flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        localSizer.Add(localBrowseBtn, flag=wx.ALL, border=5)

        # sync controls
        self.syncButton = wx.Button(self, -1, "Sync Now")
        self.syncButton.Bind(wx.EVT_BUTTON, self.onSyncBtn)
        self.syncStatus = SyncStatusPanel(parent=self, id=-1,
                                          project=self.project)
        self.status = wx.StaticText(self, -1, "put status updates here")

        self.projDetails = DetailsPanel(parent=self, noTitle=True)

        # mainSizer with title, then two columns
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.title, flag=wx.ALL | wx.EXPAND,
                           proportion=1, border=5)
        self.mainSizer.Add(wx.StaticLine(self, -1), flag=wx.ALL,
                           proportion=1, border=20)

        # set contents for left and right sizers
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(self.projDetails, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=5)
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(localSizer, flag=wx.EXPAND | wx.ALL,
                       proportion=1, border=5)
        rightSizer.Add(self.syncButton, flag=wx.EXPAND | wx.ALL,
                       proportion=1, border=5)
        rightSizer.Add(self.syncStatus, flag=wx.EXPAND | wx.ALL,
                       proportion=1, border=5)
        rightSizer.Add(self.status, flag=wx.EXPAND | wx.ALL,
                       proportion=1, border=5)

        columnSizer = wx.BoxSizer(wx.HORIZONTAL)
        columnSizer.Add(leftSizer, border=5,
                        flag=wx.EXPAND | wx.ALL, proportion=2)
        columnSizer.Add(rightSizer, border=5,
                        flag=wx.EXPAND | wx.ALL, proportion=1)
        self.mainSizer.Add(columnSizer,
                           flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(self.mainSizer)
        self.SetAutoLayout(True)
        self.update()

        self.app.trackFrame(self)
        self.Show()

    def loadProjectFile(self, filepath):
        self.project = pyosf.Project(project_file=filepath)
        self.projFilePath = filepath
        if self.project.osf:
            self.setOSFproject(self.project.osf)
        self.project = project
        self.update()

    def setOSFproject(self, OSFproject):
        """This is run when we get a project from the search dialog (rather
        than from a previously loaded project file)
        """
        self.OSFproject = OSFproject
        self.title.SetLabel(OSFproject.title)
        self.projDetails.setProject(OSFproject)
        self.update()

    def onBrowseLocal(self, evt):
        dlg = wx.DirDialog(self, message=("Root folder of your local files"))
        if dlg.ShowModal() == wx.ID_OK:
            self.localPath.SetValue(dlg.GetPath())
        self.update()

    def setProjFile(self, projFile):
        """Set the path of the project file. If this loads successfully
        then the project root and OSF project ID will also be updated
        """
        if os.path.isfile(projFile):
            self.projFilePath = projFile
            project = pyosf.Project(project_file=projFile)
            # check this is the same project !
            if self.OSFproject and project.osf.id != self.OSFproject.id:
                raise IOError("The project file relates to a different"
                              "OSF project and cannot be used for this one")
            self.localPath.SetValue(project.root_path)
            if project.osf:
                self.setOSFproject(project.osf)
            self.project = project
        self.update()

    def onSyncBtn(self, evt):
        # not sure the next line is needed - won't we have this by now?
        self.project = pyosf.Project(project_file=self.projFilePath,
                                     root_path=self.localPath.GetValue(),
                                     osf=self.OSFproject)
        # create or reset progress indicators
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


class ProjectEditor(BaseFrame):
    def __init__(self, parent=None, id=-1, projId="", *args, **kwargs):
        BaseFrame.__init__(self, None, -1, *args, **kwargs)
        panel = wx.Panel(self,-1,style=wx.TAB_TRAVERSAL)
        # when a project is succesffully created these will be populated
        self.osfProj = None
        self.projInfo = None

        if projId:
            # edit existing project
            self.isNew = False
        else:
            self.isNew = True

        # create the controls
        titleLabel = wx.StaticText(panel, -1, "Title:")
        self.titleBox = wx.TextCtrl(panel, -1, size=(400, -1))
        nameLabel = wx.StaticText(panel, -1, "Name \n(for local id):")
        self.nameBox = wx.TextCtrl(panel, -1, size=(400, -1))
        descrLabel = wx.StaticText(panel, -1, "Description:")
        self.descrBox = wx.TextCtrl(panel, -1, size=(400, 200),
                               style= wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        tagsLabel = wx.StaticText(panel, -1, "Tags (comma separated):")
        self.tagsBox = wx.TextCtrl(panel, -1, size=(400, 100),
                               style= wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        publicLabel = wx.StaticText(panel, -1, "Public:")
        self.publicBox = wx.CheckBox(panel, -1)
        # buttons
        if self.isNew:
            buttonMsg = "Create project on OSF"
        else:
            buttonMsg = "Submit changes to OSF"
        updateBtn = wx.Button(panel, -1, buttonMsg)
        updateBtn.Bind(wx.EVT_BUTTON, self.submitChanges)

        # do layout
        mainSizer = wx.FlexGridSizer(cols=2, rows=6, vgap=5, hgap=5)
        mainSizer.AddMany([(titleLabel, 0, wx.ALIGN_RIGHT), self.titleBox,
                           (nameLabel, 0, wx.ALIGN_RIGHT),
                           (self.nameBox, 0 wx.EXPAND),
                           (descrLabel, 0, wx.ALIGN_RIGHT), self.descrBox,
                           (tagsLabel, 0, wx.ALIGN_RIGHT), self.tagsBox,
                           (publicLabel, 0, wx.ALIGN_RIGHT), self.publicBox,
                           (0,0), (updateBtn, 0, wx.ALIGN_RIGHT)])
        border = wx.BoxSizer()
        border.Add(mainSizer, 0, wx.ALL, 10)
        panel.SetSizerAndFit(border)
        self.Fit()

    def submitChanges(self, evt=None):
        session = wx.GetApp().osf_session
        d={}
        d['title'] = self.titleBox.GetValue()
        d['name'] = self.name
        d['descr'] = self.descrBox.GetValue()
        d['public'] = self.publicBox.GetValue()
        # tags need splitting and then
        tagsList = self.tagsBox.GetValue().split(',')
        d['tags'] = []
        for thisTag in tagsList:
            d['tags'].append(thisTag.strip())
        if self.isNew:
            OSFproj = session.create_project(title=d['title'],
                                             descr=d['descr'],
                                             tags=d['tags'],
                                             public=d['public'])
        else:  # to be done
            OSFproj = session.update_project(id, title=d['title'],
                                             descr=d['descr'],
                                             tags=d['tags'],
                                             public=d['public'])
        self.OSFproj = OSFproj
        self.projInfo = d
        self.Destroy()  # kill the dialog


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
