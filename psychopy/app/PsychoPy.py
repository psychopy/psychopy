#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, psychopy
if sys.argv[-1] in ['-v', '--version']:
    print 'PsychoPy version %s (c)Jonathan Peirce, 2009, GNU GPL license' %psychopy.__version__
    sys.exit()
if sys.argv[-1] in ['-h', '--help']:
    print "Haven't written this yet"
    sys.exit()

# Ensure 2.8 version of wx
import wxversion
wxversion.ensureMinimal('2.8')
import wx

import sys, os, threading, time, platform
from psychopy.preferences import Preferences
#other app subpackages needs to be imported as explicitly in app 
from psychopy.app import coder, builder, keybindings, wxIDs
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
        self.version=psychopy.__version__
        self.SetAppName('PsychoPy2')
        #set default paths and import options
        self.prefs = Preferences() #from preferences.py        
        self.IDs=wxIDs
        self.keys=keybindings
                    
        #get preferred view(s) from prefs and previous view
        if self.prefs.app['defaultView']=='last':
            mainFrame = self.prefs.appData['lastFrame']
        else: mainFrame= self.prefs.app['defaultView']
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
            elif args[0][-7:]=='.psyExp':
                    mainFrame='builder'
                    exps=[args[0]]
            elif args[0][-3:]=='.py':
                    mainFrame='coder'
                    scripts=[args[0]]
        else:
            args=[]
            
        splash = PsychoSplashScreen(self)
        if splash:
            splash.Show()
            
        #create both frame for coder/builder as necess
        self.coder=coder.CoderFrame(None, -1, 
                                  title="PsychoPy2 Coder (IDE) (v%s)" %self.version,
                                  files = scripts, app=self) 
        self.builder=builder.BuilderFrame(None, -1, 
                                  title="PsychoPy2 Experiment Builder",
                                  files = exps, app=self)            
        if mainFrame in ['both','coder']: self.showCoder()
        if mainFrame in ['both','builder']: self.showBuilder()
                        
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
    def showCoder(self, event=None, filelist=None):   
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
        self.coder.Raise()
        self.coder.setOutputWindow()#takes control of sys.stdout
    def showBuilder(self, event=None, fileList=None):         
        self.builder.Show(True)
        self.builder.Raise()
        self.SetTopWindow(self.builder)
    def openMonitorCenter(self,event):
        from monitors import MonitorCenter
        frame = MonitorCenter.MainFrame(None,'PsychoPy2 Monitor Center')
        frame.Show(True)
    def MacOpenFile(self,fileName):
        if fileName.endswith('.py'):
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.builder.setCurrentDoc(fileName)
    def quit(self, event=None):
        #see whether any files need saving
        for frame in [self.coder, self.builder]:
            ok=frame.checkSave()
            if not ok: return#user cancelled quit 
        #save info about current frames for next run
        if self.coder.IsShown() and not self.builder.IsShown(): 
            self.prefs.appData['lastFrame']='coder'
        elif self.builder.IsShown() and not self.coder.IsShown(): 
            self.prefs.appData['lastFrame']='builder'
        else:
            self.prefs.appData['lastFrame']='both'
        #hide the frames then close
        for frame in [self.coder, self.builder]:
            frame.closeFrame(checkSave=False)#should update (but not save) prefs.appData
            self.prefs.saveAppData()#must do this before destroying the frame?
            frame.Destroy()#because closeFrame actually just Hides the frame            
        
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
        item = self.fileMenu.Append(wx.ID_SAVE,   "&Save prefs\t%s" %app.keys.save)
        self.Bind(wx.EVT_MENU, self.save, item)
        item = self.fileMenu.Append(wx.ID_CLOSE,   "&Close (prefs)\t%s" %app.keys.close)
        self.Bind(wx.EVT_MENU, self.close, item)
        self.fileMenu.AppendSeparator()
        item = self.fileMenu.Append(-1, "&Quit (entire app)\t%s" %app.keys.quit, "Terminate the application")
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
    
if __name__=='__main__':
    app = PsychoPyApp(0)
    app.MainLoop()