import wx
import configobj, validate

class PreferencesDlg(wx.Frame):
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy Preferences"):
        wx.Frame.__init__(self, parent, ID, title, size=(700,700))
        panel = wx.Panel(self)
        self.nb = wx.Notebook(panel)
        self.pageIDs={}#store the page numbers
        self.paths = app.prefs.paths
        self.app=app
        
        self.prefs={'user' : app.prefs.userPrefsCfg,
                    'site' : app.prefs.sitePrefsCfg,
                    'keys' : app.prefs.keysPrefsCfg,
                    'help' : app.prefs.helpPrefsCfg}
        self.prefPagesOrder = ['user', 'site', 'keys', 'help']
        
        for n, prefsType in enumerate(self.prefPagesOrder):
            sitePage = self.makePage(self.prefs[prefsType])
            self.nb.AddPage(sitePage,prefsType)
            self.pageIDs[prefsType]=n

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        self.menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        item = self.fileMenu.Append(wx.ID_SAVE,   "&Save prefs\t%s" %app.keys.save)
        self.Bind(wx.EVT_MENU, self.save, item)
        item = self.fileMenu.Append(wx.ID_CLOSE,   "&Close prefs\t%s" %app.keys.close)
        self.Bind(wx.EVT_MENU, self.close, item)
        self.fileMenu.AppendSeparator()
        item = self.fileMenu.Append(wx.ID_EXIT, "&Quit\t%s" %app.keys.quit, "Terminate the application")
        self.Bind(wx.EVT_MENU, self.quit, item)

        self.menuBar.Append(self.fileMenu, "&File")
        self.SetMenuBar(self.menuBar)
        
        try:
            self.nb.ChangeSelection(app.prefs.pageCurrent)
        except:
            pass # the above can throw an error if prefs already open

    def makePage(self, prefs):
        page = wx.stc.StyledTextCtrl(parent=self.nb)

        # setup the style
        if sys.platform=='darwin':
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier New,size:10d")
        else:
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier,size:12d")
        page.StyleClearAll()  # Reset all to be like the default
        page.SetLexer(wx.stc.STC_LEX_PROPERTIES)
        page.StyleSetSpec(wx.stc.STC_PROPS_SECTION,"fore:#FF5555,bold")
        page.StyleSetSpec(wx.stc.STC_PROPS_COMMENT,"fore:#007F00")

        buff=StringIO.StringIO()
        prefs.write(buff)
        if sys.platform == 'darwin' and 'keybindings' in prefs.keys():
            # display Cmd+ instead of Ctrl+, because that's how the keys will work
            page.SetText(buff.getvalue().replace('Ctrl+','Cmd+'))
        else:
            page.SetText(buff.getvalue())
        buff.close()

        # check that the folder exists
        dirname = os.path.dirname(prefs.filename)
        if not os.path.isdir(dirname):
            try: os.makedirs(dirname)
            except: 
                page.SetReadOnly(True)
        # make the text read-only?
        try:
            if prefs.filename.find("prefsHelp.cfg") > -1: raise Exception()  # read-only if a protected page, like prefsHelp.cfg
            f = open(prefs.filename, 'a')  # read-only if write-access fails; this test did not work for me: os.access(dirname,os.W_OK)
            f.close()
        except:  # make the textctrl read-only, and comment color blue
            if prefs.filename.find("prefsUser.cfg") < 0:  # user prefs should always be editable
                page.SetReadOnly(True)
                page.StyleSetSpec(wx.stc.STC_PROPS_COMMENT,"fore:#0033BB")
        return page
    
    def close(self, event=None):
        app.prefs.pageCurrent = self.nb.GetSelection()
        self.checkForUnsaved()        
        self.Destroy()
        
    def quit(self, event=None):
        self.checkForUnsaved()        
        self.close()
        self.app.quit()
        
    def checkForUnsaved(self, event=None):
        pageCurrent = self.nb.GetSelection()
        # better: copied from coder line 1232+; example of how to call: coder line 1444
        #for ii in range(self.notebook.GetPageCount()):
        #    doc = self.nb.GetPage(ii)
        #    filename=doc.filename
        #    if doc.UNSAVED:
        #        dlg = dialogs.MessageDialog(self,message='Save changes to %s before quitting?' %filename, type='Warning')
        #        resp = dlg.ShowModal()
        #        sys.stdout.flush()
        #        dlg.Destroy()
        #        if resp  == wx.ID_CANCEL: return 0 #return, don't quit
        #        elif resp == wx.ID_YES: self.save() #save then quit
        #        elif resp == wx.ID_NO: pass #don't save just quit        
 
        if app.prefs.prefsCfg['app']['autoSavePrefs']:
            for prefsType in self.prefs.keys():
                if self.isChanged(prefsType):
                   print "auto-",
                   break
            self.save()
        app.prefs.pageCurrent = pageCurrent
        
    def save(self, event=None):
        # user changes are to two separate cfg's; merge to set values to actually use now 
        prefsSpec = configobj.ConfigObj(os.path.join(self.paths['prefs'], 'prefsSite.spec'), encoding='UTF8', list_values=False)
        app.prefs.prefsCfg = configobj.ConfigObj(app.prefs.sitePrefsCfg, configspec=prefsSpec)
        app.prefs.prefsCfg.merge(app.prefs.userPrefsCfg)

        pageCurrent = self.nb.GetSelection()
        for prefsType in self.prefs.keys():
            pageText = self.getPageText(prefsType)
            filePath = self.paths['%sPrefsFile' % prefsType]
            if self.isChanged(prefsType):
                try:
                    f = open(filePath, 'w')
                    f.write(pageText)
                    f.close()
                    print "saved", filePath
                except:
                    pass
        # reload / refresh:
        self.app.prefs = preferences.Preferences()  # validation happens in here
        self.app.keys = self.app.prefs.keys
        
        self.nb.ChangeSelection(pageCurrent)
        return 1  # ok
    
    def getPageText(self,prefsType):
        """Get the prefs text for a given page
        """
        self.nb.ChangeSelection(self.pageIDs[prefsType])
        return self.nb.GetCurrentPage().GetText().encode('utf-8')
    def isChanged(self,prefsType='site'):
        filePath = self.paths['%sPrefsFile' %prefsType]
        if not os.path.isfile(filePath):
            return True
        f = open(filePath, 'r')  # 'r+' fails if the file does not have write permission
        savedTxt = f.read()
        f.close()
        #find the notebook page
        currTxt = self.getPageText(prefsType)
        return (currTxt!=savedTxt)