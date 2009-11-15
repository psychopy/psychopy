# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, urllib, platform, re
import configobj, validate
from preferencesDlg import PreferencesDlg

#GET PATHS------------------
join = os.path.join
if platform.system() == 'Windows':
    activeUser = os.environ['USERNAME']
else:
    activeUser = os.environ['USER']

class Preferences:
    def __init__(self):
        self.userPrefsCfg=None#the config object for the preferences
        self.appDataCfg=None #the config object for the app data (users don't need to see)

        self.general=None
        self.coder=None
        self.builder=None
        self.connections=None
        self.paths = {}  # this will remain a dictionary
        self.keys = {}  # does not remain a dictionary
        
        self.getPaths()
        self.loadAll()
        
        if self.userPrefsCfg['app']['resetSitePrefs']:
            self.resetSitePrefs()
            self.loadAll()
            # ideally now refresh the preferencesDlg display in the main app, if its open
        
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
        
        self.paths['prefsSpecFile']= join(prefSpecDir,platform.system()+'.spec')
        if platform.system()=='Windows':
            self.paths['userPrefsDir']= join(os.environ['APPDATA'],'psychopy2')
        else:
            self.paths['userPrefsDir']= join(os.environ['HOME'],'.psychopy2')
      
    def loadAll(self):
        """Load the user prefs and the application data
        """
        self._validator=validate.Validator()
        
        # note: self.paths['userPrefsDir'] gets set in loadSitePrefs()
        self.paths['appDataFile'] = join(self.paths['userPrefsDir'], 'appData.cfg')
        self.paths['userPrefsFile'] = join(self.paths['userPrefsDir'], 'userPrefs.cfg')
        
        self.userPrefsCfg = self.loadUserPrefs()
        self.appDataCfg = self.loadAppData()
        
        resultOfValidate = self.userPrefsCfg.validate(self._validator, copy=True)
        self.restoreBadPrefs(self.userPrefsCfg, resultOfValidate)
        
        #simplify namespace
        self.general=self.userPrefsCfg['general']
        self.app = self.userPrefsCfg['app']
        self.coder=self.userPrefsCfg['coder']
        self.builder=self.userPrefsCfg['builder']
        self.connections=self.userPrefsCfg['connections']
        self.keys=self.userPrefsCfg['keyBindings']
        self.appData = self.appDataCfg
        
        # keybindings:
        #self.keyDict = self.keysPrefsCfg['keybindings']  # == dict, with items in u'___' format
        #self.keys = self.convertKeyDict()  # no longer a dict, no longer u'___' format
        self.keys = self.userPrefsCfg['keyBindings']
        
        # connections:
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
    
    def convertKeyDict(self):
        """a function to convert a keybindings dict from (merged) cfg files to self.keys
        as expected elsewhere in the app, using a persistent file, psychopy/mySiteKeys.py
        """
        # logic: if no write permission for this user in site-packages psychopy/ directory, assume the user
        # is not an admin so try to use an exisiting mySiteKeys.py file created by an admin earlier
        # (and if that does not exist, then fall back to using keybindings.py for this user)
        # if the user does have write permission, then (re)create the mySiteKeys.py file, from
        # a merge of defaults + platform + possibly edited key prefs (as returned by loadKeysPrefs prior to calling this function)
        
        useDefaultKeys = False
        mySiteKeys = join(self.paths['prefs'], "mySiteKeys.py")
        
        try: 
            file = open(mySiteKeys, "w")  # if admin user, (re)create mySiteKeys.py file
            file.write("# key-bindings file, created by admin user on first run, used site-wide\n")
            usedKeys = []
            keyRegex = re.compile("^(F\d{1,2}|Ctrl[+-]|Alt[+-]|Shift[+-])+(.{1,1}|[Ff]\d{1,2}|Home|Tab){0,1}$", re.IGNORECASE)
            # extract legal menu items from cfg file, convert to regex syntax
            menuFile = open(join(self.paths['prefs'], "prefsKeys.cfg"), "r")
            menuList = []
            for line in menuFile:
                if line.find("=") > -1:
                    menuList.append(line.split()[0] + "|")
            if platform.system() == "Windows":  # update: seems no longer necessary
                file.write("#" + str(menuList)+"\n")  # I added this to help debug a windows-only menuRegex issue, and this solved it (!)
            menuFile.close()
            menuRegex = '^(' + "".join(menuList)[:-1] + ')$'
            for k in self.keyDict.keys():
                keyK = str(self.keyDict[k])
                k = str(k)
                if keyK in usedKeys and k.find("switchTo") < 0:  # hard-code allowed duplicates (e.g., Ctrl+L)
                    print "PsychoPy (preferences.py):  duplicate key %s" % keyK
                    useDefaultKeys = True
                else:
                    usedKeys.append(keyK)
                if not re.match(menuRegex, k):
                    print "PsychoPy (preferences.py):  unrecognized menu-item '%s'" % k 
                    useDefaultKeys = True
                # standardize user input
                keyK = re.sub(r"(?i)Ctrl[+-]", 'Ctrl+', keyK)  
                keyK = re.sub(r"(?i)Cmd[+-]", 'Ctrl+', keyK)
                keyK = re.sub(r"(?i)Shift[+-]", 'Shift+', keyK)
                keyK = re.sub(r"(?i)Alt[+-]", 'Alt+', keyK)
                keyK = "".join([j.capitalize() + "+" for j in keyK.split("+")])[:-1] 
                # validate user input, not a perfect filter but should be pretty good
                if keyRegex.match(keyK):
                    if self.keyDict[k].find("'") > -1: quoteDelim = '"'
                    else: quoteDelim = "'"
                    file.write("%s" % str(k) + " = " + quoteDelim + keyK + quoteDelim + "\n")
                else:
                    print "PsychoPy (preferences.py):  bad key %s (menu-item %s)" % keyK, k
            file.close()
        except:
            pass

        try:
            if useDefaultKeys: raise Exception()
            from psychopy.prefs import mySiteKeys
            self.keys = mySiteKeys
        except:
            from psychopy.app import keybindings
            self.keys = keybindings
        
        return self.keys
        
    def saveAppData(self):
        """Save the various setting to the appropriate files (or discard, in some cases)
        """
        self.appDataCfg.validate(self._validator, copy=True)#copy means all settings get saved
        if not os.path.isdir(self.paths['userPrefsDir']):
            os.makedirs(self.paths['userPrefsDir'])
        self.appDataCfg.write()
        
    def resetUserPrefs(self):
        """Reset the site preferences to the original defaults
        """
        # confirmation probably not necessary: you have to manually type 'True' and then save
        if os.path.isfile(self.paths['sitePrefsFile']): os.remove(self.paths['sitePrefsFile'])
        if os.path.isfile(self.paths['keysPrefsFile']): os.remove(self.paths['keysPrefsFile'])
        mySiteKeys = join(self.paths['prefs'], 'mySiteKeys.py')
        if os.path.isfile(mySiteKeys):        os.remove(mySiteKeys)
        if os.path.isfile(mySiteKeys + "c"):  os.remove(mySiteKeys + "c")
        print "Site prefs and key-bindings RESET to defaults"
        
    def loadAppData(self):
        #fetch appData too against a config spec
        appDataSpec = configobj.ConfigObj(join(self.paths['appDir'], 'appData.spec'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['appDataFile'], configspec=appDataSpec)
        resultOfValidate = cfg.validate(self._validator, copy=True, preserve_errors=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        return cfg

    def restoreBadPrefs(self, cfg, resultOfValidate):
        if resultOfValidate == True:
            return
        vtor = validate.Validator()
        for (section_list, key, _) in configobj.flatten_errors(cfg, resultOfValidate):
            if key is not None:
                cfg[', '.join(section_list)][key] = vtor.get_default_value(cfg.configspec[', '.join(section_list)][key])
            else:
                print "Section [%s] was missing in file '%s'" % (', '.join(section_list), cfg.filename)
        
    def loadUserPrefs(self):
        """load user prefs, if any; don't save to a file because doing so will
        break easy_install. Saving to files within the psychopy/ is fine, eg for
        key-bindings, but outside it (where user prefs will live) is not allowed
        by easy_install (security risk)
        """
        prefsSpec = configobj.ConfigObj(self.paths['prefsSpecFile'], encoding='UTF8', list_values=False)
        
        #check/create path for user prefs
        if not os.path.isdir(self.paths['userPrefsDir']):
            try: os.makedirs(self.paths['userPrefsDir'])
            except:
                print "Preferences.py failed to create folder %s. Settings will be read-only" % self.paths['userPrefsDir']
        #then get the configuration file
        cfg = configobj.ConfigObj(self.paths['userPrefsFile'], configspec=prefsSpec)
        #cfg.validate(self._validator, copy=False)  # merge first then validate
        cfg.initial_comment = ["###", "###     USER PREFERENCES for '" + activeUser + "' (override SITE prefs; see 'help')",
                                      "###    ---------------------------------------------------------------------", ""]
        cfg.final_comment = ["", "", "### [this page is stored at %s]" % self.paths['userPrefsFile']]
        # don't cfg.write(), see explanation above
        return cfg
    
    def getAutoProxy(self):
        """Fetch the proxy from the the system environment variables
        """
        if urllib.getproxies().has_key('http'):
            return urllib.getproxies()['http']
        else:
            return ""

