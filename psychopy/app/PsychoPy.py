#!/usr/bin/env python

# Ensure 2.8 version of wx
import wxversion
wxversion.ensureMinimal('2.8')
import wx

import sys, os, threading, time, platform
from keybindings import *
import psychopy, coder, builder
from psychopy.preferences import *
import wxIDs#handles for GUI controls
import urllib2 #for usage stats


links={
    wxIDs.psychopyHome:"http://www.psychopy.org/",
    wxIDs.psychopyReference:"http://www.psychopy.org/reference",
    wxIDs.psychopyTutorial:"http://www.psychopy.org/home.php/Docs/Tutorials"
    }
    
class PsychoSplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, app):
        self.app=app
        splashFile = os.path.join(self.app.prefs.paths['resources'], 'psychopySplash.png')
        aBitmap = wx.Image(name = splashFile).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.NO_BORDER
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 0, None)
        #setup statusbar  
        self.SetBackgroundColour('WHITE')
        self.status = wx.StaticText(self, -1, "Initialising PsychoPy and Libs", 
                                    wx.Point(0,250),#splash image is 640x240
                                    wx.Size(520, 20), wx.ALIGN_LEFT|wx.ALIGN_TOP)
        self.status.SetMinSize(wx.Size(520,20))
        self.Fit()
        self.Close()
        
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
    if proxy is None: proxies = urllib2.getproxies()
    else: proxies={'http':proxy}
    #build the url opener with proxy and cookie handling
    opener = urllib2.build_opener(
        urllib2.ProxyHandler(proxies))    
    urllib2.install_opener(opener)
    headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    
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
        req = urllib2.Request(URL, None, headers)
        page = urllib2.urlopen(req)#proxies
    except:
        pass#maybe proxy is wrong, maybe no internet connection etc...
        
class PsychoPyApp(wx.App):
    def OnInit(self):
        mainFrame = 'builder'
        if len(sys.argv)>1:
            if sys.argv[1]==__name__:
                args = sys.argv[2:] # program was excecuted as "python.exe PsychoPyIDE.py %1'
            else:
                args = sys.argv[1:] # program was excecuted as "PsychoPyIDE.py %1'

            #choose which frame to start with
            if args[0] in ['builder', '--builder', '-b']:
                    mainFrame='builder'
                    args = args[1:]#can remove that argument
            elif args[0][-7:]=='.psyExp':
                    mainFrame='builder'
            elif args[0] in ['coder','--coder', '-c']:
                    mainFrame='coder'
                    args = args[1:]#can remove that argument
            elif args[0][-3:]=='.py':
                    mainFrame='coder'
        else:
            args=[]
        self.SetAppName('PsychoPy')
        #set default paths and import options
        self.prefs = Preferences() #from preferences.py
        splash = PsychoSplashScreen(self)
        if splash:
            splash.Show()
        #create frame(s) for coder/builder as necess
        self.coder=None
        self.builder=None
        self.IDs=wxIDs
        self.keys=keys
        if mainFrame == 'coder': self.newCoderFrame(None, args)
        else: self.newBuilderFrame(None, args)
        
        #send anonymous info to www.psychopy.org/usage.php
        #please don't disable this - it's important for PsychoPy's development
        if self.prefs.connections['allowUsageStats']:
            statsThread = threading.Thread(target=sendUsageStats, args=(self.prefs.connections['proxy'],))
            statsThread.start()
        
        """This is in wx demo. Probably useful one day.
        #---------------------------------------------
        def ShowTip(self):
            config = GetConfig()
            showTipText = config.Read("tips")
            if showTipText:
                showTip, index = eval(showTipText)
            else:
                showTip, index = (1, 0)
                
            if showTip:
                tp = wx.CreateFileTipProvider(opj("data/tips.txt"), index)
                ##tp = MyTP(0)
                showTip = wx.ShowTip(self, tp)
                index = tp.GetCurrentTip()
                config.Write("tips", str( (showTip, index) ))
                config.Flush()"""
        
        return True
    def newCoderFrame(self, event=None, filelist=None):
        #NB a frame doesn't have an app as a parent
        if self.coder==None:
            self.coder = coder.CoderFrame(None, -1, 
                                  title="PsychoPy Coder (IDE) (v%s)" %psychopy.__version__,
                                  files = filelist, app=self)         
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
    def newBuilderFrame(self, event=None, fileList=None):    
        #NB a frame doesn't have an app as a parent
        if self.builder==None:
            self.builder = builder.BuilderFrame(None, -1, 
                                  title="PsychoPy Experiment Builder",
                                  files = fileList, app=self)       
        self.builder.Show(True)
        self.SetTopWindow(self.builder)
    def MacOpenFile(self,fileName):
        if fileName.endswith('.py'):
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.builder.setCurrentDoc(fileName)
    def quit(self, event=None):
        self.prefs.saveAppData()
        for frame in [self.coder, self.builder]:
            if hasattr(frame,'closeFrame'): 
                frame.closeFrame()#this executes the saving of files etc
                frame.Destroy()#then destroy it
        #todo: work out correct operation of closing wrt multiple frames etc...
    def showPrefs(self, event):
        prefsDlg = PreferencesDlg(app=self)
        prefsDlg.Show()

    def showAbout(self, event):
        msg = """PsychoPy %s \nWritten by Jon Peirce.\n
        It has a liberal license; basically, do what you like with it, 
        don't kill me if something doesn't work! :-) But do let me know...
        psychopy-users@googlegroups.com
        """ %psychopy.__version__
        dlg = wx.MessageDialog(None, message=msg,
                              caption = "About PsychoPy", style=wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def showLicense(self, event):
        licFile = open(os.path.join(self.prefs.paths['psychopy'],'LICENSE.txt'))
        licTxt = licFile.read()
        licFile.close()
        dlg = wx.MessageDialog(self, licTxt, "PsychoPy License", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def followLink(self, event):
        wx.LaunchDefaultBrowser(links[event.GetId()])

if __name__=='__main__':
    app = PsychoPyApp(0)
    app.MainLoop()