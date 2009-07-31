import wx, sys, os
from keybindings import *
import wxIDs#handles for GUI controls
import psychopy, coder, builder
from psychopy.preferences import *

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
        
        #set default paths and import options
        self.prefs = Preferences() #from preferences.py
        splash = PsychoSplashScreen(self)
        if splash:
            splash.Show()
        #create frame(s) for coder/builder as necess
        self.coder=None
        self.builder=None
        self.IDs=wxIDs
        if mainFrame == 'coder': self.newCoderFrame(args)
        else: self.newBuilderFrame(args)
        
        
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
    def newCoderFrame(self, filelist=None):
        #NB a frame doesn't have an app as a parent
        self.coder = coder.CoderFrame(None, -1, 
                                  title="PsychoPy Coder (IDE) (v%s)" %psychopy.__version__,
                                  files = filelist, app=self)         
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
    def newBuilderFrame(self, fileList=None):    
        #NB a frame doesn't have an app as a parent
        self.builder = builder.BuilderFrame(None, -1, 
                                  title="PsychoPy Experiment Builder",
                                  files = fileList, app=self)       
        self.builder.Show(True)
        self.SetTopWindow(self.builder)
    def MacOpenFile(self,fileName):
        self.frame.setCurrentDoc(fileName)
    def quit(self):
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