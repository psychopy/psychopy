import wx

from os.path import join
from .. import icons
from .project import syncProject, ProjectFrame
from .search import SearchFrame
from .user import UserEditor

from psychopy.localization import _translate


class PavloviaButtons:

    def __init__(self, frame, toolbar, tbSize):
        self.frame = frame
        self.toolbar = toolbar
        self.tbSize = tbSize
        self.btnHandles = {}

    def addPavloviaTools(self, buttons=[]):
        rc = self.frame.app.prefs.paths['resources']

        info = {}
        info['pavloviaRun'] = {
            'emblem': 'run16.png',
            'func': self.frame.onPavloviaRun,
            'label': _translate('Run online'),
            'tip': _translate('Run the study online (with pavlovia.org)')}
        info['pavloviaSync'] = {
            'emblem': 'sync_green16.png',
            'func': self.frame.onPavloviaSync,
            'label': _translate('Sync online'),
            'tip': _translate('Sync with web project (at pavlovia.org)')}
        info['pavloviaSearch'] = {
            'emblem': 'magnifier16.png',
            'func': self.onPavloviaSearch,
            'label': _translate('Search Pavlovia.org'),
            'tip': _translate('Find existing studies online (at pavlovia.org)')}
        info['pavloviaUser'] = {
            'emblem': 'user22.png',
            'func': self.onPavloviaUser,
            'label': _translate('Log in to Pavlovia'),
            'tip': _translate('Log in to (or create user at) Pavlovia.org')}
        info['pavloviaProject'] = {
            'emblem': 'info16.png',
            'func': self.onPavloviaProject,
            'label': _translate('View project'),
            'tip': _translate('View details of this project')}

        if not buttons:  # allows panels to select subsets
            buttons = info.keys()

        for buttonName in buttons:
            emblem = info[buttonName]['emblem']
            btnFunc = info[buttonName]['func']
            label = info[buttonName]['label']
            tip = info[buttonName]['tip']
            btnImage = icons.combineImageEmblem(
                    main=join(rc, 'globe%i.png' % self.tbSize),
                    emblem=join(rc, emblem), pos='bottom_right')

            if 'phoenix' in wx.PlatformInfo:
                self.btnHandles[buttonName] = self.toolbar.AddTool(
                        wx.ID_ANY, label, btnImage, tip)
            else:
                self.btnHandles[buttonName] = self.toolbar.AddSimpleTool(
                        wx.ID_ANY, btnImage, label, tip)

            self.toolbar.Bind(wx.EVT_TOOL, btnFunc, self.btnHandles[buttonName])

    def onPavloviaSync(self, evt=None):
        syncProject(parent=self.frame, project=self.frame.project)

    def onPavloviaRun(self, evt=None):
        if self.frame.project:
            self.frame.project.pavloviaStatus = 'ACTIVATED'
            url = "https://run.pavlovia.org/{}/html".format(
                    self.frame.project.id)
            wx.LaunchDefaultBrowser(url)

    def onPavloviaUser(self, evt=None):
        userDlg = UserEditor()
        if userDlg.user:
            userDlg.ShowModal()
        else:
            userDlg.Destroy()

    def onPavloviaSearch(self, evt=None):
        searchDlg = SearchFrame(
                app=self.frame.app, parent=self.frame,
                pos=self.frame.GetPosition())
        searchDlg.Show()

    def onPavloviaProject(self, evt=None):
        dlg = ProjectFrame(app=self.frame.app, project=self.frame.project)
        dlg.Show()

        # if self.frame.project:
        #     self.frame.project.pavloviaStatus = 'ACTIVATED'
        #     url = "https://pavlovia.org/run/{}/html".format(
        #         self.frame.project.id)
        #     wx.LaunchDefaultBrowser(url)
