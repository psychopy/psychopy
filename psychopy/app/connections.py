# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import urllib2, time, platform, sys, zipfile, os
import psychopy
import wx

class UpdatesDlg(wx.MessageDialog):
    def __init__(self, app, updateInfo):
        wx.MessageDialog.__init__(self, parent=app,
            style=wx.YES_NO|wx.CANCEL,
            message='test', caption='Warning')

#        self.outStream = wx.TextCtrl(parent=self,
        vbox = wx.BoxSizer(wx.VERTICAL)
        #add buttons
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        updateButton = wx.Button(self, wx.ID_YES, 'Update', size=(100, 30))
        cancelButton = wx.Button(self, wx.ID_CANCEL, 'Next time', size=(100, 30))
        skipButton = wx.Button(self, wx.ID_NO, 'Skip version', size=(100, 30))
#        skipButton.Bind(wx.EVT_BUTTON, self.onNo)
        hbox.Add(skipButton, 1, wx.LEFT, 5)
        hbox.Add(cancelButton, 1, wx.LEFT, 5)
        hbox.Add(updateButton, 1)

        vbox.Add(hbox)
        self.SetSizerAndFit(vbox)

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

def unzip_file_into_dir(file, dir):
    os.mkdir(dir, 0777)
    zfobj = zipfile.ZipFile(file)
    for name in zfobj.namelist():
        if name.endswith('/'):
            os.mkdir(os.path.join(dir, name))
        else:
            outfile = open(os.path.join(dir, name), 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

def updatePsychoPy():

    import subprocess
    os.chdir('/Users/jwp/Desktop/testPkg')

    p = subprocess.Popen([sys.executable,'setup.py','install'])
#        sys.argv=['-Z', '-U',#unzip, upgrade
#            '-f', 'http://code.google.com/p/psychopy/downloads/list',#
#            'psychopy']
#        msg = "#!%s\n" %sys.executable
#        msg+= """__requires__ = 'setuptools==0.6c9'
#import sys

#    from pkg_resources import load_entry_point
#    sys.argv = ['-Z', '-U',#unzip, upgrade
#            '-f', 'http://code.google.com/p/psychopy/downloads/list',#
#            'psychopy']
#    ok=load_entry_point('', 'console_scripts', 'easy_install')()

#    msg= 'returns: %s' %ok
#    dlg = wx.MessageDialog(None, style=wx.OK|wx.CENTER,
#        message=msg, caption='Update')
    #dlg.Destroy()


def checkForUpdates(app, proxy=None, currVersion=psychopy.__version__):

    sys.argv = ['junk', '-Z', '-U',#unzip, upgrade
            '-f', 'http://code.google.com/p/psychopy/downloads/list',#
            'psychopy']
    #check for proxies
    if proxy is None: proxies = urllib2.getproxies()
    else: proxies={'http':proxy}
    opener = urllib2.build_opener(
        urllib2.ProxyHandler(proxies))
    urllib2.install_opener(opener)
    headers = {'User-Agent' : 'PsychoPy2'}
    #open page
    URL = "http://www.psychopy.org/version.txt"
    req = urllib2.Request(URL, None, headers)
    page = urllib2.urlopen(req)#proxies

    #parse that as a dictionary
    info={}
    for line in page.readlines():
        key, keyInfo = line.split(':')
        info[key]=keyInfo.replace('\n', '')

#    if info['version']>currVersion and info['version']!=app.prefs.appData['skipVersion']:
    if True:
        msg = "PsychoPy v%s is available (you are running %s). " %(info['version'], currVersion)
        msg+= "For details see full changelog at\nhttp://www.psychopy.org/changelog.html"
        msg+= "\n\nDo you want to update?\n\nYes = install\nCancel = not now\nNo = skip this version"
        dlg = dialogs.MessageDialog(None, message=msg, type='Warning', title='New version available')
        retVal = dlg.ShowModal()
        if retVal==wx.ID_YES: updatePsychoPy()
        elif retVal==wx.ID_CANCEL:pass
        elif retVal==wx.ID_NO: app.prefs.appData['skipVersion']=info['version']

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
    try:
        req = urllib2.Request(URL)
        page = urllib2.urlopen(req)#proxies
    except:
        print "Failed to contact psychopy.org/usage.php. May be proxy error (proxy=%s)" %proxy
        pass#maybe proxy is wrong, maybe no internet connection etc...
