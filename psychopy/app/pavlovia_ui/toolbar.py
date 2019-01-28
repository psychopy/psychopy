import wx

from os.path import join
from .. import icons
from .project import syncProject
from .search import SearchFrame
from .user import UserEditor

class PavloviaButtons:

    def __init__(self, frame, toolbar, tbSize):
        self.frame = frame
        self.toolbar = toolbar
        self.tbSize = tbSize
        self.btnHandles = {}

    def addPavloviaTools(self, buttons=['sync', 'run', 'search', 'user']):
        rc = self.frame.app.prefs.paths['resources']

        info={}
        info['pavloviaRun'] = {'emblem': 'run16.png', 'func': self.frame.onPavloviaRun}  # Set to frame method
        info['pavloviaSync'] = {'emblem': 'sync_green16.png', 'func': self.frame.onPavloviaSync}  # Set to frame method
        info['pavloviaSearch'] = {'emblem': 'magnifier16.png', 'func': self.onPavloviaSearch}
        info['pavloviaUser'] = {'emblem': 'user22.png', 'func': self.onPavloviaUser}

        for buttonName in buttons:
            emblem = info[buttonName]['emblem']
            btnFunc = info[buttonName]['func']

            if 'phoenix' in wx.PlatformInfo:
                self.btnHandles[buttonName] = self.toolbar.AddTool(
                    wx.ID_ANY,
                    '',
                    icons.combineImageEmblem(
                        main=join(rc, 'globe%i.png' % self.tbSize),
                        emblem=join(rc, emblem), pos='bottom_right'))
            else:
                self.btnHandles[buttonName] = self.toolbar.AddSimpleTool(
                    wx.ID_ANY,
                    icons.combineImageEmblem(
                        main=join(rc, 'globe%i.png' % self.tbSize),
                        emblem=join(rc, emblem), pos='bottom_right'))
            self.toolbar.Bind(wx.EVT_TOOL, btnFunc, self.btnHandles[buttonName])

    def onPavloviaSync(self, evt=None):
        syncProject(parent=self.frame, project=self.frame.project)

    def onPavloviaRun(self, evt=None):
        if self.frame.project:
            self.frame.project.pavloviaStatus = 'ACTIVATED'
            url = "https://pavlovia.org/run/{}/html".format(self.frame.project.id)
            wx.LaunchDefaultBrowser(url)

    def onPavloviaUser(self, evt=None):
        userDlg = UserEditor()
        if userDlg.user:
            userDlg.ShowModal()
        else:
            userDlg.Destroy()

    def onPavloviaSearch(self, evt=None):
        searchDlg = SearchFrame(
            app=self.frame.app, parent=self.frame, pos=self.frame.GetPosition())
        searchDlg.Show()
