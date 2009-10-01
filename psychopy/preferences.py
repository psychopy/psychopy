# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx, wx.stc
import os, sys, urllib, StringIO
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
        self.keys={}  # for keybindings
        
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

    def loadAll(self):
        """A function to allow a class with attributes to be loaded from a
        pickle file necessarily without having the same attribs (so additional
        attribs can be added in future).
        """
        self._validator=configobjValidate.Validator()
        self.appDataCfg = self.loadAppData()
        self.prefsCfg = self.loadSitePrefs()
        self.userPrefsCfg = self.loadUserPrefs()
        #merge site prefs and user prefs
        self.prefsCfg.merge(self.userPrefsCfg)
        self.prefsCfg.validate(self._validator, copy=False)  # validate after the merge
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app']
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections']
        self.appData = self.appDataCfg
           
        # ------start keybindings stuff----------------------------------
        self.keys = self.prefsCfg['keybindings'] # == dict, with items in u'___' format
        
        # now convert dict --> tmpFile in python syntax, import tmpFile --> self.keys
        file = open(join(self.paths['userPrefs'], "tmpKeys.py"), "w") # add try ... except?
        badMenuLabel = False  # flag illegal user-entered keybindings
        for k in self.keys.keys():
            # need to do more validation: deny duplicate bindings, etc
            # ideally tweak user input to be regular, rather than ignore if irregular
            if not re.match("^[a-zA-Z][a-zA-Z0-9_]+$", str(k)): # configobj might do this; ? better: validate against wxIDs.py
                badMenuLabel = True
            regex = re.compile("^(F\d{1,2}|Ctrl[+-]|Alt[+-]|Shift[+-])+([^a-z]{1,1}|F\d{1,2}|Home|Tab|Del|Space|Enter){0,1}$")
            if regex.match(str(self.keys[k])):
                if str(self.keys[k]).find("'") > -1: qDelim = '"'
                else: qDelim = "'"
                file.write("%s" %str(k) + " = " + qDelim + str(self.keys[k]) + qDelim + "\n")
            else:
                pass  # ideally warn the user
        file.close()
        
        if badMenuLabel:
            # print "bad menu-item from pref files, reverting to app defaults"
            from psychopy.app import keybindings
            self.keys = keybindings
        else:
            sys.path.append(self.paths['userPrefs'])
            import tmpKeys
            self.keys = tmpKeys
        os.remove(join(self.paths['userPrefs'], "tmpKeys.py")) # ? also remove tmpKeys.pyc
        
        # eventually handle psychopy-default platform-specific stuff using platform.cfg files, rather than hard-coding it
        if sys.platform.lower().startswith('dar'):
            self.keys.redo = self.keys.redoDarwin
            self.keys.runScript = self.keys.runScriptDarwin
            self.keys.stopScript = self.keys.stopScriptDarwin
        elif sys.platform.lower().startswith('win'):
            self.keys.quit = self.keys.quitWindows
        # ----end keybindings stuff------------------------------------

        #override some platfrom-specific settings
        if sys.platform=='darwin':
            self.prefsCfg['app']['allowModuleImports']=False
        #connections
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
        
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
        elif not os.path.isfile(cfg['general']['userPrefsFile']):
            print 'Prefs file %s was not found.\nUsing file %s' %(cfg['general']['userPrefsFile'], self.paths['userPrefsFile'])
            cfg['general']['userPrefsFile']=self.paths['userPrefsFile']  #set path to home            
        else: #set the path to the config
            self.paths['userPrefsFile'] = cfg['general']['userPrefsFile']  #set app path to user override
        cfg.initial_comment = ["### === SITE PREFERENCES:  prefs set here apply to all users ===== ###",
                               "", "   Any line in green that starts with a '#' is merely a comment, all others are functional",
                               "", "", "##  --- General settings, e.g. about scripts, rather than any aspect of the app -----  ##"]
        cfg.final_comment = ["", "", "[this page is stored at %s]" % self.paths['sitePrefsFile']]
        cfg.filename = self.paths['sitePrefsFile']
        cfg.write()
        return cfg
    
    def loadUserPrefs(self):
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        #create file and validate based on template, but then close and reopen
        #if we validate the file that we actually use then all the settings will be
        #inserted and will override sitePrefs with defaults
        #then add user prefs
        #BUT we also can't write an actual file, because that kills easy_install,
        #so now using a StringIO object

        #check/create path for tmp file
        if not os.path.isdir(self.paths['userPrefs']):
            try: os.makedirs(self.paths['userPrefs'])
            except:
                print "PsychoPy failed to create folder %s. Settings will be read-only" % self.paths['userPrefs']  # was: tmpPath

        tmpPath = join(self.paths['userPrefs'], 'tmp')
        cfg1 = configobj.ConfigObj(tmpPath, configspec=prefsSpec)
        cfg1.validate(self._validator, copy=False)  #copy True = grab sections AND SETTINGS from sitePrefsSpec
        cfg1.initial_comment = ["### === USER PREFERENCES:  prefs set here override the SITE-wide prefs ===== ###", "",
            "To set a preference here, copy & paste the syntax from the 'site' page, then edit the value",
            "Be sure to place it in the right section ([general], [app], and so on)",
            "Any line in green text that starts with a '#' is a comment; all other lines are functional"
            "", ""]
        cfg1.final_comment = ["", "", "[this page is stored at %s]" % self.paths['userPrefsFile']]
        
        buff = StringIO.StringIO()  # ?JRG: where / how used?
        cfg1.write() 
        #then create the actual cfg from this stringIO object
        cfg = configobj.ConfigObj(tmpPath, configspec=prefsSpec)
        cfg.filename = self.paths['userPrefsFile']
        return cfg
    
    def getAutoProxy(self):
        """Fetch the proxy from the the system environment variables
        """
        if urllib.getproxies().has_key('http'):
            return urllib.getproxies()['http']
        else:
            return ""
