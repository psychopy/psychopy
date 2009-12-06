# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import urllib2, time, platform, sys, zipfile, os, cStringIO
import wx
import  wx.lib.filebrowsebutton
import psychopy
from psychopy.app import dialogs
from psychopy import log

class Updater:
    def __init__(self,app=None, proxy=None, runningVersion=None):
        """The updater will check for updates and download/install them if necess.
        Several dialogs may be created as needed during the process.
        
        Usage::
            
            if app.prefs['AutoUpdate']:
                app.updates=Updater(app, proxy)
                app.updater.checkForUpdates()#if updates are found further dialogs will prompt
        """
        self.app=app
#        self.proxies=
        if runningVersion==None:  self.runningVersion=psychopy.__version__
        else:  self.runningVersion=runningVersion
        
        self.headers = {'User-Agent' : 'Mozilla/5.0'}      
        self.latest=None
        self.setupProxies(proxy)
        
    def showModal(self):
        #setup output window for info
        origStdOut = sys.stdout
        origStdErr = sys.stderr
#        sys.stdout = self.outStream
#        sys.stderr = self.outStream
        #show dlg
        retVal = self.ShowModal()
        #return output to original
        sys.stdout = origStdOut
        sys.stderr = origStdErr
        print retVal
        self.Destroy()
        
    def setupProxies(self, proxy=None):
        """Get proxies and insert into url opener"""
        if proxy is None: proxies = urllib2.getproxies()
        else: proxies=urllib2.ProxyHandler({'http':proxy})
        if len(proxies.proxies['http'])>0:
            opener  = urllib2.build_opener(proxies)
            urllib2.install_opener(opener)#this will now be used globally for ALL urllib2 opening
        else:
            pass#no proxy could be found so use none
    def getLatestInfo(self):
        #open page
        URL = "http://www.psychopy.org/version.txt"
        try:
            page = urllib2.urlopen(URL)#proxies
        except:
            msg="Couldn't connect to psychopy.org to check for updates. \n"+\
                "Check internet settings (and proxy setting in PsychoPy Preferences)."
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title='PsychoPy updates')
            confirmDlg.ShowModal()
            return -1
        #parse update file as a dictionary
        latest={}
        for line in page.readlines():
            key, keyInfo = line.split(':')
            latest[key]=keyInfo.replace('\n', '')
        return latest
    def suggestUpdate(self, confirmationDlg=False):
        """Query user about whether to update (if it's possible to do the update)
        """
        if self.latest==None:#we haven't checked for updates yet
            self.latest=self.getLatestInfo()
        
        if self.latest==-1: return -1#failed to find out about updates
        #have found 'latest'. Is it newer than running version?
        if self.latest['version']>self.runningVersion and not (self.app.prefs.appData['skipVersion']==self.latest['version']):            
            msg = "PsychoPy v%s is available (you are running %s).\n\n" %(self.latest['version'], self.runningVersion)
            msg+= "For details see full changelog at\nhttp://www.psychopy.org/changelog.html"
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Warning', title='PsychoPy updates')
            confirmDlg.cancelBtn.SetLabel('Not now')
            confirmDlg.noBtn.SetLabel('Skip this version')        
            confirmDlg.yesBtn.SetDefault()    
            resp=confirmDlg.ShowModal()
            confirmDlg.Destroy()
            #what did the user ask us to do?
            if resp==wx.ID_CANCEL:
                return 0#do nothing
            if resp==wx.ID_NO:
                self.app.prefs.appData['skipVersion']=self.latest['version']
                self.app.prefs.saveAppData()
                return 0#do nothing
            if resp==wx.ID_YES:
                self.doUpdate()
        elif not confirmationDlg:#don't confirm but return the latest version info
            return 0
        else:
            msg= "You are running the latest version of PsychoPy (%s). " %(self.runningVersion)
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title='PsychoPy updates')
            confirmDlg.ShowModal()
            return -1
    def doUpdate(self):
        """Should be called from suggestUpdate (separate dialog to ask user whether they want to)
        """
        dlg=InstallUpdateDialog(None,-1, app=self.app,updater=self)

class InstallUpdateDialog(wx.Frame):
    def __init__(self, parent, ID, app, updater):
        """Latest is optional extra. If not given it will be fetched.
        """
        self.app = app
        self.runningVersion=updater.runningVersion
        self.latest=updater.latest
        wx.Frame.__init__(self, parent, ID, title='PsychoPy Updates', size=(100,200))
        
        mainSizer=wx.BoxSizer(wx.VERTICAL)
        self.statusMessage = wx.StaticText(self,-1,
            "PsychoPy v%s is available\nyou are running v%s)" %(self.latest['version'], self.runningVersion),
            style=wx.ALIGN_CENTER)
        mainSizer.Add(self.statusMessage,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for auto-update from web
        self.useLatestBtn = wx.RadioButton( self, -1, " Auto-update (latest) ", style = wx.RB_GROUP )
        self.useLatestBtn.SetValue(True)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useLatestBtn )
        self.progressBar = wx.Gauge(self, -1, 100, size=(250,25))
        mainSizer.Add(self.useLatestBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.progressBar,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for updating from specific zip file
        self.useZipBtn = wx.RadioButton( self, -1, " Use zip file below " )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useZipBtn )
        self.fileBrowseCtrl = wx.lib.filebrowsebutton.FileBrowseButton(
            self, -1, size=(450, -1),changeCallback = self.onFileBrowse)
        mainSizer.Add(self.useZipBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.fileBrowseCtrl,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        #ctrls for buttons (install/cancel)
        self.installBtn = wx.Button(self,-1,'Install')
        self.Bind(wx.EVT_BUTTON, self.onInstall, self.installBtn )
        self.installBtn.SetDefault()
        self.cancelBtn = wx.Button(self,-1,'Cancel')
        self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn )
        btnSizer=wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(self.installBtn,flag=wx.ALIGN_RIGHT)
        btnSizer.Add(self.cancelBtn,flag=wx.ALIGN_RIGHT|wx.LEFT,border=5)
        mainSizer.Add(btnSizer,flag=wx.ALIGN_RIGHT|wx.ALL,border=5)
        
        self.currentSelection=self.useLatestBtn
        self.onRadioSelect()#this will enable/dissable appropriate controlsfor the above
        #positioning and sizing
        self.Center()
        self.SetSizerAndFit(mainSizer)
        self.SetAutoLayout(True)
        self.Show()
    def onRadioSelect(self, event=None):
        """Set the controls of the appropriate selection to be disabled/enabled
        """
        #if receive no event then just set everthing to previous state
        if event!=None:
            self.currentSelection = event.GetEventObject()
        else:
            pass
        if self.currentSelection==self.useLatestBtn:
            self.fileBrowseCtrl.Disable()
            self.progressBar.Enable()
        elif self.currentSelection==self.useZipBtn:
            self.fileBrowseCtrl.Enable()
            self.progressBar.Disable()
    def onCancel(self, event):
        self.Destroy()
    def onFileBrowse(self, event):
        self.filename = event.GetString()
    def onInstall(self, event):
        if self.currentSelection==self.useLatestBtn:
            self.doAutoInstall()
        else:
            self.installZipFile(self.filename)
    def fetchPsychoPy(self, v='latest'):
        if v=='latest':
            v=self.latest['version']
        
        #open page
        URL = "http://psychopy.googlecode.com/files/PsychoPy-%s.zip" %(v)
        URL = 'http://downloads.egenix.com/python/locale-0.1.zip'
        page = urllib2.urlopen(URL)
        #download in chunks so that we can monitor progress and abort mid-way through
        chunk=4096; read = 0
        fileSize = int(page.info()['Content-Length'])
        buffer=cStringIO.StringIO()
        while read<fileSize:
            buffer.write(page.read(chunk))
            read+=chunk
            print '.',; sys.stdout.flush()
        print 'download complete'
        page.close()
        zfile = zipfile.ZipFile(buffer)
        buffer.close()
        return zfile
        
    def installZipFile(self, zfile):
        if type(zfile)==str and os.path.isfile(zfile):
            f=open(zfile)
            zfile=zipfile.ZipFile(f)
            f.close()
        else:
            pass#todo: error checking - zfile should be a ZipFile or a filename
            
        currPath=self.app.prefs.paths[psychopy]
        rootPath,endPath=sys.path.split(currPath)
        #depending on install method, needs diff handling
        #if path ends with 'psychopy' then move it to 'psychopy-version' and create a new 'psychopy' folder for new version
        if endPath=='psychopy':#e.g. the mac standalone app
#            os.rename(currPath, "%s-%s" %(currPath, psychopy.__version__))
            os.mkdir(currPath+'X')
            unzipTarget=currPath+'X'
        
        zfile.extractall(unzipTarget)
        print 'installed to %s' %unzipTarget
    def doAutoInstall(self, v='latest'):
        if v=='latest':
            v=self.latest['version']
        self.statusMessage.SetLabel("Downloading PsychoPy v%s" %v)
        zipFile=self.fetchPsychoPy(v)
        self.statusMessage.SetLabel("Downloaded PsychoPy v%s\nInstalling..." %v)
        self.installZipFile(zipFile)        
    
def sendUsageStats(proxy=None):
    """Sends anonymous, very basic usage stats to psychopy server:
      the version of PsychoPy
      the system used (platform and version)
      the date

    If http_proxy is set in the system environment variables these will be used automatically,
    but additional proxies can be provided here as the argument proxies.
    """
    v=psychopy.__version__
    dateNow = time.strftime("%Y-%m-%d_%H:%M")
    miscInfo = ''

    #urllib.install_opener(opener)
    #check for proxies
    if proxy in [None,""]:
        pass#use default opener (no proxies)
    else:
        #build the url opener with proxy and cookie handling
        opener = urllib2.build_opener(
            urllib2.ProxyHandler({'http':proxy}))
        urllib2.install_opener(opener)

    #get platform-specific info
    if platform.system()=='Darwin':
        OSXver, junk, architecture = platform.mac_ver()
        systemInfo = "OSX_%s_%s" %(OSXver, architecture)
    elif platform.system()=='Linux':
        systemInfo = '%s_%s_%s' % (
            platform.system(),
            ':'.join([x for x in platform.dist() if x != '']),
            platform.release())
    else:
        systemInfo = platform.system()+platform.release()
    URL = "http://www.psychopy.org/usage.php?date=%s&sys=%s&version=%s&misc=%s" \
        %(dateNow, systemInfo, v, miscInfo)
    req = urllib2.Request(URL)
    page = urllib2.urlopen(req)#proxies
    try:
        req = urllib2.Request(URL)
        page = urllib2.urlopen(req)#proxies
    except:
        log.warning("Couldn't connect to psychopy.org\n"+\
            "Check internet settings (and proxy setting in PsychoPy Preferences.")
        pass#maybe proxy is wrong, maybe no internet connection etc...
