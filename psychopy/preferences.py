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
        self.paths['keysPrefsFile']=join(self.paths['psychopy'], 'prefsKeys.cfg')
        
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
        self.keysCfg = self.loadKeysPrefs()
        
        # merge site, platform, and user prefs; order matters
        self.prefsCfg.merge(self.platformPrefsCfg)
        self.prefsCfg.merge(self.userPrefsCfg)
        self.prefsCfg.validate(self._validator, copy=False)  # validate after the merge
        del self.prefsCfg['keybindings']  # only appeared there because of the merge
        if not 'keybindings' in self.userPrefsCfg.keys():  
            self.userPrefsCfg['keybindings'] = {}  # want a keybindings section in userPrefs even if empty
        
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app']
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections']
        self.appData = self.appDataCfg
          
        # keybindings: merge general + platform + user prefs; NB: self.keys means keybindings
        self.keysCfg.merge(self.platformPrefsCfg)
        self.keysCfg.merge(self.userPrefsCfg)
        #self.keysCfg.validate(self._validator, copy=False)  # need a keysSpec file before this does anything?
        for keyOfPref in self.keysCfg.keys(): # idea: hide / remove non-keybindings sections from this cfg
            if keyOfPref <> 'keybindings': del self.keysCfg[keyOfPref]
        self.keys = self.keysCfg['keybindings'] # == dict, with items in u'___' format
        self.keys = self.convertKeys() # no longer a dict, no longer u'___' format
        
        # connections:
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
    
    def convertKeys(self):
        """a function to convert a keybindings dict from cfg files to self.keys
        as expected elsewhere in the app; uses a tmpFile written in python syntax
        (created in the user ./psychopy2 directory), import tmpFile --> self.keys
        """
        useAppDefaultKeys = False  # flag bad situations in which to give up and go with app defaults
        try:
            file = open(join(self.paths['userPrefs'], "tmpKeys.py"), "w")
            keyRegex = re.compile("^(F\d{1,2}|Ctrl[+-]|Alt[+-]|Shift[+-])+(.{1,1}|[Ff]\d{1,2}|Home|Tab){0,1}$", re.IGNORECASE)
            menuRegex = re.compile("^(open|new|save|saveAs|close|quit|cut|copy|paste|"\
                                   "duplicate|indent|dedent|smartIndent|find|findAgain|"\
                                   "undo|redo|comment|uncomment|fold|analyseCode|compileScript|"\
                                   "runScript|stopScript|switchToBuilder|switchToCoder){1,1}$")
            usedKeys = []
            for k in self.keys.keys():
                if self.keys[k] in usedKeys and str(k).find("switchTo") < 0:
                    print "PsychoPy (preferences.py):  duplicate key %s" % str(self.keys[k])
                    useAppDefaultKeys = True
                else:
                    usedKeys.append(self.keys[k])
                if not menuRegex.match(str(k)):
                    print "PsychoPy (preferences.py):  unrecognized menu-item '%s'" % str(k) 
                    useAppDefaultKeys = True
                # make user input more regular
                r = re.compile("(?i)Ctrl[+-]")
                self.keys[k] = r.sub('Ctrl+', str(self.keys[k])) # here convert to str()
                r = re.compile("(?i)Shift[+-]")
                self.keys[k] = r.sub('Shift+', self.keys[k])
                r = re.compile("(?i)Alt[+-]")
                self.keys[k] = r.sub('Alt+', self.keys[k])
                self.keys[k] = "".join([j.capitalize()+"+" for j in str(self.keys[k]).split("+")])[:-1] 
                if keyRegex.match(self.keys[k]):
                    if self.keys[k].find("'") > -1: quoteDelim = '"'
                    else: quoteDelim = "'"
                    file.write("%s" % str(k) + " = " + quoteDelim + self.keys[k] + quoteDelim + "\n")
                else:
                    print "PsychoPy (preferences.py):  bad key %s (menu-item %s)" % (str(self.keys[k]), str(k))
            file.close()  # ?? file never closed if an exception is thrown by something other than open()
        except:
            print "PsychoPy (preferences.py) could not make a temp file in %s (or less likely: could not processs keybindings)" \
                    % join(self.paths['userPrefs'], "tmpKeys.py")
            useAppDefaultKeys = True

        if useAppDefaultKeys:
            print "using default keybindings"
            from psychopy.app import keybindings
            self.keys = keybindings
        else:
            sys.path.append(self.paths['userPrefs'])
            import tmpKeys
            self.keys = tmpKeys
        if os.path.isfile(join(self.paths['userPrefs'], "tmpKeys.py")):
            os.remove(join(self.paths['userPrefs'], "tmpKeys.py"))
        if os.path.isfile(join(self.paths['userPrefs'], "tmpKeys.pyc")):
            os.remove(join(self.paths['userPrefs'], "tmpKeys.pyc"))
        
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
        # platform-dependent over-ride of default sitePrefs
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(join(self.paths['psychopy'], 'prefs' + platform.system() + '.cfg'), configspec=prefsSpec)
        cfg.validate(self._validator, copy=False) 
        return cfg
    
    def loadKeysPrefs(self):
        # platform-general (no-arch) keybindings 
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        cfg = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsKeys.cfg'), configspec=prefsSpec)  
        cfg.validate(self._validator, copy=False) 
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
            "To set a preference here: copy & paste the syntax from the 'site' or 'keys' page", 
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
