import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.flatnotebook as fnb
import platform, re
import locale

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

        self.nb = fnb.FlatNotebook(self, style=fnb.FNB_NO_X_BUTTON|fnb.FNB_NO_NAV_BUTTONS)
        #self.nb = wx.Notebook(self)#notebook isn't nice with lots of pages

        self.ctrls={}
        for sectionName in self.prefsCfg.keys():
            prefsPage = self.makePrefsPage(parent=self.nb,
                    sectionName=sectionName,
                    prefsSection=self.prefsCfg[sectionName],
                    specSection = self.prefsSpec[sectionName])
            self.nb.AddPage(prefsPage, sectionName)
        self.nb.SetSelection(self.app.prefs.pageCurrent)
        sizer.Add(self.nb,1, wx.EXPAND)

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
        sizer.Add(btnsizer, 0, wx.BOTTOM|wx.ALL, 5)

        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
    def onHelp(self, event=None):
        """Uses self.app.followLink() and app/urls.py to go to correct url
        """
        currentPane = self.nb.GetPageText(self.nb.GetSelection())
        urlName = "prefs.%s" %currentPane#what the url should be called in psychopy.app.urls
        if urlName in self.app.urls.keys():
            url = self.app.urls[urlName]
        else: url=self.app.urls["prefs"]#couldn't find that section - use default prefs
        self.app.followLink(url=url)
    def onApply(self, event=None):
        self.setPrefsFromCtrls()
        self.app.prefs.pageCurrent = self.nb.GetSelection()
        locale.setlocale(locale.LC_ALL, str(self.app.prefs.app['locale']))
    def onCancel(self, event=None):
        self.Close()
    def onOK(self, event=None):
        self.onApply(event=event)
        self.Close()
    def makePrefsPage(self, parent, sectionName, prefsSection, specSection):
        panel = scrolled.ScrolledPanel(parent,-1,size=(dlgSize[0]-100,dlgSize[1]-200))
        vertBox = wx.BoxSizer(wx.VERTICAL)
        #add each pref for this section
        for prefName in specSection.keys():
            if prefName in ['version']:#any other prefs not to show?
                continue
            #if platform.system() != 'Windows' and prefName == 'allowModuleImports':
            #    continue # allowModuleImports is handled by generateSpec.py
            #NB if something is in prefs but not in spec then it won't be shown (removes outdated prefs)
            thisPref = prefsSection[prefName]
            thisSpec = specSection[prefName]
            ctrlName = sectionName+'.'+prefName
            if platform.system() == 'Darwin' and sectionName == 'keyBindings' and \
                    thisSpec.startswith('string'):
                thisPref = thisPref.replace('Ctrl+', 'Cmd+')
            self.ctrls[ctrlName] = ctrls = PrefCtrls(parent=panel, name=prefName, value=thisPref, spec=thisSpec)
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            ctrlSizer.Add(ctrls.nameCtrl, 0, wx.ALL, 5)
            ctrlSizer.Add(ctrls.valueCtrl, 0, wx.ALL, 5)

            # get tooltips from comment lines from the spec, as parsed by configobj
            hints = self.prefsSpec[sectionName].comments[prefName] # a list
            if len(hints):
                # use only one comment line, from right above the pref
                hint = hints[-1].lstrip().lstrip('#').lstrip()
            else:
                hint = ''
            ctrls.valueCtrl.SetToolTipString(hint)

            vertBox.Add(ctrlSizer)
        #size the panel and setup scrolling
        panel.SetSizer(vertBox)
        panel.SetAutoLayout(True)
        panel.SetupScrolling()
        return panel
    def setPrefsFromCtrls(self):
        # case-insensitive match for Cmd+ at start of string:
        re_cmd2ctrl = re.compile('^Cmd\+', re.I)
        for sectionName in self.prefsCfg.keys():
            for prefName in self.prefsSpec[sectionName].keys():
                if prefName in ['version']:#any other prefs not to show?
                    continue
                ctrlName = sectionName+'.'+prefName
                ctrl = self.ctrls[ctrlName]
                thisPref = ctrl.getValue()
                # remove invisible trailing whitespace:
                if type(thisPref) in [str, unicode]:
                    thisPref = thisPref.strip()
                # regularize the display format for keybindings
                if sectionName == 'keyBindings':
                    thisPref = thisPref.replace(' ','')
                    thisPref = '+'.join([part.capitalize() for part in thisPref.split('+')])
                    if platform.system() == 'Darwin':
                        # key-bindings were displayed as 'Cmd+O', revert to 'Ctrl+O' internally
                        thisPref = re_cmd2ctrl.sub('Ctrl+', thisPref)
                self.prefsCfg[sectionName][prefName]=thisPref
                #make sure list values are converted back to being lists (from strings)
                if self.prefsSpec[sectionName][prefName].startswith('list'):
                    newVal = eval(thisPref)
                    if type(newVal)!=list:
                        self.prefsCfg[sectionName][prefName]=[newVal]
                    else:
                        self.prefsCfg[sectionName][prefName]=newVal
        self.app.prefs.saveUserPrefs()#includes a validation
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
        if type(value)==bool:
            #only True or False - use a checkbox
            self.valueCtrl = wx.CheckBox(self.parent)
            self.valueCtrl.SetValue(value)
        elif spec.startswith('option'):
            options = spec.replace("option(", "").replace("'","").replace(", ",",")
            options = options.split(',')[:-1]
            self.valueCtrl = wx.Choice(self.parent, choices=options)
            self.valueCtrl.SetStringSelection(unicode(value))
        else:#just use a string
            self.valueCtrl = wx.TextCtrl(self.parent,-1,str(value),
                            size=(valueWidth,-1))

    def _getCtrlValue(self, ctrl):
        """Retrieve the current value from the control (whatever type of ctrl it
        is, e.g. checkbox.GetValue, textctrl.GetStringSelection
        """
        """Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl==None: return None
        elif hasattr(ctrl, 'GetStringSelection') and len(ctrl.GetStringSelection())>0: #for wx.Choice
            return ctrl.GetStringSelection()
        elif hasattr(ctrl, 'GetValue'): #e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetLabel'): #for wx.StaticText
            return ctrl.GetLabel()
        else:
            print "failed to retrieve the value for: %s" %(ctrl.valueCtrl)
            return None
    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)

if __name__=='__main__':
    import preferences
    app = wx.PySimpleApp()
    app.prefs=preferences.Preferences()#don't do this normally - use the existing psychopy.prefs instance
    dlg = PreferencesDlg(app)
    dlg.ShowModal()
