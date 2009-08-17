# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx, wx.stc
import os, sys, urllib
from shutil import copyfile
import configobj, configobjValidate

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
        
        self.getPaths()
        self.loadAll()            
        
    def getPaths(self):
        #on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath= os.path.abspath(__file__)
        dirPsychoPy = os.path.split(thisFileAbsPath)[0]
        #paths to user settings
        if sys.platform=='win32':
            dirUserPrefs = join(os.environ['APPDATA'],'psychoy2') #the folder where the user cfg file is stored
        else:
            dirUserPrefs = join(os.environ['HOME'], '.psychopy2')
        #from the directory for preferences work out the path for preferences (incl filename)
        if not os.path.isdir(dirUserPrefs):
            os.makedirs(dirUserPrefs)
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
        self.prefsCfg.validate(self._validator, copy=False)#validate after the merge
        #simplify namespace
        self.general=self.prefsCfg['general']
        self.app = self.prefsCfg['app'] 
        self.coder=self.prefsCfg['coder']
        self.builder=self.prefsCfg['builder']
        self.connections=self.prefsCfg['connections'] 
        self.appData = self.appDataCfg

        #override some platfrom-specific settings
        if sys.platform=='darwin':
            self.prefsCfg['app']['allowImportModules']=False            
        #connections
        if self.connections['autoProxy']: self.connections['proxy'] = self.getAutoProxy()
    def saveAppData(self):
        """Save the various setting to the appropriate files (or discard, in some cases)
        """
        self.appDataCfg.validate(self._validator, copy=True)#copy means all settings get saved
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
        cfg.validate(self._validator, copy=True)#copy means all settings get saved
        if len(cfg['general']['userPrefsFile'])==0:
            cfg['general']['userPrefsFile']=self.paths['userPrefsFile']#set path to home
        else: self.paths['userPrefsFile']=cfg['general']['userPrefsFile']#set app path to user override
        cfg.initial_comment=["#preferences set in this file apply to all users",
            "the file can be found at %s" %self.paths['sitePrefsFile']]
        cfg.write()#so the user can see what's (now) available
        return cfg
    def loadUserPrefs(self):  
        prefsSpec = configobj.ConfigObj(join(self.paths['psychopy'], 'prefsSpec.cfg'), encoding='UTF8', list_values=False)
        #check for folder
        if not os.path.isfile(self.paths['userPrefsFile']):
            #create file and validate based on template, but then close and reopen
            #if we validate the file that we actually use then all the settings will be
            #inserted and will override sitePrefs with defaults
            #then add user prefs
            cfg1 = configobj.ConfigObj(self.paths['userPrefsFile'], configspec=prefsSpec)
            cfg1.validate(self._validator, copy=False)#copy means all settings get saved   
            cfg1.initial_comment=["#preferences set in this file will override the site-prefs",
                "#to set a preference here simply copy and paste from the site-prefs file",
                "the file can be found at %s" %self.paths['userPrefsFile']]
            cfg1.write()
        cfg = configobj.ConfigObj(self.paths['userPrefsFile'], configspec=prefsSpec)
        return cfg
    def getAutoProxy(self):
        """Fetch the proxy from the the system environment variables
        """
        if urllib.getproxies().has_key('http'):
            return urllib.getproxies()['http']
        else:
            return ""
        