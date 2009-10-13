# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, urllib, platform, re
import configobj, configobjValidate

#GET PATHS------------------
join = os.path.join
if platform.system() == 'Windows':
    activeUser = os.environ['USERNAME']
else:
    activeUser = os.popen('id -un', 'r').read()[:-1]  # whoami

class Preferences:
    def __init__(self):
        self.prefsCfg=None#the config object for the preferences
        self.appDataCfg=None #the config object for the app data (users don't need to see)

        self.general=None
        self.coder=None
        self.builder=None
        self.connections=None
        self.paths = {}  # this will remain a dictionary
        self.keys = {}  # does not remain a dictionary
        
        self.getPaths()
        self.loadAll()
        
        if self.prefsCfg['app']['resetSitePrefs']:
            self.resetSitePrefs()
            self.loadAll()
            # ideally now refresh the preferencesDlg display in the main app, if its open
        
    def getPaths(self):
        #on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath= os.path.abspath(__file__)
        dirPsychoPy = os.path.split(thisFileAbsPath)[0]

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
        self.paths['prefs'] = join(dirPsychoPy, 'prefs')
        
        self.paths['sitePrefsFile'] = join(self.paths['prefs'], 'mySitePrefs.cfg')
        self.paths['keysPrefsFile'] = join(self.paths['prefs'], 'mySiteKeys.cfg')
        self.paths['helpPrefsFile'] = join(self.paths['prefs'], 'prefsHelp.cfg')
        # note self.paths['userPrefsFile'] gets defined later, after userPrefsTemplate
        
    def loadAll(self):
        """A function to allow a class with attributes to be loaded from a
        pickle file necessarily without having the same attribs (so additional
        attribs can be added in future).
        """
        self._validator=configobjValidate.Validator()
        self.platformPrefsCfg = self.loadPlatformPrefs()
        self.helpPrefsCfg = self.loadHelpPrefs()
        self.sitePrefsCfg = self.loadSitePrefs()
        
        # now set user path(s), which can depend on the site prefs
        self.paths['userPrefsTemplate'] = self.sitePrefsCfg['general']['userPrefsTemplate']
        # note: self.paths['userPrefsDir'] gets set in loadSitePrefs()
        self.paths['appDataFile'] = join(self.paths['userPrefsDir'], 'appData.cfg')
        self.paths['userPrefsFile'] = join(self.paths['userPrefsDir'], 'userPrefs.cfg')
        
        self.userPrefsCfg = self.loadUserPrefs()
        self.appDataCfg = self.loadAppData()
        
        # merge general, platform, and user prefs; order matters
        self.sitePrefsCfg.merge(self.platformPrefsCfg)
        prefsSpec = configobj.ConfigObj(join(self.paths['prefs'], 'prefsSite.spec'), encoding='UTF8', list_values=False)
        self.prefsCfg = configobj.ConfigObj(self.sitePrefsCfg, configspec=prefsSpec)
        
        self.prefsCfg.merge(self.userPrefsCfg)
        resultOfValidate = self.prefsCfg.validate(self._validator, copy=False)  # validate after the merge
        self.restoreBadPrefs(self.prefsCfg, resultOfValidate)
        resultOfValidate = self.userPrefsCfg.validate(self._validator, copy=False)
        self.restoreBadPrefs(self.userPrefsCfg, resultOfValidate)
        # a 'keybindings' section can appear after merge with platform prefs:
        if 'keybindings' in self.prefsCfg: del self.prefsCfg['keybindings']
        if 'keybindings' in self.sitePrefsCfg: del self.sitePrefsCfg['keybindings']
        
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app']
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections']
        self.appData = self.appDataCfg
          
        # keybindings:
        self.keysPrefsCfg = self.loadKeysPrefs()  # = merged general + platform prefs, used in psychopyApp.py too
        self.keyDict = self.keysPrefsCfg['keybindings']  # == dict, with items in u'___' format
        self.keys = self.convertKeyDict()  # no longer a dict, no longer u'___' format
        
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
        
    def resetSitePrefs(self):
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
        appDataSpec = configobj.ConfigObj(join(self.paths['appDir'], 'appDataSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['appDataFile'], configspec=appDataSpec)
        resultOfValidate = cfg.validate(self._validator, copy=True, preserve_errors=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        return cfg

    def restoreBadPrefs(self, cfg, resultOfValidate):
        if resultOfValidate == True:
            return
        for (section_list, key, _) in configobj.flatten_errors(cfg, resultOfValidate):
            if key is not None:
                type, default = cfg.configspec[', '.join(section_list)][key].split('default')
                default = default.replace(')','').replace('=','')  # assume default=value) comes at the end of the line
                section = ''.join(section_list)  # == assume there are no nested sections in psychopy prefs
                if default[0] in ['"', "'"]:
                    default = default[1:-1]
                # type conversion:
                if type.find('boolean(') > -1:
                    default = bool(default)
                elif type.find('option(') > -1:
                    pass
                elif type.find('integer(') > -1:
                    default = int(default)
                elif type.find('float(') > -1:
                    default = float(default)
                elif type.find('list(') > -1:
                    default = []  # not correct, but avoids some fatal crashes when starting with bad saved values
                else:
                    default = str(default)
                cfg[section][key] = default
            else:
                print "Section [%s] was missing in file '%s'" % (', '.join(section_list), cfg.filename)  # hopefully not encountered...
        
    def loadSitePrefs(self):
        #load against the spec, then validate and save to a file
        #(this won't overwrite existing values, but will create additional ones if necess)
        prefsSpec = configobj.ConfigObj(join(self.paths['prefs'], 'prefsSite.spec'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['sitePrefsFile'], configspec=prefsSpec)
        resultOfValidate = cfg.validate(self._validator, copy=True, preserve_errors=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        if len(cfg['general']['userPrefsTemplate']) == 0:
            #create the template for first time
            if platform.system() == 'Windows':
                self.paths['userPrefsTemplate'] = "C:\Documents and Settings\USERNAME\Application Data\psychopy2\prefsUser.cfg"
            elif platform.system() == 'Darwin':
                self.paths['userPrefsTemplate'] = '/Users/USERNAME/.psychopy2/prefsUser.cfg'
            else:
                self.paths['userPrefsTemplate'] = '/home/USERNAME/.psychopy2/prefsUser.cfg'
            cfg['general']['userPrefsTemplate'] = self.paths['userPrefsTemplate']  #set path to home
            self.paths['userPrefsFile'] = self.paths['userPrefsTemplate'].replace('USERNAME', activeUser)
            self.paths['userPrefsDir'] = self.paths['userPrefsFile'].replace('prefsUser.cfg', '')
        elif 'userPrefsFile' in self.paths.keys() and not os.path.isfile(self.paths['userPrefsFile']):
            print 'Prefs file %s was not found.\nUsing location %s' %(self.paths['userPrefsFile'], self.paths['userPrefsFile'])
            self.paths['userPrefsFile'] = cfg['general']['userPrefsTemplate'].replace('USERNAME', activeUser)
        else: #set the path to the config
            self.paths['userPrefsFile'] = cfg['general']['userPrefsTemplate'].replace('USERNAME', activeUser)  #set app path to user override
        cfg.initial_comment = ["###", "###     SITE PREFERENCES:  settings here apply to all users; see 'help'",
                                      "###    ---------------------------------------------------------------------", "",
                               "###  General settings, e.g. about scripts, rather than any aspect of the app -----"]
        cfg.final_comment = ["", "", "### [this page is stored at %s]" % self.paths['sitePrefsFile']]
        cfg.filename = self.paths['sitePrefsFile']
        self.paths['userPrefsDir'] = self.paths['userPrefsFile'].replace('prefsUser.cfg', '')
        try:
            cfg.write()
        except:
            pass
        return cfg
    
    def loadPlatformPrefs(self):
        # platform-dependent over-ride of default sitePrefs; validate later (e.g., after merging with platform-general prefs)
        cfg = configobj.ConfigObj(join(self.paths['prefs'], 'prefs' + platform.system() + '.cfg'))
        return cfg
    
    def loadHelpPrefs(self):
        cfg = configobj.ConfigObj(join(self.paths['prefs'], 'prefsHelp.cfg'))
        cfg.filename = self.paths['helpPrefsFile']
        return cfg
    
    def loadKeysPrefs(self):
        """function to load keybindings file, or create a fresh one if its missing
        use a spec file for keys (to ensure that there's at least a default value for all menu items)
        also validate later in convertKeyDict() using reg-ex's
        """
        keysSpec = configobj.ConfigObj(join(self.paths['prefs'], 'prefsKeys.spec'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(join(self.paths['prefs'], 'prefsKeys.cfg'), configspec=keysSpec)
        cfg.merge(self.platformPrefsCfg)
        resultOfValidate = cfg.validate(self._validator, copy=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        if not os.path.isfile(self.paths['keysPrefsFile']):  # then its the first run, or first after resetSitePrefs()
            # copy default + platform-specific key prefs --> newfile to be used on subsequent runs, user can edit + save it
            #cfg.validate(self._validator, copy=True)  #copy means all settings get saved
            for k in cfg.keys(): # remove non-keybindings sections from this cfg because platformPrefs might contain them
                if k <> 'keybindings': del cfg[k]
            cfg.initial_comment = ["###", "###     KEY-BINDINGS:  menu-key assignments, apply to all users; see 'help'",
                                          "###    ---------------------------------------------------------------------"]
            if platform.system() == 'Darwin':
                cfg.initial_comment.append("###     NB:  Ctrl is not available as a key modifier, use Cmd; quit is always Cmd+Q")
            cfg.initial_comment.append("")
            cfg.final_comment = ["", "", "### [this page is stored at %s]" % self.paths['keysPrefsFile']]
            cfg.filename = self.paths['keysPrefsFile']
            try:
                cfg.write()
            except:
                print "failed to write to %s" % self.paths['keysPrefsFile']
        else:
            cfg = configobj.ConfigObj(self.paths['keysPrefsFile'])
            
        return cfg
        
    def loadUserPrefs(self):
        """load user prefs, if any; don't save to a file because doing so will
        break easy_install. saving to files within the psychopy/ is fine, eg for
        key-bindings, but outside it (where user prefs will live) is not allowed
        by easy_install (security risk)
        """
        prefsSpec = configobj.ConfigObj(join(self.paths['prefs'], 'prefsSite.spec'), encoding='UTF8', list_values=False)
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
