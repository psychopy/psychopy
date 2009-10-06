# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx, wx.stc
import os, sys, urllib, StringIO, platform
from shutil import copyfile
import configobj, configobjValidate, re

#GET PATHS------------------
join = os.path.join

class Preferences:
    def __init__(self):
        self.prefsCfg=None#the config object for the preferences
        self.appDataCfg=None #the config object for the app data (users don't need to see)

        self.general=None
        self.coder=None
        self.builder=None
        self.connections=None
        self.paths={}#this will remain a dictionary
        self.keys = {}  # for keybindings
        
        self.getPaths()
        self.loadAll()
        
    def getPaths(self):
        #on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath= os.path.abspath(__file__)
        dirPsychoPy = os.path.split(thisFileAbsPath)[0]
        #paths to user settings
        if sys.platform=='win32':
            dirUserPrefs = join(os.environ['APPDATA'],'psychopy2') #the folder where the user cfg file is stored
        else:
            dirUserPrefs = join(os.environ['HOME'], '.psychopy2')
        #from the directory for preferences work out the path for preferences (incl filename)
#        if not os.path.isdir(dirUserPrefs):
#            os.makedirs(dirUserPrefs)
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
        self.paths['userPrefs']=dirUserPrefs
        self.paths['userPrefsFile']=join(dirUserPrefs, 'prefsUser.cfg')
        self.paths['appDataFile']=join(dirUserPrefs,'appData.cfg')
        self.paths['sitePrefsFile']=join(self.paths['psychopy'], 'prefsSite.cfg')
        self.paths['keysPrefsFile']=join(self.paths['psychopy'], 'prefsSiteKeys.cfg')
        
    def loadAll(self):
        """A function to allow a class with attributes to be loaded from a
        pickle file necessarily without having the same attribs (so additional
        attribs can be added in future).
        """
        self._validator=configobjValidate.Validator()
        self.appDataCfg = self.loadAppData()
        self.prefsCfg = self.loadSitePrefs()
        self.platformPrefsCfg = self.loadPlatformPrefs()
        self.userPrefsCfg = self.loadUserPrefs()
        
        # merge site, platform, and user prefs; order matters
        self.prefsCfg.merge(self.platformPrefsCfg)
        self.prefsCfg.merge(self.userPrefsCfg)
        self.prefsCfg.validate(self._validator, copy=False)  # validate after the merge
        del self.prefsCfg['keybindings']  # appeared after merge with platform prefs which can have keybindings
        
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app']
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections']
        self.appData = self.appDataCfg
          
        # keybindings: merge general + platform prefs; userPrefs should not have keybindings
        self.keysCfg = self.loadKeysPrefs()
        self.keyDict = self.keysCfg['keybindings'] # == dict, with items in u'___' format
        self.keys = self.convertKeyDict() # no longer a dict, no longer u'___' format
        
        # connections:
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
    
    def convertKeyDict(self):
        """a function to convert a keybindings dict from cfg files to self.keys
        as expected elsewhere in the app; uses a tmpFile written in python syntax
        (created in the user ./psychopy2 directory), import tmpFile --> self.keys
        """
        useAppDefaultKeys = False  # flag bad situations in which to give up and go with app defaults
        try: 
            tmpFile = join(self.paths['psychopy'], "tmpKeys.py")
            file = open(tmpFile, "w")  # I tried this as StringIO obj, but couldn't import its contents as python code (is there a way?)
            usedKeys = []
            keyRegex = re.compile("^(F\d{1,2}|Ctrl[+-]|Alt[+-]|Shift[+-])+(.{1,1}|[Ff]\d{1,2}|Home|Tab){0,1}$", re.IGNORECASE)
            menuRegex = re.compile("^(open|new|save|saveAs|close|quit|cut|copy|paste|"\
                                   "duplicate|indent|dedent|smartIndent|find|findAgain|"\
                                   "undo|redo|comment|uncomment|fold|analyseCode|compileScript|"\
                                   "runScript|stopScript|switchToBuilder|switchToCoder)$")
            for k in self.keyDict.keys():
                keyK = str(self.keyDict[k])
                k = str(k)
                if keyK in usedKeys and k.find("switchTo") < 0:  # hard-code allowed duplicates (e.g., Ctrl+L)
                    print "PsychoPy (preferences.py):  duplicate key %s" % keyK
                    useAppDefaultKeys = True
                else:
                    usedKeys.append(keyK)
                if not menuRegex.match(k):
                    print "PsychoPy (preferences.py):  unrecognized menu-item '%s'" % k 
                    useAppDefaultKeys = True
                # standardize user input
                keyK = re.sub(r"(?i)Ctrl[+-]", 'Ctrl+', keyK)  
                keyK = re.sub(r"(?i)Cmd[+-]", 'Ctrl+', keyK)
                keyK = re.sub(r"(?i)Shift[+-]", 'Shift+', keyK)
                keyK = re.sub(r"(?i)Alt[+-]", 'Alt+', keyK)
                keyK = "".join([j.capitalize()+"+" for j in keyK.split("+")])[:-1] 
                # screen / validate
                if keyRegex.match(keyK) and not re.match(r"(F\d{1,2}).+", keyK):
                    if self.keyDict[k].find("'") > -1: quoteDelim = '"'
                    else: quoteDelim = "'"
                    file.write("%s" % str(k) + " = " + quoteDelim + keyK + quoteDelim + "\n")
                else:
                    print "PsychoPy (preferences.py):  bad key %s (menu-item %s)" % keyK, k
            file.close()
        except:
            print "PsychoPy (preferences.py) could not create temp file %s (or could not processs keybindings)" % tmpFile
            useAppDefaultKeys = True

        if useAppDefaultKeys:
            print "using default key bindings"
            from psychopy.app import keybindings
            self.keys = keybindings
        else:
            from psychopy import tmpKeys
            self.keys = tmpKeys
        if os.path.isfile(tmpFile):
            os.remove(tmpFile)
        if os.path.isfile(tmpFile+"c"):
            os.remove(tmpFile+"c")
        
        return self.keys
        
    def saveAppData(self):
        """Save the various setting to the appropriate files (or discard, in some cases)
        """
        self.appDataCfg.validate(self._validator, copy=True)#copy means all settings get saved
        if not os.path.isdir(self.paths['userPrefs']):
            os.makedirs(self.paths['userPrefs'])
        self.appDataCfg.write()
    def resetSitePrefs(self):
        """Reset the site preferences to the original defaults (to reset user prefs, just delete entries)
        """
        if os.path.isfile(self.paths['sitePrefsFile']):
            os.remove(self.paths['sitePrefsFile'])
        if os.path.isfile(self.paths['keysPrefsFile']):
            os.remove(self.paths['keysPrefsFile'])
            
    def loadAppData(self):
        #fetch appData too against a config spec
        appDataSpec = configobj.ConfigObj(join(self.paths['appDir'], 'appDataSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['appDataFile'], configspec=appDataSpec)
        cfg.validate(self._validator, copy=True)
        return cfg
    
    def loadSitePrefs(self):
        #load against the spec, then validate and save to a file
        #(this won't overwrite existing values, but will create additional ones if necess)
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(self.paths['sitePrefsFile'], configspec=prefsSpec)
        cfg.validate(self._validator, copy=True)  #copy means all settings get saved
        if len(cfg['general']['userPrefsFile']) == 0:
            #create file for first time
            cfg['general']['userPrefsFile']=self.paths['userPrefsFile']  #set path to home
            tmp = open(cfg['general']['userPrefsFile'], 'a')  # create empty file; use 'a' to append, just safer
            tmp.close()  # idea: sidestep warning message in 2nd run of pp if user does not save prefs in 1st run
        elif not os.path.isfile(cfg['general']['userPrefsFile']):
            print 'Prefs file %s was not found.\nUsing file %s' %(cfg['general']['userPrefsFile'], self.paths['userPrefsFile'])
            cfg['general']['userPrefsFile']=self.paths['userPrefsFile']  #set path to home            
        else: #set the path to the config
            self.paths['userPrefsFile'] = cfg['general']['userPrefsFile']  #set app path to user override
        cfg.initial_comment = ["### === SITE PREFERENCES:  settings here apply to all users ===== ###",
                               "", "##  --- General settings, e.g. about scripts, rather than any aspect of the app -----  ##"]
        cfg.final_comment = ["", "", "[this page is stored at %s]" % self.paths['sitePrefsFile']]
        cfg.filename = self.paths['sitePrefsFile']
        cfg.write()
        return cfg
    
    def loadPlatformPrefs(self):
        # platform-dependent over-ride of default sitePrefs; validate later (e.g., after merging with platform-general prefs)
        cfg = configobj.ConfigObj(join(self.paths['psychopy'], 'prefs' + platform.system() + '.cfg'))
        return cfg
    
    def loadKeysPrefs(self):
        """function to load keybindings file, or create a fresh one if its missing
        don't cfg.validate() here because key-info is string, too variable to use explicit 'option'
        do validate later in convertKeyDict() using reg-ex's
        """
        if not os.path.isfile(self.paths['keysPrefsFile']):  # then its the first run, or first after resetSitePrefs()
            # copy default + platform-specific key prefs --> newfile to be used on subsequent runs, user can edit + save it
            cfg = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsKeys.cfg'))
            cfg.merge(self.platformPrefsCfg)
            for keyOfPref in cfg.keys(): # remove non-keybindings sections from this cfg because platformPrefs might contain them
                if keyOfPref <> 'keybindings':
                    del self.keysCfg[keyOfPref]
            cfg.filename = self.paths['keysPrefsFile']
            cfg.write()
        else:
            cfg = configobj.ConfigObj(self.paths['keysPrefsFile'])
        
        return cfg
        
    def loadUserPrefs(self):
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        #check/create path for user prefs
        if not os.path.isdir(self.paths['userPrefs']):
            try: os.makedirs(self.paths['userPrefs'])
            except:
                print "PsychoPy (preferences.py) failed to create folder %s. Settings will be read-only" % self.paths['userPrefs']  # was: tmpPath
        #then get the configuration file
        cfg = configobj.ConfigObj(self.paths['userPrefsFile'], configspec=prefsSpec)
        cfg.validate(self._validator, copy=False)
        cfg.initial_comment = ["### === USER PREFERENCES:  settings here override the SITE-wide prefs ===== ###", "",
            "To set a preference here: copy & paste the syntax from the 'site' page", 
            "placing it under the correct section ([general], [app], etc.) then edit the value",
            "A line in green text that starts with a '#' is a comment (like this line)", ""]
        cfg.final_comment = ["", "", "[this page is stored at %s]" % self.paths['userPrefsFile']]
        return cfg
    
    def getAutoProxy(self):
        """Fetch the proxy from the the system environment variables
        """
        if urllib.getproxies().has_key('http'):
            return urllib.getproxies()['http']
        else:
            return ""
