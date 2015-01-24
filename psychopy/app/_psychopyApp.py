#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, psychopy
import copy

if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal('2.8') # because this version has agw
import wx
try:
    from agw import advancedsplash as AS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.advancedsplash as AS
#NB keep imports to a minimum here because splash screen has not yet shown
#e.g. coder and builder are imported during app.__init__ because they take a while
from psychopy import preferences, logging#needed by splash screen for the path to resources/psychopySplash.png
from psychopy.app import connections
import sys, os, threading

# knowing if the user has admin priv is generally a good idea for security.
# not actually needed; psychopy should never need anything except normal user
# see older versions for code to detect admin (e.g., v 1.80.00)

class MenuFrame(wx.Frame):
    """A simple, empty frame with a menubar that should be the last frame to close on a mac
    """
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy2"):
        wx.Frame.__init__(self, parent, ID, title, size=(1,1))
        self.app=app

        self.menuBar = wx.MenuBar()

        self.viewMenu = wx.Menu()
        self.menuBar.Append(self.viewMenu, _translate('&View'))
        self.viewMenu.Append(self.app.IDs.openBuilderView, _translate("&Open Builder view\t%s") %self.app.keys['switchToBuilder'], _translate("Open a new Builder view"))
        wx.EVT_MENU(self, self.app.IDs.openBuilderView,  self.app.showBuilder)
        self.viewMenu.Append(self.app.IDs.openCoderView, _translate("&Open Coder view\t%s") %self.app.keys['switchToCoder'], _translate("Open a new Coder view"))
        wx.EVT_MENU(self, self.app.IDs.openCoderView,  self.app.showCoder)
        item=self.viewMenu.Append(wx.ID_EXIT, _translate("&Quit\t%s") %self.app.keys['quit'], _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, self.app.quit, item)

        self.SetMenuBar(self.menuBar)
        self.Show()

class _Showgui_Hack():
    """Class with side-effect of restoring wx window switching/launching under wx-3.0

    - might only be needed on some platforms (Mac 10.9.4 needs it for me);
    - needs to be launched as an external script
    - needs to be separate code (seg-faults as method of PsychoPyApp, or in-lined code)
    - unlear why it works or what the deeper issue is, blah
    - called at end of PsychoPyApp.onInit()
    """
    def __init__(self):
        from psychopy import core
        import os
        # should be writable:
        noopPath = os.path.join(psychopy.prefs.paths['userPrefsDir'], 'showgui_hack.py')
        # code to open & immediately close a gui (= invisibly):
        if not os.path.isfile(noopPath):
            code = """from psychopy import gui
                dlg = gui.Dlg().Show()  # non-blocking
                try: dlg.Destroy()  # might as well
                except: pass""".replace('    ', '')
            with open(noopPath, 'wb') as fd:
                fd.write(code)
        core.shellCall([sys.executable, noopPath])  # append 'w' for pythonw seems not needed

class PsychoPyApp(wx.App):
    def __init__(self, arg=0, **kwargs):
        wx.App.__init__(self, arg)
        self.onInit(**kwargs)

    def onInit(self, showSplash=True, testMode=False):
        """
        :Parameters:

          testMode: bool
            If set to True then startup wizard won't appear and stdout/stderr
            won't be redirected to the Coder
        """
        self.version=psychopy.__version__
        self.SetAppName('PsychoPy2')

        # import localization after wx:
        from psychopy.app import localization  # needed by splash screen
        self.localization = localization
        self.locale = localization.wxlocale
        self.locale.AddCatalog(self.GetAppName())

        #set default paths and prefs
        self.prefs = psychopy.prefs
        if self.prefs.app['debugMode']:
            logging.console.setLevel(logging.DEBUG)
        self.testMode = testMode #indicates whether we're running for testing purposes

        if showSplash:
            #show splash screen
            splashFile = os.path.join(self.prefs.paths['resources'], 'psychopySplash.png')
            splashBitmap = wx.Image(name = splashFile).ConvertToBitmap()
            splash = AS.AdvancedSplash(None, bitmap=splashBitmap, timeout=3000, style=AS.AS_TIMEOUT|wx.FRAME_SHAPED,
                                      shadowcolour=wx.RED)#could use this in future for transparency
            splash.SetTextPosition((10,240))
            splash.SetText(_translate("  Loading libraries..."))
        else:
            splash=None

        #LONG IMPORTS - these need to be imported after splash screen starts (they're slow)
        #but then that they end up being local so keep track in self
        if splash: splash.SetText(_translate("  Loading PsychoPy2..."))
        from psychopy import compatibility
        from psychopy.app import coder, builder, dialogs, wxIDs, urls #import coder and builder here but only use them later
        self.keys = self.prefs.keys
        self.prefs.pageCurrent = 0  # track last-viewed page of prefs, to return there
        self.IDs=wxIDs
        self.urls=urls.urls
        self.quitting=False
        #check compatibility with last run version (before opening windows)
        self.firstRun = False

        if '--firstrun' in sys.argv:
            del sys.argv[sys.argv.index('--firstrun')]
            self.firstRun = True
        if 'lastVersion' not in self.prefs.appData.keys():
            last=self.prefs.appData['lastVersion']='1.73.04'#must be before 1.74.00
            self.firstRun = True
        else:
            last=self.prefs.appData['lastVersion']

        if self.firstRun and not self.testMode:
            self.firstrunWizard()

        #setup links for URLs
        #on a mac, don't exit when the last frame is deleted, just show a menu
        if sys.platform=='darwin':
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
        #fetch prev files if that's the preference
        if self.prefs.coder['reloadPrevFiles']:
            scripts=self.prefs.appData['coder']['prevFiles']
        else: scripts=[]
        if self.prefs.builder['reloadPrevExp'] and ('prevFiles' in self.prefs.appData['builder'].keys()):
            exps=self.prefs.appData['builder']['prevFiles']
        else:
            exps=[]
        #then override the prev files by command options and passed files
        if len(sys.argv)>1:
            if sys.argv[1]==__name__:
                args = sys.argv[2:] # program was executed as "python.exe PsychoPyIDE.py %1'
            else:
                args = sys.argv[1:] # program was executed as "PsychoPyIDE.py %1'
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

        if sys.platform=='win32': #wx.SYS_DEFAULT_GUI_FONT is default GUI font in Win32
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        else:
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        if hasattr(self._mainFont, 'Larger'):
            # Font.Larger is available since wyPython version 2.9.1
            # PsychoPy still supports 2.8 (see ensureMinimal above)
            self._mainFont = self._mainFont.Larger()
        self._codeFont = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
        self._codeFont.SetFaceName(self.prefs.coder['codeFont'])
        self._codeFont.SetPointSize(self._mainFont.GetPointSize()) #unify font size

        #create both frame for coder/builder as necess
        if splash:
            splash.SetText(_translate("  Creating frames..."))
        self.coder = None
        self.builderFrames = []
        self.copiedRoutine=None
        self.allFrames=[]#these are ordered and the order is updated with self.onNewTopWindow
        if mainFrame in ['both', 'coder']:
            self.showCoder(fileList=scripts)
        if mainFrame in ['both', 'builder']:
            self.showBuilder(fileList=exps)

        #send anonymous info to www.psychopy.org/usage.php
        #please don't disable this - it's important for PsychoPy's development
        self._latestAvailableVersion=None
        self.updater=None
        if self.prefs.connections['checkForUpdates'] or self.prefs.connections['allowUsageStats']:
            connectThread = threading.Thread(target=connections.makeConnections, args=(self,))
            connectThread.start()

        ok, msg = compatibility.checkCompatibility(last, self.version, self.prefs, fix=True)
        if not ok and not self.firstRun and not self.testMode:  #tell the user what has changed
            dlg = dialogs.MessageDialog(parent=None,message=msg,type='Info', title=_translate("Compatibility information"))
            dlg.ShowModal()

        if self.prefs.app['showStartupTips'] and not self.testMode:
            tipFile = os.path.join(self.prefs.paths['resources'], _translate("tips.txt"))
            tipIndex = self.prefs.appData['tipIndex']
            tp = wx.CreateFileTipProvider(tipFile, tipIndex)
            showTip = wx.ShowTip(None, tp)
            self.prefs.appData['tipIndex'] = tp.GetCurrentTip()
            self.prefs.saveAppData()
            self.prefs.app['showStartupTips'] = showTip
            self.prefs.saveUserPrefs()

        if self.prefs.connections['checkForUpdates']:
            self.Bind(wx.EVT_IDLE, self.checkUpdates)
        else:
            self.Bind(wx.EVT_IDLE, self.onIdle)

        # doing this once subsequently enables the app to open & switch among
        # wx-windows on some platforms (Mac 10.9.4) with wx-3.0:
        if wx.version() >= '3.0' and sys.platform == 'darwin':
            _Showgui_Hack()  # returns ~immediately, no display
            # focus stays in never-land, so bring back to the app:
            if mainFrame in ['both', 'builder']:
                self.showBuilder()
            else:
                self.showCoder()

        return True

    def _wizard(self, selector, arg=''):
        from psychopy import core
        wizard = os.path.join(self.prefs.paths['psychopy'], 'tools', 'wizard.py')
        so, se = core.shellCall([sys.executable, wizard, selector, arg], stderr=True)
        if se and self.prefs.app['debugMode']:
            print se  # stderr contents; sometimes meaningless
    def firstrunWizard(self):
        self._wizard('--config', '--firstrun')
        # wizard typically creates html report file, but user can manually skip
        reportPath = os.path.join(self.prefs.paths['userPrefsDir'], 'firstrunReport.html')
        if os.path.exists(reportPath):
            report = open(reportPath, 'r').read()
            if 'Configuration problem' in report:
                # fatal error was encountered (currently only if bad drivers), so
                # before psychopy shuts down, ensure wizard will be triggered again:
                del self.prefs.appData['lastVersion']
                self.prefs.saveAppData()
    def benchmarkWizard(self, evt=None):
        self._wizard('--benchmark')
    def checkUpdates(self, evt):
        #if we have internet and haven't yet checked for updates then do so
        if self._latestAvailableVersion not in [-1, None]:#we have a network connection but not yet tried an update
            #change IDLE routine so we won't come back here
            self.Unbind(wx.EVT_IDLE)#unbind all EVT_IDLE methods from app
            self.Bind(wx.EVT_IDLE, self.onIdle)
            #create updater (which will create dialogs as needed)
            self.updater=connections.Updater(app=self)
            self.updater.latest=self._latestAvailableVersion
            self.updater.suggestUpdate(confirmationDlg=False)
        evt.Skip()
    def onIdle(self, evt):
        evt.Skip()
    def getPrimaryDisplaySize(self):
        """Get the size of the primary display (whose coords start (0,0))
        """
        return list(wx.Display(0).GetGeometry())[2:]
    def makeAccelTable(self):
        """Makes a standard accelorator table and returns it. This then needs
        to be set for the Frame using self.SetAccelerator(table)
        """
        def parseStr(inStr):
            accel=0
            if 'ctrl' in inStr.lower():
                accel += wx.ACCEL_CTRL
            if 'shift' in inStr.lower():
                accel += wx.ACCEL_SHIFT
            if 'alt' in inStr.lower():
                accel += wx.ACCEL_ALT
            return accel, ord(inStr[-1])
        #create a list to link IDs to key strings
        keyCodesDict = {}
        keyCodesDict[self.keys['copy']] = wx.ID_COPY
        keyCodesDict[self.keys['cut']] = wx.ID_CUT
        keyCodesDict[self.keys['paste']] = wx.ID_PASTE
        keyCodesDict[self.keys['undo']] = wx.ID_UNDO
        keyCodesDict[self.keys['redo']] = wx.ID_REDO
        keyCodesDict[self.keys['save']] = wx.ID_SAVE
        keyCodesDict[self.keys['saveAs']] = wx.ID_SAVEAS
        keyCodesDict[self.keys['close']] = wx.ID_CLOSE
        keyCodesDict[self.keys['redo']] = wx.ID_REDO
        keyCodesDict[self.keys['quit']] = wx.ID_EXIT
        #parse the key strings and convert to accelerator entries
        entries = []
        for keyStr, code in keyCodesDict.items():
            mods, key = parseStr(keyStr)
            entry = wx.AcceleratorEntry(mods, key, code)
            entries.append(entry)
        table = wx.AcceleratorTable(entries)
        return table
    def showCoder(self, event=None, fileList=None):
        from psychopy.app import coder#have to reimport because it is ony local to __init__ so far
        if self.coder is None:
            self.coder=coder.CoderFrame(None, -1,
                      title="PsychoPy2 Coder (IDE) (v%s)" %self.version,
                      files = fileList, app=self)
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
        self.coder.Raise()
        self.coder.setOutputWindow()#takes control of sys.stdout
        if self.coder not in self.allFrames:
            self.allFrames.append(self.coder)
    def newBuilderFrame(self, event=None, fileName=None):
        from psychopy.app import builder#have to reimport because it is ony local to __init__ so far
        thisFrame = builder.BuilderFrame(None, -1,
                                  title="PsychoPy2 Experiment Builder (v%s)" %self.version,
                                  fileName=fileName, app=self)
        thisFrame.Show(True)
        thisFrame.Raise()
        self.SetTopWindow(thisFrame)
        self.builderFrames.append(thisFrame)
        self.allFrames.append(thisFrame)
    def showBuilder(self, event=None, fileList=[]):
        from psychopy.app import builder#have to reimport because it is ony local to __init__ so far
        for fileName in fileList:
            if os.path.isfile(fileName):
                self.newBuilderFrame(fileName=fileName)
        #create an empty Builder view if needed
        if len(self.builderFrames)==0:
            self.newBuilderFrame()
        #loop through all frames, from the back bringing each forward
        for thisFrame in self.allFrames:
            if thisFrame.frameType!='builder':continue
            thisFrame.Show(True)
            thisFrame.Raise()
            self.SetTopWindow(thisFrame)
    #def showShell(self, event=None):
    #    from psychopy.app import ipythonShell#have to reimport because it is ony local to __init__ so far
    #    if self.shell is None:
    #        self.shell = ipythonShell.ShellFrame(None, -1,
    #            title="IPython in PsychoPy (v%s)" %self.version, app=self)
    #        self.shell.Show()
    #        self.shell.SendSizeEvent()
    #    self.shell.Raise()
    #    self.SetTopWindow(self.shell)
    #    self.shell.SetFocus()
    def openIPythonNotebook(self, event=None):
        """Note that right now this is bad because it ceases all activity in the
        main wx loop and the app has to be quit. We need it to run from a separate
        process? The necessary depends (zmq and tornado) were included from v1.78
        onwards in the standalone
        """
        import IPython.frontend.html.notebook.notebookapp
        instance = IPython.frontend.html.notebook.notebookapp.launch_new_instance()
    def openUpdater(self, event=None):
        from psychopy.app import connections
        dlg = connections.InstallUpdateDialog(parent=None, ID=-1, app=self)

    def colorPicker(self, event=None):
        """Opens system color-picker, sets clip-board and parent.new_rgb = string [r,g,b].

        Note: units are psychopy -1..+1 rgb units to three decimal places, preserving 24-bit color
        """
        class ColorPicker(wx.Panel):
            def __init__(self, parent):
                wx.Panel.__init__(self, parent, wx.ID_ANY)
                rgb = 'None'
                dlg = wx.ColourDialog(self)
                dlg.GetColourData().SetChooseFull(True)
                if dlg.ShowModal() == wx.ID_OK:
                    data = dlg.GetColourData()
                    rgb = data.GetColour().Get()
                    rgb = map(lambda x: "%.3f" % ((x-127.5)/127.5),list(rgb))
                    rgb = '['+','.join(rgb)+']'
                    if wx.TheClipboard.Open():
                        #http://wiki.wxpython.org/AnotherTutorial#wx.TheClipboard
                        wx.TheClipboard.Clear()
                        wx.TheClipboard.SetData(wx.TextDataObject(str(rgb)))
                        wx.TheClipboard.Close()
                dlg.Destroy()
                parent.new_rgb = rgb
        frame = wx.Frame(None, wx.ID_ANY, "Color picker", size=(0,0)) # not shown
        ColorPicker(frame)
        new_rgb = frame.new_rgb # string; also on system clipboard, try wx.TheClipboard
        frame.Destroy()
        return new_rgb
    def openMonitorCenter(self,event):
        from psychopy.monitors import MonitorCenter
        self.monCenter = MonitorCenter.MainFrame(None,'PsychoPy2 Monitor Center')
        self.monCenter.Show(True)
    def MacOpenFile(self,fileName):
        logging.debug('PsychoPyApp: Received Mac file dropped event')
        if fileName.endswith('.py'):
            if self.coder is None:
                self.showCoder()
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.newBuilderFrame(fileName=fileName)
    def terminateHubProcess(self):
        """
        Send a UDP message to iohub informing it to exit.

        Use this when force quiting the experiment script process so iohub
        knows to exit as well.

        If message is not sent within 1 second, or the iohub server
        address in incorrect,the issue is logged.
        """
        sock=None
        try:
            logging.debug('PsychoPyApp: terminateHubProcess called.')
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            iohub_address='127.0.0.1', 9034
            import msgpack
            tx_data=msgpack.Packer().pack(('STOP_IOHUB_SERVER',))
            return sock.sendto(tx_data,iohub_address)
        except socket.error,e:
            logging.debug('PsychoPyApp: terminateHubProcess socket.error: %s'%(str(e)))
        except socket.herror,e:
            logging.debug('PsychoPyApp: terminateHubProcess socket.herror: %s'%(str(e)))
        except socket.gaierror,e:
            logging.debug('PsychoPyApp: terminateHubProcess socket.gaierror: %s'%(str(e)))
        except socket.timeout,e:
            logging.debug('PsychoPyApp: terminateHubProcess socket.timeout: %s'%(str(e)))
        except Exception, e:
            logging.debug('PsychoPyApp: terminateHubProcess exception: %s'%(str(e)))
        finally:
            if sock:
                sock.close()
            logging.debug('PsychoPyApp: terminateHubProcess completed.')
    def quit(self, event=None):
        logging.debug('PsychoPyApp: Quitting...')
        self.quitting=True
        #see whether any files need saving
        for frame in self.allFrames:
            try: #will fail if the frame has been shut somehow elsewhere
                ok = frame.checkSave()
            except:
                ok = False
                logging.debug("PsychopyApp: exception when saving")
            if not ok:
                logging.debug('PsychoPyApp: User cancelled shutdown')
                return#user cancelled quit

        #save info about current frames for next run
        if self.coder and len(self.builderFrames)==0:
            self.prefs.appData['lastFrame']='coder'
        elif self.coder is None:
            self.prefs.appData['lastFrame']='builder'
        else:
            self.prefs.appData['lastFrame']='both'

        self.prefs.appData['lastVersion']=self.version
        #update app data while closing each frame
        self.prefs.appData['builder']['prevFiles']=[]#start with an empty list to be appended by each frame
        self.prefs.appData['coder']['prevFiles']=[]

        for frame in list(self.allFrames):
            try:
                frame.closeFrame(event=event, checkSave=False)
                self.prefs.saveAppData()#must do this before destroying the frame?
            except:
                pass #we don't care if this fails - we're quitting anyway
        self.Exit()

    def showPrefs(self, event):
        from psychopy.app.preferencesDlg import PreferencesDlg
        logging.debug('PsychoPyApp: Showing prefs dlg')
        prefsDlg = PreferencesDlg(app=self)
        prefsDlg.Show()

    def showAbout(self, event):
        logging.debug('PsychoPyApp: Showing about dlg')

        license = open(os.path.join(self.prefs.paths['psychopy'],'LICENSE.txt'), 'rU').read()
        msg = _translate("""For stimulus generation and experimental control in python.

            PsychoPy depends on your feedback. If something doesn't work
            then let us know at psychopy-users@googlegroups.com""").replace('    ', '')
        info = wx.AboutDialogInfo()
        if wx.version() >= '3.':
            icon = os.path.join(self.prefs.paths['resources'], 'psychopy.png')
            info.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_PNG, 128, 128))
        info.SetName('PsychoPy')
        info.SetVersion('v'+psychopy.__version__)
        info.SetDescription(msg)

        info.SetCopyright('(C) 2002-2015 Jonathan Peirce')
        info.SetWebSite('http://www.psychopy.org')
        info.SetLicence(license)
        info.AddDeveloper('Jonathan Peirce')
        info.AddDeveloper('Jeremy Gray')
        info.AddDeveloper('Sol Simpson')
        info.AddDeveloper(u'Jonas Lindel\xF8v')
        info.AddDeveloper('Yaroslav Halchenko')
        info.AddDeveloper('Erik Kastman')
        info.AddDeveloper('Michael MacAskill')
        info.AddDeveloper('Hiroyuki Sogo')
        info.AddDocWriter('Jonathan Peirce')
        info.AddDocWriter('Jeremy Gray')
        info.AddDocWriter('Rebecca Sharman')
        info.AddTranslator('Hiroyuki Sogo')
        if not self.testMode:
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
    sys.exit("Do not launch the app from this script - use python psychopyApp.py instead")
