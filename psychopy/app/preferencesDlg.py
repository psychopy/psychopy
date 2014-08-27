from psychopy import logging
import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.flatnotebook as fnb
import platform, re
import copy
import localization

dlgSize = (520,600)#this will be overridden by the size of the scrolled panel making the prefs

# labels mappings for display:
_localized = {
        # section labels:
            'general': _('General'), 'app': _('App'),
            'builder': "Builder", 'coder': "Coder",  # not localized
            'connections': _('Connections'), 'keyBindings': _('Key bindings'),
        # pref labels:
            'winType': _("window type"), 'units': _("units"),
            'fullscr': _("full-screen"), 'allowGUI': _("allow GUI"), 'paths': _('paths'),
            'audioLib': _("audio library"), 'audioDriver': _("audio driver"),
            'flac': _('flac audio compression'),
            'parallelPorts': _("parallel ports"), 'showStartupTips': _("show start-up tips"),
            'largeIcons': _("large icons"), 'defaultView': _("default view"),
            'resetPrefs': _('reset preferences'), 'autoSavePrefs': _('auto-save prefs'),
            'debugMode': _('debug mode'), 'locale': _('locale'),
            'codeFont': _('code font'), 'commentFont': _('comment font'),
            'outputFont': _('output font'), 'outputFontSize': _('output font size'),
            'codeFontSize': _('code font size'),
            'showSourceAsst': _('show source asst'), 'showOutput': _('show output'),
            'reloadPrevFiles': _('reload previous files'),
            'preferredShell': _('preferred shell'), 'newlineConvention': _('newline convention'),
            'reloadPrevExp': _('reload previous exp'), 'unclutteredNamespace': _('uncluttered namespace'),
            'componentsFolders': _('components folders'), 'hiddenComponents': _('hidden components'),
            'unpackedDemosDir': _('unpacked demos dir'), 'savedDataFolder': _('saved data folder'),
            'topFlow': _('Flow at top'), 'alwaysShowReadme': _('always show readme'),
            'maxFavorites': _('max favorites'), 'proxy': _('proxy'),
            'autoProxy': _('auto-proxy'), 'allowUsageStats': _('allow usage stats'),
            'checkForUpdates': _('check for updates'), 'timeout': _('timeout'),
            'open': _('open'), 'new': _('new'), 'save': _('save'),
            'saveAs': _('save as'), 'print': _('print'), 'close': _('close'), 'quit': _('quit'),
            'preferences': _('preferences'), 'cut': _('cut'), 'copy': _('copy'),
            'paste': _('paste'), 'duplicate': _('duplicate'), 'indent': _('indent'),
            'dedent': _('dedent'), 'smartIndent': _('smart indent'),
            'find': _('find'), 'findAgain': _('find again'), 'undo': _('undo'), 'redo': _('redo'),
            'comment': _('comment'), 'uncomment': _('uncomment'), 'fold': _('fold'),
            'analyseCode': _('analyze code'), 'compileScript': _('compile script'), 'runScript': _('run script'),
            'stopScript': _('stop script'), 'toggleWhitespace': _('toggle whitespace'),
            'toggleEOLs': _('toggle EOLs'), 'toggleIndentGuides': _('toggle indent guides'),
            'newRoutine': _('new Routine'), 'copyRoutine': _('copy Routine'),
            'pasteRoutine': _('paste Routine'), 'toggleOutputPanel': _('toggle output panel'),
            'switchToBuilder': _('switch to Builder'), 'switchToCoder': _('switch to Coder'),
            'largerFlow': _('larger Flow'), 'smallerFlow': _('smaller Flow'),
            'largerRoutine': _('larger routine'), 'smallerRoutine': _('smaller routine'),
            'toggleReadme': _('toggle readme'),
        # pref wxChoice lists:
            'last': _('same as last session'), 'both': _('both Builder & Coder'),
            'keep': _('same as in the file'),  # line endings
            # not translated:
            'pix': 'pix', 'deg': 'deg', 'cm': 'cm', 'norm': 'norm', 'height': 'height',
            'pyshell': 'pyshell', 'iPython': 'iPython'
        }
# add pre-translated names-of-langauges, for display in locale pref:
_localized.update(localization.locname)

class PreferencesDlg(wx.Dialog):
    def __init__(self,app,
            pos=wx.DefaultPosition, size=dlgSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self,None,-1,_("PsychoPy Preferences"),pos,size,style)
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
        sectionOrdering = ['app', 'builder', 'coder', 'general', 'connections', 'keyBindings']
        for sectionName in sectionOrdering:
            prefsPage = self.makePrefsPage(parent=self.nb,
                    sectionName=sectionName,
                    prefsSection=self.prefsCfg[sectionName],
                    specSection = self.prefsSpec[sectionName])
            self.nb.AddPage(prefsPage, _localized[sectionName])
        self.nb.SetSelection(self.app.prefs.pageCurrent)
        sizer.Add(self.nb,1, wx.EXPAND)

        aTable = wx.AcceleratorTable([
                                      (wx.ACCEL_NORMAL, wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_OK),
                                      ])
        self.SetAcceleratorTable(aTable)

        #create buttons
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        btnsizer = wx.StdDialogButtonSizer()
        #ok
        btn = wx.Button(self, wx.ID_OK, _('OK'))
        btn.SetHelpText(_("Save prefs (in all sections) and close window"))
        btn.Bind(wx.EVT_BUTTON, self.onOK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        #cancel
        btn = wx.Button(self, wx.ID_CANCEL, _('Cancel'))
        btn.SetHelpText(_("Cancel any changes (to any panel)"))
        btn.Bind(wx.EVT_BUTTON, self.onCancel)
        btnsizer.AddButton(btn)
        #apply
        btn = wx.Button(self, wx.ID_APPLY, _('Apply'))
        btn.SetHelpText(_("Apply these prefs (in all sections) and continue"))
        btn.Bind(wx.EVT_BUTTON, self.onApply)
        btnsizer.AddButton(btn)
        #help
        btn = wx.Button(self, wx.ID_HELP, _('Help'))
        btn.SetHelpText(_("Get help on prefs"))
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
        # don't set locale here; need to restart app anyway
    def onEvt(self, evt, id=None):
        print evt
    def onCancel(self, event=None):
        self.Destroy()
    def onOK(self, event=None):
        self.onApply(event=event)
        self.Destroy()
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
            try:
                pLabel = _localized[prefName]
            except:
                pLabel = prefName
            if prefName == 'locale':
                # fake spec -> option: use available locale info not spec file
                thisSpec = 'option(' + ','.join([''] + self.app.localization.available)+ ', default=xxx)'
                thisPref = self.app.prefs.app['locale']
            self.ctrls[ctrlName] = ctrls = PrefCtrls(parent=panel, name=pLabel, value=thisPref, spec=thisSpec)
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            ctrlSizer.Add(ctrls.nameCtrl, 0, wx.ALL, 5)
            ctrlSizer.Add(ctrls.valueCtrl, 0, wx.ALL, 5)

            # get tooltips from comment lines from the spec, as parsed by configobj
            hints = self.prefsSpec[sectionName].comments[prefName] # a list
            if len(hints):
                # use only one comment line, from right above the pref
                hint = hints[-1].lstrip().lstrip('#').lstrip()
                ctrls.valueCtrl.SetToolTipString(_(hint))
            else:
                ctrls.valueCtrl.SetToolTipString('')

            vertBox.Add(ctrlSizer)
        #size the panel and setup scrolling
        panel.SetSizer(vertBox)
        panel.SetAutoLayout(True)
        panel.SetupScrolling()
        return panel
    def setPrefsFromCtrls(self):
        # extract values, adjust as needed:
        # a) strip() to remove whitespace
        # b) case-insensitive match for Cmd+ at start of string
        # c) reverse-map locale display names to canonical names (ja_JP)
        re_cmd2ctrl = re.compile('^Cmd\+', re.I)
        for sectionName in self.prefsCfg.keys():
            for prefName in self.prefsSpec[sectionName].keys():
                if prefName in ['version']:#any other prefs not to show?
                    continue
                ctrlName = sectionName+'.'+prefName
                ctrl = self.ctrls[ctrlName]
                thisPref = ctrl.getValue()
                # remove invisible trailing whitespace:
                if hasattr(thisPref, 'strip'):
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
            options = options.split(',')[:-1]  # item -1 is 'default=x' from spec
            labels = []  # display only
            for opt in options:
                try:
                    labels.append(_localized[opt])
                except:
                    labels.append(opt)
            self.valueCtrl = wx.Choice(self.parent, choices=labels)
            self.valueCtrl._choices = copy.copy(options)  # internal values
            self.valueCtrl.SetSelection(options.index(value))
        else:#just use a string
            self.valueCtrl = wx.TextCtrl(self.parent,-1,str(value),
                            size=(valueWidth,-1))

    def _getCtrlValue(self, ctrl):
        """Retrieve the current value from the control (whatever type of ctrl it
        is, e.g. checkbox.GetValue, textctrl.GetStringSelection
        Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl==None:
            return None
        elif hasattr(ctrl, '_choices'): #for wx.Choice
            return ctrl._choices[ctrl.GetSelection()]
        elif hasattr(ctrl, 'GetValue'): #e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetLabel'): #for wx.StaticText
            return ctrl.GetLabel()
        else:
            logging.warning("failed to retrieve the value for pref: %s" %(ctrl.valueCtrl))
            return None
    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)

if __name__=='__main__':
    import preferences
    if wx.version() < '2.9':
        app = wx.PySimpleApp()
    else:
        app = wx.App(False)
    app.prefs=preferences.Preferences()#don't do this normally - use the existing psychopy.prefs instance
    dlg = PreferencesDlg(app)
    dlg.ShowModal()
