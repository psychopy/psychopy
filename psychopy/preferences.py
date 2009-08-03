import wx, wx.stc
import os, sys, urllib
from shutil import copyfile
from psychopy import configobj, configobjValidate
from psychopy.app.keybindings import key_save, key_close, key_quit
#GET PATHS------------------
join = os.path.join

class Preferences:
    def __init__(self):
        self.prefsCfg=None#the config object for the preferences
        self.appDataCfg=None #the config object for the app data (users don't need to see)
        
        self.general=None
        self.coder=None
        self.builder=None
        self.connections=None        
        self.paths={}#this will remain a dictionary
        
        self.getPaths()
        self.loadAll()            
        
    def getPaths(self):
        #on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath= os.path.abspath(__file__)
        dirPsychoPy = os.path.split(thisFileAbsPath)[0]
        #paths to user settings
        if sys.platform=='win32':
            dirUserPrefs = join(os.environ['APPDATA'],'psychoy2') #the folder where the user cfg file is stored
        else:
            dirUserPrefs = join(os.environ['HOME'], '.psychopy2')
        #from the directory for preferences work out the path for preferences (incl filename)
        if not os.path.isdir(dirUserPrefs):
            os.makedirs(dirUserPrefs)
        #path to Resources (icons etc)
        dirApp = join(dirPsychoPy, 'app')
        if os.path.isdir(join(dirApp, 'Resources')):
            dirResources = join(dirApp, 'Resources')
        else:dirResources = dirApp
        
        self.paths['psychopy']=dirPsychoPy
        self.paths['appDir']=dirApp
        self.paths['appFile']=join(dirApp, 'PsychoPy.py')
        self.paths['demos'] = join(dirPsychoPy, 'demos')
        self.paths['resources']=dirResources
        self.paths['userPrefs']=dirUserPrefs
        self.paths['userPrefsFile']=join(dirUserPrefs, 'prefsUser.cfg')
        self.paths['appDataFile']=join(dirUserPrefs,'appData.cfg')
        self.paths['sitePrefsFile']=join(self.paths['psychopy'], 'sitePrefs.cfg')

    def loadAll(self):
        """A function to allow a class with attributes to be loaded from a 
        pickle file necessarily without having the same attribs (so additional 
        attribs can be added in future).
        """
        self._validator=configobjValidate.Validator()
        self.appDataCfg = self.loadAppData()
        self.prefsCfg = self.loadSitePrefs()
        self.userPrefsCfg = self.loadUserPrefs()
        self.userPrefsCfg.validate(self._validator, copy=True)#copy means all settings get saved
        #merge site prefs and user prefs
        self.prefsCfg.merge(self.userPrefsCfg)
        
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app'] 
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections'] 
        self.appData = self.appDataCfg

        #override some platfrom-specific settings
        if sys.platform=='darwin':
            self.prefsCfg['app']['allowImportModules']=False            
        #connections
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
    def saveAppData(self):
        """Save the various setting to the appropriate files (or discard, in some cases)
        """
        self.appDataCfg.validate(self._validator, copy=True)#copy means all settings get saved
        self.appDataCfg.write()
    def resetSitePrefs(self):
        """Reset the site preferences to the original defaults (to reset user prefs, just delete entries)
        """
        os.remove(self.paths['sitePrefsFile'])
    def loadAppData(self):
        #fetch appData too against a config spec
        appDataSpec = configobj.ConfigObj(join(self.paths['appDir'], 'appDataSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['appDataFile'], configspec=appDataSpec)
        cfg.validate(self._validator, copy=True)     
        return cfg   
    def loadSitePrefs(self):        
        #load against the spec, then validate and save to a file 
        #(this won't overwrite existing values, but will create additional ones if necess)
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['sitePrefsFile'], configspec=prefsSpec)
        cfg.validate(self._validator, copy=True)#copy means all settings get saved
        if len(cfg['general']['userPrefsFile'])==0:
            cfg['general']['userPrefsFile']=self.paths['userPrefsFile']#set path to home
        else: self.paths['userPrefsFile']=cfg['general']['userPrefsFile']#set app path to user override
        cfg.initial_comment=["#preferences set in this file apply to all users",
            "the file can be found at %s" %self.paths['sitePrefsFile']]
        cfg.write()#so the user can see what's (now) available
        return cfg
    def loadUserPrefs(self):  
        #check for folder
        if not os.path.isdir(self.paths['userPrefs']):
            os.makedirs(self.paths['userPrefs'])  
        #then add user prefs
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['userPrefsFile'], configspec=prefsSpec)
        cfg.validate(self._validator, copy=False)#copy means all settings get saved   
        cfg.initial_comment=["#preferences set in this file will override the site-prefs",
            "#to set a preference here simply copy and paste from the site-prefs file",
            "the file can be found at %s" %self.paths['userPrefsFile']]
        cfg.write()
        return cfg
    def getAutoProxy(self):
        """Fetch the proxy from the the system environment variables
        """
        if urllib.getproxies().has_key('http'):
            return urllib.getproxies()['http']
        else:
            return ""
        
class PreferencesDlg(wx.Frame):
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy Preferences"):
        wx.Frame.__init__(self, parent, ID, title, size=(500,700))
        panel = wx.Panel(self)
        self.nb = wx.Notebook(panel)
        self.pageIDs={}#store the page numbers
        self.paths = app.prefs.paths
        self.app=app
        
        for n, prefsType in enumerate(['site','user']):
            sitePage = self.makePage(self.paths['%sPrefsFile' %prefsType])
            self.nb.AddPage(sitePage,prefsType)
            self.pageIDs[prefsType]=n
        
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        panel.SetSizer(sizer)
    
        self.menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        item = self.fileMenu.Append(wx.ID_SAVE,   "&Save prefs\t%s" %key_save)
        self.Bind(wx.EVT_MENU, self.save, item)
        item = self.fileMenu.Append(wx.ID_CLOSE,   "&Close (prefs)\t%s" %key_close)
        self.Bind(wx.EVT_MENU, self.close, item)
        self.fileMenu.AppendSeparator()
        item = self.fileMenu.Append(-1, "&Quit (entire app)\t%s" %key_quit, "Terminate the application")
        self.Bind(wx.EVT_MENU, self.quit, item)

#        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
#        self.fileMenu.Enable(wx.ID_SAVE, False)
        self.menuBar.Append(self.fileMenu, "&File")
        self.SetMenuBar(self.menuBar)
        
    def makePage(self, path):
        page = wx.stc.StyledTextCtrl(parent=self.nb)
        
        # setup the style
        if sys.platform=='darwin':
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier New,size:10d")
        else:
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier,size:12d")
        page.StyleClearAll()  # Reset all to be like the default
        page.SetLexer(wx.stc.STC_LEX_PROPERTIES)
        page.StyleSetSpec(wx.stc.STC_PROPS_SECTION,"fore:#FF0000")
        page.StyleSetSpec(wx.stc.STC_PROPS_COMMENT,"fore:#007F00")
        
        f = open(path, 'r+')
        page.SetText(f.read())
        f.close()        
        if not os.access(path,os.W_OK):#can only read so make the textctrl read-only
            page.set_read_only()
        
        return page
    def close(self, event=None):
        okToQuit=self.save(event=None)#will be -1 if user cancelled during save
        self.Destroy()
    def quit(self,event=None):
        self.close()
        self.app.quit()
    def save(self, event=None):
        ok=1
        for prefsType in ['site','user']:
            pageText = self.getPageText(prefsType)
            filePath = self.paths['%sPrefsFile' %prefsType]
            if self.isChanged(prefsType):
                f=open(filePath,'w')
                f.write(pageText)
                f.close()
                print "saved", filePath             
        return ok
    def getPageText(self,prefsType):
        """Get the prefs text for a given page
        """
        self.nb.ChangeSelection(self.pageIDs[prefsType])
        return self.nb.GetCurrentPage().GetText().encode('utf-8')
    def isChanged(self,prefsType='site'):
        filePath = self.paths['%sPrefsFile' %prefsType]
        f = open(filePath, 'r+')
        savedTxt = f.read()
        f.close()
        #find the notebook page
        currTxt = self.getPageText(prefsType)
        return (currTxt!=savedTxt)
    