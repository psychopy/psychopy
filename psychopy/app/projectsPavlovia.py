#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import os
import time
import wx
import wx.html2
import wx.lib.scrolledpanel as scrlpanel
from past.builtins import basestring

import git
import gitlab

try:
    import wx.adv as wxhl  # in wx 4
except ImportError:
    wxhl = wx  # in wx 3.0.2

from psychopy import logging, web, prefs
from psychopy.app import dialogs
from psychopy.projects import projectCatalog, projectsFolder, pavlovia
from psychopy.localization import _translate

# Done: add+commit before push
# Done:  add .gitignore file. Added when opening a repo without one
# TODO: user dlg could/should be local not a browser
# TODO: if more than one remote then offer options
# TODO: after clone, remember this folder for next file-open call
# TODO: fork+sync doesn't yet fork the project first
#



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

        PavloviaMenu.knownUsers = pavlovia.knownUsers

        # sub-menu for usernames and login
        self.userMenu = wx.Menu()
        # if a user was previously logged in then set them as current
        lastPavUser = PavloviaMenu.appData['pavloviaUser']
        if lastPavUser not in pavlovia.knownUsers:
            lastPavUser = None
        if lastPavUser and not PavloviaMenu.currentUser:
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
        if user in pavlovia.knownUsers:
            token = pavlovia.knownUsers[user]
            pavlovia.currentSession.setToken(token)
        else:
            self.onLogInPavlovia()

        if self.searchDlg:
            self.searchDlg.updateUserProjs()

    def onSync(self, event):
        pass  # TODO: create quick-sync from menu item

    def onSearch(self, event):
        PavloviaMenu.searchDlg = SearchFrame(app=self.parent.app)
        PavloviaMenu.searchDlg.Show()

    def onLogInPavlovia(self, event=None):
        logInPavlovia(parent=self.parent)

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
    """This class is used by to open the login (browser) window for pavlovia.org
    """
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
        url = event.GetURL()
        if 'access_token=' in url:
            self.tokenInfo['token'] = self.getParamFromURL(
                    'access_token', url)
            self.tokenInfo['tokenType'] = self.getParamFromURL(
                    'token_type', url)
            self.tokenInfo['state'] = self.getParamFromURL(
                    'state', url)
            self.EndModal(wx.ID_OK)
        else:
            logging.info("OAuthBrowser.onNewURL:", url)

    def getParamFromURL(self, paramName, url=None):
        """Takes a url and returns the named param"""
        if url is None:
            url = self.browser.GetCurrentURL()
        return url.split(paramName + '=')[1].split('&')[0]


class PavloviaMiniBrowser(wx.Dialog):
    """This class is used by to open an internal browser for the user stuff
    """
    def __init__(self, parent, user=None, *args, **kwargs):
        # check there is a user (or log them in)
        if not user:
            user = pavlovia.currentSession.user
        if not user:
            user = logInPavlovia(parent=parent)
        if not user:
            return None
        self.user = user
        # create the dialog
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, style=style, *args, **kwargs)
        # create browser window for authentication
        self.browser = wx.html2.WebView.New(self)

        # do layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)
        self.SetSize((700, 700))

    def setURL(self, url):
        self.browser.LoadURL(url)

    def gotoUserPage(self):
        url = self.user.attributes['web_url']
        self.browser.LoadURL(url)

    def gotoProjects(self):
        self.browser.LoadURL("https://pavlovia.org/projects.html")


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
        self.project = None

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

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(leftSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.mainSizer.Add(self.detailsPanel, flag=wx.EXPAND, proportion=1,
                           border=5)
        self.SetSizerAndFit(self.mainSizer)

        aTable = wx.AcceleratorTable([(0, wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      ])
        self.SetAcceleratorTable(aTable)
        self.Show()  # show the window before doing search/updates
        self.updateUserProjs()  # update the info in myProjectsPanel

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
        self.project = proj


class DetailsPanel(scrlpanel.ScrolledPanel):

    def __init__(self, parent, noTitle=False,
                 style=wx.VSCROLL | wx.NO_BORDER):
        scrlpanel.ScrolledPanel.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.app = self.parent.app
        self.project = {}
        self.noTitle = noTitle

        # self.syncPanel = SyncStatusPanel(parent=self, id=wx.ID_ANY)
        # self.syncPanel.Hide()

        if not noTitle:
            self.title = wx.StaticText(parent=self, id=-1,
                                       label="", style=wx.ALIGN_CENTER)
            font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            self.title.SetFont(font)

        # if we've synced before we should know the local location
        self.localFolder = wx.StaticText(
                parent=self, id=-1,
                label="Local root: ")
        self.browseLocalBtn = wx.Button(self, wx.ID_ANY, "Browse...")
        self.browseLocalBtn.Bind(wx.EVT_BUTTON, self.onBrowseLocalFolder)

        # remote attributes
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
        localFolderSizer.Add(self.localFolder, border=5,
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

    def setProject(self, project):
        if not isinstance(project, pavlovia.PavloviaProject):
            # e.g. '382' or 382
            project = pavlovia.currentSession.getProject(project)
        if project is None:
            return  # we're done
        self.project = project

        if not self.noTitle:
            self.title.SetLabel("{} / {}".format(project.owner, project.name))

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
        localFolder = project['local']
        if not localFolder:
            localFolder = "<not yet synced>"
        self.localFolder.SetLabel("Local root: {}".format(localFolder))

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
        if 'local' not in self.project or not self.project.localRoot:
            # we first need to choose a location for the repository
            newPath = setLocalPath(self, self.project)
            if newPath:
                self.localFolder.SetLabel(
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
        newPath = setLocalPath(self, self.project)
        if newPath:
            self.localFolder.SetLabel(
                    label="Local root: {}".format(newPath))
        self.Update()


class ProjectEditor(wx.Dialog):
    def __init__(self, parent=None, id=wx.ID_ANY, project=None, *args, **kwargs):

        wx.Dialog.__init__(self, parent, id,
                           *args, **kwargs)
        panel = wx.Panel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        # when a project is succesfully created these will be populated
        if hasattr(parent, 'filename'):
            self.filename = parent.filename
        else:
            self.filename = None
        self.project = project
        self.projInfo = None

        if project:
            # edit existing project
            self.isNew = False
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
        self.localBox = wx.TextCtrl(panel, -1, size=(400, -1))
        self.btnLocalBrowse = wx.Button(self, wx.ID_ANY, "Browse...")
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

        # do layout
        mainSizer = wx.FlexGridSizer(cols=2, rows=6, vgap=5, hgap=5)
        mainSizer.AddMany([(nameLabel, 0, wx.ALIGN_RIGHT), self.nameBox,
                           (localLabel, 0, wx.ALIGN_RIGHT), localPathSizer,
                           (descrLabel, 0, wx.ALIGN_RIGHT), self.descrBox,
                           (tagsLabel, 0, wx.ALIGN_RIGHT), self.tagsBox,
                           (publicLabel, 0, wx.ALIGN_RIGHT), self.publicBox,
                           (updateBtn, 0, wx.ALIGN_RIGHT)])
        border = wx.BoxSizer()
        border.Add(mainSizer, 0, wx.ALL, 10)
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

        # then create/update
        if self.isNew:
            project = session.createProject(name=name,
                                            description=descr,
                                            tags=tags,
                                            visibility=visibility)
            project.localRoot = self.localBox.GetLabel()
            self.project = project
            self.project.sync()
        else:  # to be done
            self.project.pavlovia.name = name
            self.project.pavlovia.description = descr
            self.project.tags = tags
            self.project.visibility=visibility
            self.project.save()

        self.EndModal(wx.ID_OK)

    def onBrowseLocal(self, evt=None):
        newPath = setLocalPath(self, path=self.filename)
        if newPath:
            self.localBox.SetLabel(newPath)

class SyncFrame(wx.Frame):
    def __init__(self, parent, id, project):
        title = "{} / {}".format(project.owner, project.title)
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        wx.Frame.__init__(self, parent=None, id=id, style=style,
                          title=title)
        self.parent = parent
        self.project = project

        # create the sync panel and start sync(!)
        self.syncPanel = SyncStatusPanel(parent=self, id=wx.ID_ANY)
        self.progHandler = ProgressHandler(syncPanel=self.syncPanel)
        self.Fit()
        self.Show()
        wx.Yield()


class SyncStatusPanel(wx.Panel):
    def __init__(self, parent, id, size=(300, 250), *args, **kwargs):
        # init super classes
        wx.Panel.__init__(self, parent, id, size=size, *args, **kwargs)
        # set self properties
        self.parent = parent
        self.statusMsg = wx.StaticText(self, -1, "Synchronising...")
        self.progBar = wx.Gauge(self, -1, range=1, size=(200, -1))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.statusMsg, 1, wx.ALL | wx.CENTER, border=10)
        self.mainSizer.Add(self.progBar, 1, wx.ALL | wx.CENTER, border=10)
        self.SetSizerAndFit(self.mainSizer)

        self.SetAutoLayout(True)
        self.Layout()

    def reset(self):
        self.progBar.SetRange(1)
        self.progBar.SetValue(0)

    def setStatus(self, status):
        self.statusMsg.SetLabel(status)
        self.Update()
        self.Layout()
        wx.Yield()


class ProgressHandler(git.remote.RemoteProgress):
    """We can't override the update() method so we have to create our own
    subclass for this"""

    def __init__(self, syncPanel, *args, **kwargs):
        git.remote.RemoteProgress.__init__(self, *args, **kwargs)
        self.syncPanel = syncPanel
        self.frame = syncPanel.parent
        self.t0 = None

    def setStatus(self, msg):
        self.syncPanel.statusMsg.SetLabel(msg)

    def update(self, op_code=0, cur_count=1, max_count=None, message=''):
        """Update the statusMsg and progBar for the syncPanel
        """
        if not self.t0:
            self.t0 = time.time()
        if op_code in ['10', 10]:  # indicates complete
            label = "Successfully synced"
        else:
            label = self._cur_line.split(':')[1]
            # logging.info("{:.5f}: {}"
            #              .format(time.time() - self.t0, self._cur_line))
            label = self._cur_line
        self.setStatus(label)
        try:
            maxCount = int(max_count)
        except:
            maxCount = 1
        try:
            currCount = int(cur_count)
        except:
            currCount = 1

        self.syncPanel.progBar.SetRange(maxCount)
        self.syncPanel.progBar.SetValue(currCount)
        self.syncPanel.Update()
        self.syncPanel.mainSizer.Layout()
        wx.Yield()
        time.sleep(0.001)


def setLocalPath(parent, project=None, path=""):
    """Open a DirDialog and set the project local folder to that specified

    Returns
    ----------

    None for no change and newPath if this has changed from previous
    """
    if path:
        origPath = path
    elif project and 'local' in project:
        origPath = project.local
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
    info = {}
    url, state = pavlovia.getAuthURL()
    dlg = OAuthBrowserDlg(parent, url, info=info)
    dlg.ShowModal()
    if info and state == info['state']:
        token = info['token']
        pavlovia.login(token)
        return pavlovia.currentSession.user


def syncPavlovia(parent, project=None):
    """A function to sync the current project (if there is one)
    """
    if not project:  # try getting one from the frame
        project = parent.project

    if not project:  # ask the user to create one
        msg = ("This file doesn't belong to any existing project.")
        style = wx.OK | wx.CANCEL | wx.CENTER
        dlg = wx.MessageDialog(parent=parent, message=msg, style=style)
        dlg.SetOKLabel("Create a project")
        if dlg.ShowModal()==wx.ID_OK:
            project = createProject(parent=parent)

    if not project: # we did our best for them. Give up!
        return 0

    # if project.localRoot doesn't exist, or is empty
    if 'local' not in project or not project.localRoot:
        # we first need to choose a location for the repository
        setLocalPath(parent, project)
    if not project.repo:
        project.getRepo()

    # check for anything to commit before pull/push
    outcome = showCommitDialog(parent, project)

    syncFrame = SyncFrame(parent=parent, id=wx.ID_ANY, project=project)
    wx.Yield()
    project.sync(syncFrame.syncPanel, syncFrame.progHandler)
    syncFrame.Destroy()

    return 1

def showCommitDialog(parent, project):
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
    commitTitleCtrl = wx.TextCtrl(dlg, size=(500, -1))
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

def createProject(parent):
    """Opens a dialog to create a new project

    Parameters
    ----------
    parent

    Returns
    -------

    """
    editor = ProjectEditor(parent=parent)
    editor.ShowModal()
    # while not editor.finished:  # doesn't have ShowModal (Frame not Dialog)
    #     time.sleep(0.01)

