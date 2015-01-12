# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import urllib2, re, glob
import time, platform, sys, zipfile, os, cStringIO
import wx
import wx.lib.filebrowsebutton
try:
    from agw import hyperlink as wxhl
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.hyperlink as wxhl
import psychopy
from psychopy import web
from psychopy.app import dialogs
from psychopy import logging

versionURL = "http://www.psychopy.org/version.txt"

"""The Updater class checks for updates and suggests that an update is carried
out if a new version is found. The actual updating is handled by InstallUpdateDialog
(via Updater.doUpdate() ).
"""

def makeConnections(app):
    """A helper function to be launched from a thread. Will setup proxies and check for updates.
    Should be run from a thread while the program continues to load.
    """
    if web.proxies is None:
        web.setupProxy()
    if web.proxies==0:
        return
    if app.prefs.connections['allowUsageStats']:
        sendUsageStats()
    if app.prefs.connections['checkForUpdates']:
        app._latestAvailableVersion = getLatestVersionInfo()

def getLatestVersionInfo():
    """
    Fetch info about the latest availiable version.
    Returns -1 if fails to make a connection
    """
    try:
        page = urllib2.urlopen(versionURL)
    except urllib2.URLError:
        return -1
    #parse update file as a dictionary
    latest={}
    for line in page.readlines():
        #in some odd circumstances (wifi hotspots) you might successfully fetch a
        #page that is not the correct URL but a redirect
        if line.find(':')==-1:
            return -1
            #this will succeed if every line has a key
        key, keyInfo = line.split(':')
        latest[key]=keyInfo.replace('\n', '').replace('\r', '')
    return latest

class Updater:
    def __init__(self,app=None, runningVersion=None):
        """The updater will check for updates and download/install them if necess.
        Several dialogs may be created as needed during the process.

        Usage::

            if app.prefs['AutoUpdate']:
                app.updates=Updater(app)
                app.updater.checkForUpdates()#if updates are found further dialogs will prompt
        """
        self.app=app
        if runningVersion is None:  self.runningVersion=psychopy.__version__
        else:  self.runningVersion=runningVersion

        #self.headers = {'User-Agent' : psychopy.constants.PSYCHOPY_USERAGENT}
        self.latest=None
        if web.proxies is None:
            web.setupProxy()

    def getLatestInfo(self, warnMsg=False):
        #open page
        latest=getLatestVersionInfo()
        if latest==-1:
            msg=_translate("Couldn't connect to psychopy.org to check for updates. \n")+\
                _translate("Check internet settings (and proxy setting in PsychoPy Preferences).")
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title=_translate('PsychoPy updates'))
            confirmDlg.ShowModal()
        return latest
    def suggestUpdate(self, confirmationDlg=False):
        """Query user about whether to update (if it's possible to do the update)
        """
        if self.latest is None:#we haven't checked for updates yet
            self.latest=self.getLatestInfo()

        if self.latest==-1: return -1#failed to find out about updates
        #have found 'latest'. Is it newer than running version?
        if self.latest['version']>self.runningVersion and not (self.app.prefs.appData['skipVersion']==self.latest['version']):
            if self.latest['lastUpdatable']<=self.runningVersion:
                #go to the updating window
                confirmDlg = SuggestUpdateDialog(self.latest, self.runningVersion)
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
            else:
                #the latest version needs a full install, rather than an autoupdate
                msg = _translate("PsychoPy v%(latest)s is available (you are running %(running)s).\n\n") % {'latest':self.latest['version'], 'running':self.runningVersion}
                msg+= _translate("This version is too big an update to be handled automatically.\n")
                msg+= _translate("Please fetch the latest version from www.psychopy.org and install manually.")
                confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Warning', title=_translate('PsychoPy updates'))
                confirmDlg.cancelBtn.SetLabel(_translate('Go to downloads'))
                confirmDlg.cancelBtn.SetDefault()
                confirmDlg.noBtn.SetLabel(_translate('Go to changelog'))
                confirmDlg.yesBtn.SetLabel(_translate('Later'))
                resp=confirmDlg.ShowModal()
                confirmDlg.Destroy()
                if resp==wx.ID_CANCEL:
                    self.app.followLink(url=self.app.urls['downloads'])
                if resp==wx.ID_NO:
                    self.app.followLink(url=self.app.urls['changelog'])
        elif not confirmationDlg:#do nothing
            return 0
        else:
            msg= _translate("You are running the latest version of PsychoPy (%s). ") %(self.runningVersion)
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title=_translate('PsychoPy updates'))
            confirmDlg.ShowModal()
            return -1
    def doUpdate(self):
        """Should be called from suggestUpdate (separate dialog to ask user whether they want to)
        """
        dlg=InstallUpdateDialog(None,-1, app=self.app)#app contains a reciprocal pointer to this Updater object

class SuggestUpdateDialog(wx.Dialog):
    """A dialog explaining that a new version is available with a link to the changelog
    """
    def __init__(self,latest,runningVersion):
        wx.Dialog.__init__(self,None,-1,title='PsychoPy2 Updates')
        sizer=wx.BoxSizer(wx.VERTICAL)

        #info about current version
        msg1 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label=_translate("PsychoPy v%(latest)s is available (you are running %(running)s).\n\n(To disable this check, see Preferences > connections > checkForUpdates)") % {'latest':latest['version'],'running':runningVersion})
        if latest['lastCompatible']>runningVersion:
            msg2 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label=_translate("This version MAY require you to modify your\nscripts/exps slightly. Read the changelog carefully."))
            msg2.SetForegroundColour([200,0,0])
        else: msg2 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label=_translate("There are no known compatibility\nissues with your current version."))
        changelogLink = wxhl.HyperLinkCtrl(self, wx.ID_ANY, _translate("View complete Changelog"),
                                        URL="http://www.psychopy.org/changelog.html")

        if sys.platform.startswith('linux'):
            msg3 = wx.StaticText(self,-1,_translate("You can update PsychoPy with your package manager"))
        else:
            msg3 = wx.StaticText(self,-1,_translate("Should PsychoPy update itself?"))

        sizer.Add(msg1,flag=wx.ALL|wx.CENTER,border=15)
        sizer.Add(msg2,flag=wx.RIGHT|wx.LEFT|wx.CENTER,border=15)
        sizer.Add(changelogLink,flag=wx.RIGHT|wx.LEFT|wx.CENTER,border=5)
        sizer.Add(msg3,flag=wx.ALL|wx.CENTER,border=15)

        #add buttons
        btnSizer=wx.BoxSizer(wx.HORIZONTAL)

        if sys.platform.startswith('linux'):#for linux there should be no 'update' option
            self.cancelBtn=wx.Button(self,wx.ID_CANCEL,_translate('Keep warning me'))
            self.cancelBtn.SetDefault()
            self.noBtn=wx.Button(self,wx.ID_NO,_translate('Stop warning me'))
        else:
            self.yesBtn=wx.Button(self,wx.ID_YES,_translate('Yes'))
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_YES)
            self.cancelBtn=wx.Button(self,wx.ID_CANCEL,_translate('Not now'))
            self.noBtn=wx.Button(self,wx.ID_NO,_translate('Skip this version'))
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_NO)
        btnSizer.Add(self.noBtn, wx.ALIGN_LEFT)
        btnSizer.Add((60, 20), 0, wx.EXPAND)
        btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)

        if not sys.platform.startswith('linux'):
            self.yesBtn.SetDefault()
            btnSizer.Add((5, 20), 0)
            btnSizer.Add(self.yesBtn, wx.ALIGN_RIGHT)

        #configure sizers and fit
        sizer.Add(btnSizer,flag=wx.ALIGN_RIGHT|wx.ALL,border=5)
        self.Center()
        self.SetSizerAndFit(sizer)
    def onButton(self,event):
        self.EndModal(event.GetId())

class InstallUpdateDialog(wx.Dialog):
    def __init__(self, parent, ID, app):
        """Latest is optional extra. If not given it will be fetched.
        """
        self.app = app
        #get latest version info if poss
        if app.updater in [False,None]:
            #user has turned off check for updates in prefs so check now
            app.updater = updater = Updater(app=self.app)
            self.latest=updater.getLatestInfo(warnMsg=False)#don't need a warning - we'll provide one ourselves
        else:
            self.latest=app.updater.latest
        self.runningVersion=app.updater.runningVersion
        wx.Dialog.__init__(self, parent, ID, title=_translate('PsychoPy Updates'), size=(100,200))

        mainSizer=wx.BoxSizer(wx.VERTICAL)
        #set the actual content of the status message later in self.updateStatus()
        msg = "x"
        self.statusMessage = wx.StaticText(self,-1,msg,style=wx.ALIGN_CENTER)
        mainSizer.Add(self.statusMessage,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for auto-update from web
        self.useLatestBtn = wx.RadioButton( self, -1, _translate(" Auto-update (will fetch latest version)"), style = wx.RB_GROUP )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useLatestBtn )
        self.progressBar = wx.Gauge(self, -1, 100, size=(250,25))
        mainSizer.Add(self.useLatestBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.progressBar,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for updating from specific zip file
        self.useZipBtn = wx.RadioButton( self, -1, _translate(" Use zip file below (download a PsychoPy release file ending .zip)") )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useZipBtn )
        self.fileBrowseCtrl = wx.lib.filebrowsebutton.FileBrowseButton(
            self, -1, size=(450, -1),changeCallback = self.onFileBrowse, fileMask='*.zip')
        mainSizer.Add(self.useZipBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.fileBrowseCtrl,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        #ctrls for buttons (install/cancel)
        self.installBtn = wx.Button(self,-1,_translate('Install'))
        self.Bind(wx.EVT_BUTTON, self.onInstall, self.installBtn )
        self.installBtn.SetDefault()
        self.cancelBtn = wx.Button(self,-1,_translate('Close'))
        self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn )
        btnSizer=wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(self.installBtn,flag=wx.ALIGN_RIGHT)
        btnSizer.Add(self.cancelBtn,flag=wx.ALIGN_RIGHT|wx.LEFT,border=5)
        mainSizer.Add(btnSizer,flag=wx.ALIGN_RIGHT|wx.ALL,border=5)

        self.SetSizerAndFit(mainSizer)
        self.SetAutoLayout(True)

        #positioning and sizing
        self.updateStatus()
        self.Center()
        self.ShowModal()
    def updateStatus(self):
        """Check the current version and most recent version and update ctrls if necess
        """
        if self.latest==-1:
            msg = _translate("You are running PsychoPy v%s.\n ") %(self.runningVersion) + \
                _translate("PsychoPy could not connect to the \n internet to check for more recent versions.\n") + \
                _translate("Check proxy settings in preferences.")
        elif self.latest==self.runningVersion:
            msg = _translate("You are running the latest version of PsychoPy (%s)\n ") %(self.runningVersion) + \
                _translate("You can revert to a previous version by selecting a specific .zip source installation file")
        else:
            msg = _translate("PsychoPy v%(latest)s is available\nYou are running v%(running)s") % {'latest':self.latest['version'], 'running':self.runningVersion}
            if self.latest['lastUpdatable']<=self.runningVersion:
                msg+=_translate("\nYou can update to the latest version automatically")
            else:
                msg+=_translate("\nYou cannot update to the latest version automatically.\nPlease fetch the latest Standalone package from www.psychopy.org")
        self.statusMessage.SetLabel(msg)
        if self.latest==-1 \
            or self.latest['version']==self.runningVersion \
            or self.latest['lastUpdatable']>self.runningVersion:#can't auto-update
                self.currentSelection=self.useZipBtn
                self.useZipBtn.SetValue(True)
                self.useLatestBtn.Disable()
        else:
            self.currentSelection=self.useLatestBtn
            self.useLatestBtn.SetValue(True)
        self.Fit()
        self.onRadioSelect()#this will enable/disable additional controls for the above
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
            self.installBtn.Enable()#if this has been disabled by the fact that we couldn't connect
    def onCancel(self, event):
        self.app.updater=None
        self.Destroy()
    def onFileBrowse(self, event):
        self.filename = event.GetString()
    def onInstall(self, event):
        if self.currentSelection==self.useLatestBtn:
            info = self.doAutoInstall()
        else:
            info = self.installZipFile(self.filename)
        self.statusMessage.SetLabel(info)
        self.Fit()
    def fetchPsychoPy(self, v='latest'):
        msg = _translate("Attempting to fetch PsychoPy %s...") %(self.latest['version'])
        self.statusMessage.SetLabel(msg)
        info = ""
        if v=='latest':
            v=self.latest['version']

        #open page
        URL = "https://sourceforge.net/projects/psychpy/files/PsychoPy-%s.zip" %(v)
        page = urllib2.urlopen(URL)
        #download in chunks so that we can monitor progress and abort mid-way through
        chunk=4096; read = 0
        fileSize = int(page.info()['Content-Length'])
        buffer=cStringIO.StringIO()
        self.progressBar.SetRange(fileSize)
        while read<fileSize:
            ch=page.read(chunk)
            buffer.write(ch)
            read+=chunk
            self.progressBar.SetValue(read)
            msg = _translate("Fetched %(done)i of %(total)i kb of PsychoPy-%(version)s.zip") % {'done':read/1000, 'total':fileSize/1000, 'version':v}
            self.statusMessage.SetLabel(msg)
            self.Update()
        info+= _translate('Successfully downloaded PsychoPy-%s.zip') %v
        page.close()
        zfile = zipfile.ZipFile(buffer)
        #buffer.close()
        return zfile, info

    def installZipFile(self, zfile, v=None):
        """If v is provided this will be used as new version number, otherwise try and retrieve
        a version number from zip file name
        """
        info=""#return this at the end

        if type(zfile) in [str, unicode] and os.path.isfile(zfile):#zfile is filename not an actual file
            if v is None: #try and deduce it
                zFilename = os.path.split(zfile)[-1]
                searchName = re.search('[0-9]*\.[0-9]*\.[0-9]*.', zFilename)
                if searchName!=None:
                    v=searchName.group(0)[:-1]
                else:logging.warning("Couldn't deduce version from zip file: %s" %zFilename)
            f=open(zfile, 'rb')
            zfile=zipfile.ZipFile(f)
        else:#assume here that zfile is a ZipFile
            pass#todo: error checking - is it a zipfile?

        currPath=self.app.prefs.paths['psychopy']
        #any commands that are successfully executed may need to be undone if a later one fails
        undoString = ""
        #depending on install method, needs diff handling
        #if path ends with 'psychopy' then move it to 'psychopy-version' and create a new 'psychopy' folder for new version
        versionLabelsInPath = re.findall('PsychoPy-.*/',currPath)#does the path contain any version number?
        if len(versionLabelsInPath)==0:#e.g. the mac standalone app, no need to refer to new versino number
            unzipTarget=currPath
            try: #to move existing PsychoPy
                os.rename(currPath, "%s-%s" %(currPath, psychopy.__version__))
                undoString += 'os.rename("%s-%s" %(currPath, psychopy.__version__),currPath)\n'
            except:
                if sys.platform=='win32' and int(sys.getwindowsversion()[1])>5:
                    msg = _translate("To upgrade you need to restart the app as admin (Right-click the app and 'Run as admin')")
                else:
                    msg=_translate("Could not move existing PsychoPy installation (permissions error?)")
                return msg
        else:#setuptools-style installation
            #generate new target path
            unzipTarget=currPath
            for thisVersionLabel in versionLabelsInPath:
                pathVersion=thisVersionLabel[:-1]#remove final slash from the re.findall
                unzipTarget=unzipTarget.replace(pathVersion, "PsychoPy-%s" %v)
                # find the .pth file that specifies the python dir
                #create the new installation directory BEFORE changing pth file
                nUpdates, newInfo = self.updatePthFile(pathVersion, "PsychoPy-%s" %v)
                if nUpdates==-1:#there was an error (likely permissions)
                    undoString += 'self.updatePthFile(unzipTarget, currPath)\n'
                    exec(undoString)#undo previous changes
                    return newInfo

        try:
            os.makedirs(unzipTarget)#create the new installation directory AFTER renaming existing dir
            undoString += 'os.remove(%s)\n' %unzipTarget
        except: #revert path rename and inform user
            exec(undoString)#undo previous changes
            if sys.platform=='win32' and int(sys.getwindowsversion()[1])>5:
                msg = _translate("Right-click the app and 'Run as admin'):\n%s") %unzipTarget
            else:
                msg = _translate("Failed to create directory for new version (permissions error?):\n%s") %unzipTarget
            return msg

        #do the actual extraction
        for name in zfile.namelist():#for each file within the zip
            #check that this file is part of the psychopy (not metadata or docs)
            if name.count('/psychopy/')<1: continue
            try:
                targetFile = os.path.join(unzipTarget, name.split('/psychopy/')[1])
                targetContainer=os.path.split(targetFile)[0]
                if not os.path.isdir(targetContainer):
                    os.makedirs(targetContainer)#make the containing folder
                if targetFile.endswith('/'):
                    os.makedirs(targetFile)#it's a folder
                else:
                    outfile = open(targetFile, 'wb')
                    outfile.write(zfile.read(name))
                    outfile.close()
            except:
                exec(undoString)#undo previous changes
                logging.error('failed to unzip file: '+name)
                logging.error(sys.exc_info()[0])
        info += _translate('Success. \nChanges to PsychoPy will be completed when the application is next run')
        self.cancelBtn.SetDefault()
        self.installBtn.Disable()
        return info
    def doAutoInstall(self, v='latest'):
        if v=='latest':
            v=self.latest['version']
        self.statusMessage.SetLabel(_translate("Downloading PsychoPy v%s") %v)
        try: zipFile, info =self.fetchPsychoPy(v)
        except:
            self.statusMessage.SetLabel(_translate('Failed to fetch PsychoPy release.\nCheck proxy setting in preferences'))
            return -1
        self.statusMessage.SetLabel(info)
        self.Fit()
        #got a download - try to install it
        info=self.installZipFile(zipFile, v)
        return info
    def updatePthFile(self, oldName, newName):
        """Searches site-packages for .pth files and replaces any instance of
        `oldName` with `newName`, where the names likely have the form PsychoPy-1.60.04
        """
        from distutils.sysconfig import get_python_lib
        siteDir=get_python_lib()
        pthFiles = glob.glob(os.path.join(siteDir, '*.pth'))
        enclosingSiteDir = os.path.split(siteDir)[0]#sometimes the site-packages dir isn't where the pth files are kept?
        pthFiles.extend(glob.glob(os.path.join(enclosingSiteDir, '*.pth')))
        nUpdates = 0#no paths updated
        info=""
        for filename in pthFiles:
            lines = open(filename, 'r').readlines()
            needSave=False
            for lineN, line in enumerate(lines):
                if oldName in line:
                    lines[lineN] = line.replace(oldName, newName)
                    needSave=True
            if needSave:
                try:
                    f = open(filename, 'w')
                    f.writelines(lines)
                    f.close()
                    nUpdates+=1
                    logging.info('Updated PsychoPy path in %s' %filename)
                except:
                    info+='Failed to update PsychoPy path in ', filename
                    return -1, info
        return nUpdates, info
def sendUsageStats():
    """Sends anonymous, very basic usage stats to psychopy server:
      the version of PsychoPy
      the system used (platform and version)
      the date
    """

    v=psychopy.__version__
    dateNow = time.strftime("%Y-%m-%d_%H:%M")
    miscInfo = ''

    #urllib.install_opener(opener)
    #check for proxies
    if web.proxies is None:
        web.setupProxy()

    #get platform-specific info
    if sys.platform=='darwin':
        OSXver, junk, architecture = platform.mac_ver()
        systemInfo = "OSX_%s_%s" %(OSXver, architecture)
    elif sys.platform.startswith('linux'):
        systemInfo = '%s_%s_%s' % (
            'Linux',
            ':'.join([x for x in platform.dist() if x != '']),
            platform.release())
    elif sys.platform=='win32':
        ver=sys.getwindowsversion()
        if len(ver[4])>0:
            systemInfo=("win32_v%i.%i.%i_%s" %(ver[0],ver[1],ver[2],ver[4])).replace(' ','')
        else:
            systemInfo="win32_v%i.%i.%i" %(ver[0],ver[1],ver[2])
    else:
        systemInfo = platform.system()+platform.release()
    URL = "http://www.psychopy.org/usage.php?date=%s&sys=%s&version=%s&misc=%s" \
        %(dateNow, systemInfo, v, miscInfo)
    try:
        req = urllib2.Request(URL)
        page = urllib2.urlopen(req)#proxies
    except:
        logging.warning("Couldn't connect to psychopy.org\n"+\
            "Check internet settings (and proxy setting in PsychoPy Preferences.")
