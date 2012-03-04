# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import urllib2, socket, re, glob
import time, platform, sys, zipfile, os, cStringIO
import threading
import wx
import  wx.lib.filebrowsebutton
try:
    from agw import hyperlink as wxhl
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.hyperlink as wxhl
import psychopy
from psychopy.app import dialogs
from psychopy import logging
from psychopy import preferences
prefs=preferences.Preferences()

socket.setdefaulttimeout(2)

global proxies
proxies=None #if this is populated then it has been set up already

versionURL = "http://www.psychopy.org/version.txt"

"""The Updater class checks for updates and suggests that an update is carried
out if a new version is found. The actual updating is handled by InstallUpdateDialog
(via Updater.doUpdate() ).
"""

def makeConnections(app):
    """A helper function to be launched from a thread. Will setup proxies and check for updates.
    Should be run from a thread while the program continues to load.
    """
    if proxies is None:
        setupProxy()
    if proxies==0:
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
    def __init__(self,app=None, runningVersion=None, proxy=None):
        """The updater will check for updates and download/install them if necess.
        Several dialogs may be created as needed during the process.

        Usage::

            if app.prefs['AutoUpdate']:
                app.updates=Updater(app, proxy)
                app.updater.checkForUpdates()#if updates are found further dialogs will prompt
        """
        global proxies
        self.app=app
        if runningVersion==None:  self.runningVersion=psychopy.__version__
        else:  self.runningVersion=runningVersion

        self.headers = {'User-Agent' : 'Mozilla/5.0'}
        self.latest=None
        if proxies==None:
            setupProxy()

    def getLatestInfo(self, warnMsg=False):
        #open page
        latest=getLatestVersionInfo()
        if latest==-1:
            msg="Couldn't connect to psychopy.org to check for updates. \n"+\
                "Check internet settings (and proxy setting in PsychoPy Preferences)."
            confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title='PsychoPy updates')
            confirmDlg.ShowModal()
        return latest
    def suggestUpdate(self, confirmationDlg=False):
        """Query user about whether to update (if it's possible to do the update)
        """
        if self.latest==None:#we haven't checked for updates yet
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
                msg = "PsychoPy v%s is available (you are running %s).\n\n" %(self.latest['version'], self.runningVersion)
                msg+= "This version is too big an update to be handled automatically.\n"
                msg+= "Please fetch the latest version from www.psychopy.org and install manually."
                confirmDlg = dialogs.MessageDialog(parent=None,message=msg,type='Warning', title='PsychoPy updates')
                confirmDlg.cancelBtn.SetLabel('Go to downloads')
                confirmDlg.cancelBtn.SetDefault()
                confirmDlg.noBtn.SetLabel('Go to changelog')
                confirmDlg.yesBtn.SetLabel('Later')
                resp=confirmDlg.ShowModal()
                confirmDlg.Destroy()
                if resp==wx.ID_CANCEL:
                    self.app.followLink(url=self.app.urls['downloads'])
                if resp==wx.ID_NO:
                    self.app.followLink(url=self.app.urls['changelog'])
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
        dlg=InstallUpdateDialog(None,-1, app=self.app)#app contains a reciprocal pointer to this Updater object

class SuggestUpdateDialog(wx.Dialog):
    """A dialog explaining that a new version is available with a link to the changelog
    """
    def __init__(self,latest,runningVersion):
        wx.Dialog.__init__(self,None,-1,title='PsychoPy2 auto-updater')
        sizer=wx.BoxSizer(wx.VERTICAL)

        #info about current version
        msg1 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label="PsychoPy v%s is available (you are running %s)." %(latest['version'],runningVersion))
        if latest['lastCompatible']>runningVersion:
            msg2 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label="This version MAY require you to modify your\nscripts/exps slightly. Read the changelog carefully.")
            msg2.SetForegroundColour([200,0,0])
        else: msg2 = wx.StaticText(self,-1,style=wx.ALIGN_CENTRE,
            label="There are no known compatibility\nissues with your current version.")
        changelogLink = wxhl.HyperLinkCtrl(self, wx.ID_ANY, "View complete Changelog",
                                        URL="http://www.psychopy.org/changelog.html")

        msg3 = wx.StaticText(self,-1,"Should PsychoPy update itself?")
        sizer.Add(msg1,flag=wx.ALL|wx.CENTER,border=15)
        sizer.Add(msg2,flag=wx.RIGHT|wx.LEFT|wx.CENTER,border=15)
        sizer.Add(changelogLink,flag=wx.RIGHT|wx.LEFT|wx.CENTER,border=5)
        sizer.Add(msg3,flag=wx.ALL|wx.CENTER,border=15)

        #add buttons
        btnSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.yesBtn=wx.Button(self,wx.ID_YES,'Yes')
        self.cancelBtn=wx.Button(self,wx.ID_CANCEL,'Not now')
        self.noBtn=wx.Button(self,wx.ID_NO,'Skip this version')
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_YES)
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_NO)
        self.yesBtn.SetDefault()
        btnSizer.Add(self.noBtn, wx.ALIGN_LEFT)
        btnSizer.Add((60, 20), 0, wx.EXPAND)
        btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)
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
        wx.Dialog.__init__(self, parent, ID, title='PsychoPy Updates', size=(100,200))

        mainSizer=wx.BoxSizer(wx.VERTICAL)
        #set the actual content of the status message later in self.updateStatus()
        msg = "x"
        self.statusMessage = wx.StaticText(self,-1,msg,style=wx.ALIGN_CENTER)
        mainSizer.Add(self.statusMessage,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for auto-update from web
        self.useLatestBtn = wx.RadioButton( self, -1, " Auto-update (will fetch latest version)", style = wx.RB_GROUP )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useLatestBtn )
        self.progressBar = wx.Gauge(self, -1, 100, size=(250,25))
        mainSizer.Add(self.useLatestBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.progressBar,flag=wx.EXPAND|wx.ALL,border=5)
        #ctrls for updating from specific zip file
        self.useZipBtn = wx.RadioButton( self, -1, " Use zip file below (download a PsychoPy release file ending .zip)" )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useZipBtn )
        self.fileBrowseCtrl = wx.lib.filebrowsebutton.FileBrowseButton(
            self, -1, size=(450, -1),changeCallback = self.onFileBrowse, fileMask='*.zip')
        mainSizer.Add(self.useZipBtn,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        mainSizer.Add(self.fileBrowseCtrl,flag=wx.ALIGN_LEFT|wx.ALL,border=5)
        #ctrls for buttons (install/cancel)
        self.installBtn = wx.Button(self,-1,'Install')
        self.Bind(wx.EVT_BUTTON, self.onInstall, self.installBtn )
        self.installBtn.SetDefault()
        self.cancelBtn = wx.Button(self,-1,'Close')
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
            msg = "You are running PsychoPy v%s.\n " %(self.runningVersion) + \
                "PsychoPy could not connect to the \n internet to check for more recent versions.\n" + \
                "Check proxy settings in preferences."
        elif self.latest==self.runningVersion:
            msg = "You are running the latest version of PsychoPy (%s)\n " %(self.runningVersion) + \
                "You can revert to a previous version by selecting a specific .zip source installation file"
        else:
            msg = "PsychoPy v%s is available\nYou are running v%s" %(self.latest['version'], self.runningVersion)
            if self.latest['lastUpdatable']<=self.runningVersion:
                msg+="\nYou can update to the latest version automatically"
            else:
                msg+="\nYou cannot update to the latest version automatically.\nPlease fetch the latest Standalone package from www.psychopy.org"
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
        msg = "Attempting to fetch PsychoPy %s..." %(self.latest['version'])
        self.statusMessage.SetLabel(msg)
        info = ""
        if v=='latest':
            v=self.latest['version']

        #open page
        URL = "http://psychopy.googlecode.com/files/PsychoPy-%s.zip" %(v)
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
            msg = "Fetched %i of %i kb of PsychoPy-%s.zip" %(read/1000, fileSize/1000, v)
            self.statusMessage.SetLabel(msg)
            self.Update()
        info+= 'Successfully downloaded PsychoPy-%s.zip' %v
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
            if v==None: #try and deduce it
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
                    msg = "To upgrade you need to restart the app as admin (Right-click the app and 'Run as admin')"
                else:
                    msg="Could not move existing PsychoPy installation (permissions error?)"
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
                msg = "Right-click the app and 'Run as admin'):\n%s" %unzipTarget
            else:
                msg = "Failed to create directory for new version (permissions error?):\n%s" %unzipTarget
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
        info += 'Success. \nChanges to PsychoPy will be completed when the application is next run'
        self.cancelBtn.SetDefault()
        self.installBtn.Disable()
        return info
    def doAutoInstall(self, v='latest'):
        if v=='latest':
            v=self.latest['version']
        self.statusMessage.SetLabel("Downloading PsychoPy v%s" %v)
        try: zipFile, info =self.fetchPsychoPy(v)
        except:
            self.statusMessage.SetLabel('Failed to fetch PsychoPy release.\nCheck proxy setting in preferences')
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
    if proxies is None:
        setupProxy()

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


def testProxy(handler, URL=None):
    """
    Test whether we can connect to a URL with the current proxy settings.

    :Returns:

        - True (success)
        - a urllib2.URLError (which can be interrogated with .reason)
        - a urllib2.HTTPError (which can be interrogated with .code)

    """
    if URL is None:
        URL='http://www.google.com'#hopefully google isn't down!
    req = urllib2.Request(URL)
    opener = urllib2.build_opener(handler)
    try:
        page = opener.open(req).read(5)#open and read a few characters
        return True
    except urllib2.URLError, err:
        return err
    except urllib2.HTTPError, err:
        return err

def getPacFiles():
    """Return a list of possible auto proxy .pac files being used,
    based on the system registry (win32) or system preferences (OSX).
    """
    pacFiles=[]
    if sys.platform=='win32':
        try:
            import _winreg as winreg#used from python 2.0-2.6
        except:
            import winreg#used from python 2.7 onwards
        net = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        )
        nSubs, nVals, lastMod = winreg.QueryInfoKey(net)
        subkeys={}
        for i in range(nVals):
            thisName, thisVal, thisType=winreg.EnumValue(net,i)
            subkeys[thisName]=thisVal
        if 'AutoConfigURL' in subkeys.keys() and len(subkeys['AutoConfigURL'])>0:
            pacFiles.append(subkeys['AutoConfigURL'])
    elif sys.platform=='darwin':
        import plistlib
        sysPrefs = plistlib.readPlist('/Library/Preferences/SystemConfiguration/preferences.plist')
        networks=sysPrefs['NetworkServices']
        #loop through each possible network (e.g. Ethernet, Airport...)
        for network in networks.items():
            netKey, network=network#the first part is a long identifier
            if 'ProxyAutoConfigURLString' in network['Proxies'].keys():
                pacFiles.append(network['Proxies']['ProxyAutoConfigURLString'])
    return pacFiles

def getWpadFiles():
    """
    Return possible pac file locations from the standard set of .wpad locations

    NB this method only uses the DNS method to search, not DHCP queries, and
    so may not find all possible .pac locations.

    See http://en.wikipedia.org/wiki/Web_Proxy_Autodiscovery_Protocol
    """
    domainParts = socket.gethostname().split('.')
    pacURLs=[]
    for ii in range(len(domainParts)):
        domain = '.'.join(domainParts[ii:])
        pacURLs.append("http://wpad."+domain+"/wpad.dat")
    return pacURLs

def proxyFromPacFiles(pacURLs=[],URL=None):
    """Attempts to locate and setup a valid proxy server from pac file URLs

    :Parameters:

        - pacURLs : list

            List of locations (URLs) to look for a pac file. This might come from
            :func:`~psychopy.connections.getPacFiles` or
            :func:`~psychopy.connections.getWpadFiles`.

        - URL : string

            The URL to use when testing the potential proxies within the files

    :Returns:

        - A urllib2.ProxyHandler if successful (and this will have been added as
        an opener to the urllib2.
        - -1 if no proxy was found in the files that allowed successful connection
    """

    if pacURLs==[]:#if given none try to find some
        pacURLs = getPacFiles()
    if pacURLs==[]:#if still empty search for wpad files
        pacURLs = getWpadFiles()
        #for each file search for valid urls and test them as proxies
    for thisPacURL in pacURLs:
        logging.debug('proxyFromPacFiles is searching file:\n  %s' %thisPacURL)
        try:
            response = urllib2.urlopen(thisPacURL, timeout=5.0)
        except urllib2.URLError:
            logging.debug("Failed to find PAC URL '%s' " %thisPacURL)
            continue
        pacStr = response.read()
        #find the candidate PROXY strings (valid URLS)
        possProxies = re.findall(r"PROXY [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{4}", pacStr)
        for thisPoss in possProxies:
            proxUrl = 'http://'+thisPoss[6:]
            handler=urllib2.ProxyHandler({'http':proxUrl})
            if testProxy(handler)==True:
                logging.debug('successfully loaded: %s' %proxUrl)
                urllib2.install_opener(urllib2.build_opener(handler))
                return handler
    return False

def setupProxy():
    """Set up the urllib proxy if possible.

     The function will use the following methods in order to try and determine proxies:
        #. standard urllib2.urlopen (which will use any statically-defined http-proxy settings)
        #. previous stored proxy address (in prefs)
        #. proxy.pac files if these have been added to system settings
        #. auto-detect proxy settings (WPAD technology)

     .. note:
        This can take time, as each failed attempt to set up a proxy involves trying to load a URL and timing out. Best
        to do in a separate thread.

    :Returns:

        True (success) or False (failure)
    """
    global proxies
    #try doing nothing
    proxies=urllib2.ProxyHandler(urllib2.getproxies())
    if testProxy(proxies) is True:
        logging.debug("Using standard urllib2 (static proxy or no proxy required)")
        urllib2.install_opener(urllib2.build_opener(proxies))#this will now be used globally for ALL urllib2 opening
        return 1

    #try doing what we did last time
    if len(prefs.connections['proxy'])>0:
        proxies=urllib2.ProxyHandler({'http': prefs.connections['proxy']})
        if testProxy(proxies) is True:
            logging.debug('Using %s (from prefs)' %(prefs.connections['proxy']))
            urllib2.install_opener(urllib2.build_opener(proxies))#this will now be used globally for ALL urllib2 opening
            return 1
        else:
            logging.debug("Found a previous proxy but it didn't work")

    #try finding/using a proxy.pac file
    pacURLs=getPacFiles()
    logging.debug("found pac files: %s" %pacURLs)
    proxies=proxyFromPacFiles(pacURLs)
    if proxies and hasattr(proxies, 'proxies') and len(proxies.proxies['http'])>0:
        #save that proxy for future
        prefs.connections['proxy']=proxies.proxies['http']
        prefs.saveUserPrefs()
        logging.debug('Using %s (from proxy PAC file)' %(prefs.connections['proxy']))
        return 1

    #try finding/using 'auto-detect proxy'
    pacURLs=getWpadFiles()
    proxies=proxyFromPacFiles(pacURLs)
    if proxies and hasattr(proxies, 'proxies') and len(proxies.proxies['http'])>0:
        #save that proxy for future
        prefs.connections['proxy']=proxies.proxies['http']
        prefs.saveUserPrefs()
        logging.debug('Using %s (from proxy auto-detect)' %(prefs.connections['proxy']))
        return 1

    proxies=0
    return 0

if __name__=='__main__':
    logging.console.setLevel(logging.DEBUG)
    t0=time.time()
    print setupProxy()
    print 'that took %.2fs' %(time.time()-t0)
