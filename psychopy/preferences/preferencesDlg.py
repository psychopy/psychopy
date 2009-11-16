import wx
import wx.lib.scrolledpanel as scrolled
from wx.lib.agw import flatnotebook

import configobj, validate
dlgSize = (500,600)#this will be overridden by the size of the scrolled panel making the prefs

class PreferencesDlg(wx.Dialog):
    def __init__(self,app,
            pos=wx.DefaultPosition, size=dlgSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self,None,-1,"PsychoPy Preferences",pos,size,style)
        self.app=app
        self.Center()
        self.prefsCfg = self.app.prefs.userPrefsCfg
        self.prefsSpec = self.app.prefs.prefsSpec
        sizer = wx.BoxSizer(wx.VERTICAL)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        #notebook, flatnotebook or something else?
        
        self.nb = flatnotebook.FlatNotebook(self)#flatNoteBook has the option to close pages (which we don't want)
#        self.nb = wx.Notebook(self)#notebook isn't nice with lots of pages
        
        self.ctrls={}
        for sectionName in self.prefsCfg.keys():
            prefsPage = self.makePrefsPage(parent=self.nb, 
                    sectionName=sectionName,
                    prefsSection=self.prefsCfg[sectionName],
                    specSection = self.prefsSpec[sectionName])
            self.nb.AddPage(prefsPage, sectionName)
        sizer.Add(self.nb)
        
        #create buttons
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        btnsizer = wx.StdDialogButtonSizer()     
        #ok
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("Save prefs (in all sections) and close window")
        btn.Bind(wx.EVT_BUTTON, self.onOK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        #cancel
        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel any changes (to any panel)")
        btn.Bind(wx.EVT_BUTTON, self.onCancel)
        btnsizer.AddButton(btn)
        #apply
        btn = wx.Button(self, wx.ID_APPLY)
        btn.SetHelpText("Apply these prefs (in all sections) and continue")
        btn.Bind(wx.EVT_BUTTON, self.onApply)
        btnsizer.AddButton(btn)    
        #help
        btn = wx.Button(self, wx.ID_HELP)
        btn.SetHelpText("Get help on prefs")
        btn.Bind(wx.EVT_BUTTON, self.onHelp)
        btnsizer.AddButton(btn)
        btnsizer.Realize()    
        #add buttons to dlg
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizerAndFit(sizer)
        sizer.Fit(self)
    def onHelp(self, event=None):
        #this should be handled from app.followLink instead
        wx.LaunchDefaultBrowser("http://www.psychopy.org/general/prefs.html")
    def onApply(self, event=None):
        self.setPrefsFromCtrls()
    def onCancel(self, event=None):
        self.Close()
    def onOK(self, event=None):
        self.setPrefsFromCtrls()
        self.close()
    def makePrefsPage(self, parent, sectionName, prefsSection, specSection):
        panel = scrolled.ScrolledPanel(parent,-1,size=(dlgSize[0]-100,dlgSize[1]-200))
        vertBox = wx.BoxSizer(wx.VERTICAL)
        #add each pref for this section
        for prefName in specSection.keys():
            #NB if something is in prefs but not in spec then it won't be shown (removes outdated prefs)
            thisPref = prefsSection[prefName]
            thisSpec = specSection[prefName]
            ctrlName = sectionName+'.'+prefName
            self.ctrls[ctrlName] = ctrls = PrefCtrls(parent=panel, name=prefName, value=thisPref, spec=thisSpec)            
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            ctrlSizer.Add(ctrls.nameCtrl, 0, wx.ALL, 5)
            ctrlSizer.Add(ctrls.valueCtrl, 0, wx.ALL, 5)
            vertBox.Add(ctrlSizer)
        #size the panel and setup scrolling
        panel.SetSizer(vertBox)
        panel.SetAutoLayout(1)
        panel.SetupScrolling()
        return panel
    def setPrefsFromCtrls(self):
        for sectionName in self.prefsCfg.keys():
            for prefName in self.prefsSpec[sectionName].keys():
                ctrlName = sectionName+'.'+prefName
                ctrl = self.ctrls[ctrlName]
                self.prefsCfg[sectionName][prefName]=ctrl.getValue()
        self.prefs.saveUserPrefs()#includes a validation
        #maybe then go back and set GUI from prefs again, because validation may have changed vals?
        
class PrefCtrls:
    def __init__(self, parent, name, value, spec):
        """Create a set of ctrls for a particular preference entry
        """
        self.pref=value
        self.parent = parent
        valueWidth = 200
        labelWidth = 200
        self.nameCtrl = self.valueCtrl = None
        
        self.nameCtrl = wx.StaticText(self.parent,-1,name,size=(labelWidth,-1),
                                        style=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.valueCtrl = wx.TextCtrl(self.parent,-1,str(value),
                        size=(valueWidth,-1))
        #use the spec to work out which type of control to present (checkbox for bool, choice for list, textCtrl for string)
#        if =='bool':
#            #only True or False - use a checkbox
#             self.valueCtrl = wx.CheckBox(self.dlg, size = wx.Size(self.valueWidth,-1))
#             self.valueCtrl.SetValue(pref.val)
#        elif ...:
#            #there are limitted options - use a Choice control
#            self.valueCtrl = wx.Choice(self.dlg, choices=param.allowedVals, size=wx.Size(self.valueWidth,-1))
#            self.valueCtrl.SetStringSelection(unicode(param.val))
#        else:
#            #create the full set of ctrls
#            self.valueCtrl = wx.TextCtrl(self.dlg,-1,str(param.val),
#                        size=wx.Size(self.valueWidth,-1))

    def _getCtrlValue(self, ctrl):
        """Retrieve the current value from the control (whatever type of ctrl it
        is, e.g. checkbox.GetValue, textctrl.GetStringSelection
        """
        """Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl==None: return None
        elif hasattr(ctrl, 'GetValue'): #e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetStringSelection'): #for wx.Choice
            return ctrl.GetStringSelection()
        elif hasattr(ctrl, 'GetLabel'): #for wx.StaticText
            return ctrl.GetLabel()
        else:
            print "failed to retrieve the value for: %s" %(ctrl.valueCtrl)
            return None
    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)
        
class PreferencesDlgText(wx.Frame):
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
    
if __name__=='__main__':
    import preferences
    app = wx.PySimpleApp()
    app.prefs=preferences.Preferences()
    dlg = PreferencesDlg(app)
    dlg.ShowModal()