
import os, sys, urllib, platform, re, logging
import configobj, validate
import locale

join = os.path.join

class Preferences:
    """Users can alter preferences from the dialog box in the application,
    by editing their user preferences file (which is what the dialog box does)
    or, within a script, preferences can be controlled like this::

        import psychopy
        psychopy.prefs.general['audioLib'] = ['pyo','pygame']
        print(prefs) #prints the location of the user prefs file and all the current values

    Use the instance of `prefs`, as above, rather than the `Preferences` class
    directly if you want to affect the script that's running.
    """
    def __init__(self):
        self.userPrefsCfg=None#the config object for the preferences
        self.prefsSpec=None#specifications for the above
        self.appDataCfg=None #the config object for the app data (users don't need to see)

        self.general=None
        self.coder=None
        self.builder=None
        self.connections=None
        self.paths = {}  # this will remain a dictionary
        self.keys = {}  # does not remain a dictionary

        self.getPaths()
        self.loadAll()
        # set locale using pref if present, default if not present ''
        if str(self.app['locale']):
            locPref = str(self.app['locale'])
            try:
                lc = locale.setlocale(locale.LC_ALL, locPref)
                logging.info('locale set to preference: ' + lc)
            except locale.Error, e:
                logging.warning('locale pref: '+ str(e) + " '" +
                                locPref + "'; using system default")
                locale.setlocale(locale.LC_ALL, '')
        else: # handles unset == ''  --> use system default explicitly
            locale.setlocale(locale.LC_ALL, '')
            if locale.getlocale()==(None,None):
                logging.info('no locale set')
            else:
                logging.info('locale set to system default: ' + '.'.join(locale.getlocale()))

        if self.userPrefsCfg['app']['resetPrefs']:
            self.resetPrefs()
    def __str__(self):
        """pretty print the current preferences"""
        strOut = "psychopy.prefs <%s>:\n" %(join(self.paths['userPrefsDir'], 'userPrefs.cfg'))
        for sectionName in ['general','coder','builder','connections']:
            section = getattr(self,sectionName)
            for key, val in section.items():
                strOut += "  prefs.%s['%s'] = %s\n" %(sectionName, key, repr(val))
        return strOut
    def resetPrefs(self):
        """removes userPrefs.cfg, does not touch appData.cfg
        """
        userCfg = join(self.paths['userPrefsDir'], 'userPrefs.cfg')
        try:
            os.unlink(userCfg)
        except:
            print "Could not remove prefs file '%s'; (try doing it manually?)" % userCfg
        self.loadAll() # reloads, now getting all from .spec

    def getPaths(self):
        #on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath= os.path.abspath(__file__)
        prefSpecDir = os.path.split(thisFileAbsPath)[0]
        dirPsychoPy = os.path.split(prefSpecDir)[0]

        #path to Resources (icons etc)
        dirApp = join(dirPsychoPy, 'app')
        if os.path.isdir(join(dirApp, 'Resources')):
            dirResources = join(dirApp, 'Resources')
        else:dirResources = dirApp

        self.paths['psychopy']=dirPsychoPy
        self.paths['appDir']=dirApp
        self.paths['appFile']=join(dirApp, 'PsychoPy.py')
        self.paths['demos'] = join(dirPsychoPy, 'demos')
        self.paths['resources']=dirResources
        self.paths['tests'] = join(dirPsychoPy, 'tests')

        if sys.platform=='win32':
            self.paths['prefsSpecFile']= join(prefSpecDir,'Windows.spec')
            self.paths['userPrefsDir']= join(os.environ['APPDATA'],'psychopy2')
        else:#platform.system gives nicer names, but no good on standalone vista/win7
            self.paths['prefsSpecFile']= join(prefSpecDir,platform.system()+'.spec')
            self.paths['userPrefsDir']= join(os.environ['HOME'],'.psychopy2')

    def loadAll(self):
        """Load the user prefs and the application data
        """
        self._validator=validate.Validator()

        # note: self.paths['userPrefsDir'] gets set in loadSitePrefs()
        self.paths['appDataFile'] = join(self.paths['userPrefsDir'], 'appData.cfg')
        self.paths['userPrefsFile'] = join(self.paths['userPrefsDir'], 'userPrefs.cfg')

        # If PsychoPy is tucked away by Py2exe in library.zip, the preferences file
        # cannot be found. This hack is an attempt to fix this.
        if "\\library.zip\\psychopy\\preferences\\" in self.paths["prefsSpecFile"]:
            self.paths["prefsSpecFile"] = self.paths["prefsSpecFile"].replace("\\library.zip\\psychopy\\preferences\\", "\\resources\\")

        self.userPrefsCfg = self.loadUserPrefs()
        self.appDataCfg = self.loadAppData()
        self.validate()

        #simplify namespace
        self.general=self.userPrefsCfg['general']
        self.app = self.userPrefsCfg['app']
        self.coder=self.userPrefsCfg['coder']
        self.builder=self.userPrefsCfg['builder']
        self.connections=self.userPrefsCfg['connections']
        self.keys=self.userPrefsCfg['keyBindings']
        self.appData = self.appDataCfg

        # keybindings:
        self.keys = self.userPrefsCfg['keyBindings']

    def loadUserPrefs(self):
        """load user prefs, if any; don't save to a file because doing so will
        break easy_install. Saving to files within the psychopy/ is fine, eg for
        key-bindings, but outside it (where user prefs will live) is not allowed
        by easy_install (security risk)
        """
        self.prefsSpec = configobj.ConfigObj(self.paths['prefsSpecFile'], encoding='UTF8', list_values=False)

        #check/create path for user prefs
        if not os.path.isdir(self.paths['userPrefsDir']):
            try: os.makedirs(self.paths['userPrefsDir'])
            except:
                print "Preferences.py failed to create folder %s. Settings will be read-only" % self.paths['userPrefsDir']
        #then get the configuration file
        cfg = configobj.ConfigObj(self.paths['userPrefsFile'], encoding='UTF8', configspec=self.prefsSpec)
        #cfg.validate(self._validator, copy=False)  # merge first then validate
        # don't cfg.write(), see explanation above
        return cfg
    def saveUserPrefs(self):
        """Validate and save the various setting to the appropriate files (or discard, in some cases)
        """
        self.validate()
        if not os.path.isdir(self.paths['userPrefsDir']):
            os.makedirs(self.paths['userPrefsDir'])
        self.userPrefsCfg.write()

    def loadAppData(self):
        #fetch appData too against a config spec
        appDataSpec = configobj.ConfigObj(join(self.paths['appDir'], 'appData.spec'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['appDataFile'], encoding='UTF8', configspec=appDataSpec)
        resultOfValidate = cfg.validate(self._validator, copy=True, preserve_errors=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        #force favComponent level values to be integers
        if 'favComponents' in cfg['builder'].keys():
            for key in cfg['builder']['favComponents']:
                cfg['builder']['favComponents'][key] = int(cfg['builder']['favComponents'][key])
        return cfg
    def saveAppData(self):
        """Save the various setting to the appropriate files (or discard, in some cases)
        """
        self.appDataCfg.validate(self._validator, copy=True)#copy means all settings get saved
        if not os.path.isdir(self.paths['userPrefsDir']):
            os.makedirs(self.paths['userPrefsDir'])
        self.appDataCfg.write()

    def validate(self):
        """Validate (user) preferences and reset invalid settings to defaults"""
        resultOfValidate = self.userPrefsCfg.validate(self._validator, copy=True)
        self.restoreBadPrefs(self.userPrefsCfg, resultOfValidate)
    def restoreBadPrefs(self, cfg, resultOfValidate):
        if resultOfValidate == True:
            return
        vtor = validate.Validator()
        for (section_list, key, _) in configobj.flatten_errors(cfg, resultOfValidate):
            if key is not None:
                cfg[', '.join(section_list)][key] = vtor.get_default_value(cfg.configspec[', '.join(section_list)][key])
            else:
                print "Section [%s] was missing in file '%s'" % (', '.join(section_list), cfg.filename)

prefs=Preferences()
