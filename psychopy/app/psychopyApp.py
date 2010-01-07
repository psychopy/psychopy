#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, psychopy
import StringIO
if sys.argv[-1] in ['-v', '--version']:
    print 'PsychoPy2, version %s (c)Jonathan Peirce, 2009, GNU GPL license' %psychopy.__version__
    sys.exit()
if sys.argv[-1] in ['-h', '--help']:
    print """Starts the PsychoPy2 application.

Usage:  python PsychoPy.py [options] [file]

Without options or files provided starts the psychopy using prefs to
decide on the view(s) to open.  If optional [file] is provided action
depends on the type of the [file]:

 Python script 'file.py' -- opens coder

 Experiment design 'file.psyexp' -- opens builder

Options:
    -c, --coder, coder       opens coder view only
    -b, --builder, builder   opens builder view only

    --version        prints version and exits
    -h, --help       prints this help and exit

"""
    sys.exit()

# Ensure 2.8 version of wx
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal('2.8')
import wx
#NB keep imports to a minimum here because splash screen has not yet shown
#e.g. coder and builder are imported during app.__init__ because they take a while
from psychopy import preferences#needed by splash screen for the path to resources/psychopySplash.png
import sys, os, threading, time, platform

class PsychoSplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self):
        prefs=preferences.Preferences()
        splashFile = os.path.join(prefs.paths['resources'], 'psychopySplash.png')
        aBitmap = wx.Image(name = splashFile).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.NO_BORDER
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 0, None)
        #setup statusbar
        self.SetBackgroundColour('WHITE')
        self.status = wx.StaticText(self, -1, "  Loading libraries...",
                                    wx.Point(0,250),#splash image is 640x240
                                    wx.Size(520, 20), wx.ALIGN_LEFT|wx.ALIGN_TOP)
        self.status.SetMinSize(wx.Size(520,20))
        self.Fit()
        self.Close()
        
class MenuFrame(wx.Frame):
    """A simple, empty frame with a menubar that should be the last frame to close on a mac
    """
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy2"):
        wx.Frame.__init__(self, parent, ID, title, size=(1,1))
        self.app=app

        self.menuBar = wx.MenuBar()

        self.viewMenu = wx.Menu()
        self.menuBar.Append(self.viewMenu, '&View')
        self.viewMenu.Append(self.app.IDs.openBuilderView, "&Open Builder view\t%s" %self.app.keys['switchToBuilder'], "Open a new Builder view")
        wx.EVT_MENU(self, self.app.IDs.openBuilderView,  self.app.showBuilder)
        self.viewMenu.Append(self.app.IDs.openCoderView, "&Open Coder view\t%s" %self.app.keys['switchToCoder'], "Open a new Coder view")
        wx.EVT_MENU(self, self.app.IDs.openCoderView,  self.app.showCoder)
        item=self.viewMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys['quit'], "Terminate the program")
        self.Bind(wx.EVT_MENU, self.app.quit, item)

        self.SetMenuBar(self.menuBar)
        self.Show()

class PsychoPyApp(wx.App):
    def OnInit(self):
        self.version=psychopy.__version__
        self.SetAppName('PsychoPy2')        
        #show splash screen
        splash = PsychoSplashScreen()
        if splash:
            splash.Show()
        #LONG IMPORTS - these need to be imported after splash screen starts (they're slow)
        #but then that they end up being local so keep track in self
        splash.status.SetLabel("  Loading PsychoPy2...")
        from psychopy.monitors import MonitorCenter
        from psychopy.app import coder, builder, wxIDs, connections, urls
        #set default paths and prefs
        self.prefs = preferences.Preferences() #from preferences.py
        self.keys = self.prefs.keys
        self.prefs.pageCurrent = 0  # track last-viewed page of prefs, to return there
        self.IDs=wxIDs
        self.urls=urls.urls
        self.quitting=False
        self.updater=None#create an updater when it's needed
        #setup links for URLs
        #on a mac, don't exit when the last frame is deleted, just show a menu
        if platform.system()=='Darwin':
            self.menuFrame=MenuFrame(parent=None, app=self)
        #get preferred view(s) from prefs and previous view
        if self.prefs.app['defaultView']=='last':
            mainFrame = self.prefs.appData['lastFrame']
        else:
            # configobjValidate should take care of this situation (?), but doesn't:
            if self.prefs.app['defaultView'] in ['last', 'coder', 'builder', 'both']:
                mainFrame = self.prefs.app['defaultView']
            else:
                self.prefs.app['defaultView'] = 'both'
                mainFrame = 'both'
        #then override the main frame by command options and passed files
        scripts=[]; exps=[]
        if len(sys.argv)>1:
            if sys.argv[1]==__name__:
                args = sys.argv[2:] # program was excecuted as "python.exe PsychoPyIDE.py %1'
            else:
                args = sys.argv[1:] # program was excecuted as "PsychoPyIDE.py %1'
            #choose which frame to start with
            if args[0] in ['builder', '--builder', '-b']:
                    mainFrame='builder'
                    args = args[1:]#can remove that argument
            elif args[0] in ['coder','--coder', '-c']:
                    mainFrame='coder'
                    args = args[1:]#can remove that argument
            #did we get .py or .psyexp files?
            elif args[0][-7:]=='.psyexp':
                    mainFrame='builder'
                    exps=[args[0]]
            elif args[0][-3:]=='.py':
                    mainFrame='coder'
                    scripts=[args[0]]
        else:
            args=[]

        self.dpi = int(wx.GetDisplaySize()[0]/float(wx.GetDisplaySizeMM()[0])*25.4)
        if not (50<self.dpi<120): self.dpi=80#dpi was unreasonable, make one up

        #create both frame for coder/builder as necess
        self.coder = self.builder = None
        if mainFrame in ['both', 'coder']: self.showCoder(fileList=scripts)
        if mainFrame in ['both', 'builder']: self.showBuilder(fileList=exps)

        #send anonymous info to www.psychopy.org/usage.php
        #please don't disable this - it's important for PsychoPy's development
        if self.prefs.connections['allowUsageStats']:
            statsThread = threading.Thread(target=connections.sendUsageStats, args=(self.prefs.connections['proxy'],))
            statsThread.start()
        if self.prefs.connections['checkForUpdates']:
            self.updater=connections.Updater(app=self, proxy=self.prefs.connections['proxy'])
            self.updater.suggestUpdate(confirmationDlg=False)#check for updates (silently)
        else: self.updater=False
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

    def showCoder(self, event=None, fileList=None):
        from psychopy.app import coder#have to reimport because it is ony local to __init__ so far
        if self.coder==None:
            self.coder=coder.CoderFrame(None, -1,
                      title="PsychoPy2 Coder (IDE) (v%s)" %self.version,
                      files = fileList, app=self)
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
        self.coder.Raise()
        self.coder.setOutputWindow()#takes control of sys.stdout
    def showBuilder(self, event=None, fileList=None):
        from psychopy.app import builder#have to reimport because it is ony local to __init__ so far
        if self.builder==None:
            self.builder=builder.BuilderFrame(None, -1,
                                  title="PsychoPy2 Experiment Builder",
                                  files = fileList, app=self)
        self.builder.Show(True)
        self.builder.Raise()
        self.SetTopWindow(self.builder)
    def openUpdater(self, event=None):
        from psychopy.app import connections
        dlg = connections.InstallUpdateDialog(parent=None, ID=-1, app=self)
        
    def openMonitorCenter(self,event):
        from psychopy.monitors import MonitorCenter
        frame = MonitorCenter.MainFrame(None,'PsychoPy2 Monitor Center')
        frame.Show(True)
    def MacOpenFile(self,fileName):
        if fileName.endswith('.py'):
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.builder.setCurrentDoc(fileName)
    def quit(self, event=None):
        self.quitting=True
        #see whether any files need saving
        for frame in [self.coder, self.builder]:
            if frame==None: continue
            ok=frame.checkSave()
            if not ok: return#user cancelled quit
        #save info about current frames for next run
        if self.coder and not self.builder:
            self.prefs.appData['lastFrame']='coder'
        elif self.builder and not self.coder:
            self.prefs.appData['lastFrame']='builder'
        else:
            self.prefs.appData['lastFrame']='both'
        #hide the frames then close
        for frame in [self.coder, self.builder]:
            if frame==None: continue
            frame.closeFrame(checkSave=False)#should update (but not save) prefs.appData
            self.prefs.saveAppData()#must do this before destroying the frame?
            frame.Destroy()#because closeFrame actually just Hides the frame
        if platform.system()=='Darwin':
            self.menuFrame.Destroy()
        sys.exit()#really force a quit
    def showPrefs(self, event):
        prefsDlg = preferences.PreferencesDlg(app=self)
        prefsDlg.Show()

    def showAbout(self, event):

        licFile = open(os.path.join(self.prefs.paths['psychopy'],'LICENSE.txt'))
        license = licFile.read()
        licFile.close()

        msg = """For stimulus generation and experimental control in python.

PsychoPy depends on your feedback. If something doesn't work then
let me/us know at psychopy-users@googlegroups.com"""
        info = wx.AboutDialogInfo()
        info.SetName('PsychoPy')
        info.SetVersion('v'+psychopy.__version__)
        info.SetDescription(msg)

        info.SetCopyright('(C) 2002-2009 Jonathan Peirce')
        info.SetWebSite('http://www.psychopy.org')
        info.SetLicence(license)
        info.AddDeveloper('Jonathan Peirce')
        info.AddDeveloper('Yaroslav Halchenko')
        info.AddDeveloper('Jeremy Gray')
        info.AddDocWriter('Jonathan Peirce')

        wx.AboutBox(info)

    def followLink(self, event=None, url=None):
        """Follow either an event id (which should be a key to a url defined in urls.py)
        or follow a complete url (a string beginning "http://")
        """
        if event!=None:
            wx.LaunchDefaultBrowser(self.urls[event.GetId()])
        elif url!=None:
            wx.LaunchDefaultBrowser(url)
            

if __name__=='__main__':
    app = PsychoPyApp(0)
    app.MainLoop()
