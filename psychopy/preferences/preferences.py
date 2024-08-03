#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import os
import sys
import platform
from pathlib import Path
from .. import __version__

from packaging.version import Version
import shutil

try:
    import configobj
    if (sys.version_info.minor >= 7 and
            Version(configobj.__version__) < Version('5.1.0')):
        raise ImportError('Installed configobj does not support Python 3.7+')
    _haveConfigobj = True
except ImportError:
    _haveConfigobj = False


if _haveConfigobj:  # Use the "global" installation.
    from configobj import ConfigObj
    try:
        from configobj import validate
    except ImportError:  # Older versions of configobj
        import validate
else:  # Use our contrib package if configobj is not installed or too old.
    from psychopy.contrib import configobj
    from psychopy.contrib.configobj import ConfigObj
    from psychopy.contrib.configobj import validate
join = os.path.join


class Preferences:
    """Users can alter preferences from the dialog box in the application,
    by editing their user preferences file (which is what the dialog box does)
    or, within a script, preferences can be controlled like this::

        import psychopy
        psychopy.prefs.hardware['audioLib'] = ['ptb', 'pyo','pygame']
        print(psychopy.prefs)
        # prints the location of the user prefs file and all the current vals

    Use the instance of `prefs`, as above, rather than the `Preferences` class
    directly if you want to affect the script that's running.
    """

    # Names of legacy parameters which are needed for use version
    legacy = [
        "winType",  # 2023.1.0
        "audioLib",  # 2023.1.0
        "audioLatencyMode",  # 2023.1.0
    ]

    def __init__(self):
        super(Preferences, self).__init__()
        self.userPrefsCfg = None  # the config object for the preferences
        self.prefsSpec = None  # specifications for the above
        # the config object for the app data (users don't need to see)
        self.appDataCfg = None

        self.general = None
        self.piloting = None
        self.coder = None
        self.builder = None
        self.connections = None
        self.paths = {}  # this will remain a dictionary
        self.keys = {}  # does not remain a dictionary

        self.getPaths()
        self.loadAll()
        # setting locale is now handled in psychopy.localization.init
        # as called upon import by the app

        if self.userPrefsCfg['app']['resetPrefs']:
            self.resetPrefs()

    def __str__(self):
        """pretty printing the current preferences"""
        strOut = "psychopy.prefs <%s>:\n" % (
            join(self.paths['userPrefsDir'], 'userPrefs.cfg'))
        for sectionName in ['general', 'coder', 'builder', 'connections']:
            section = getattr(self, sectionName)
            for key, val in list(section.items()):
                strOut += "  prefs.%s['%s'] = %s\n" % (
                    sectionName, key, repr(val))
        return strOut

    def resetPrefs(self):
        """removes userPrefs.cfg, does not touch appData.cfg
        """
        userCfg = join(self.paths['userPrefsDir'], 'userPrefs.cfg')
        try:
            os.unlink(userCfg)
        except Exception:
            msg = "Could not remove prefs file '%s'; (try doing it manually?)"
            print(msg % userCfg)
        self.loadAll()  # reloads, now getting all from .spec

    def getPaths(self):
        """Get the paths to various directories and files used by PsychoPy.

        If the paths are not found, they are created. Usually, this is only
        necessary on the first run of PsychoPy. However, if the user has
        deleted or moved the preferences directory, this method will recreate 
        those directories.

        """
        # on mac __file__ might be a local path, so make it the full path
        thisFileAbsPath = os.path.abspath(__file__)
        prefSpecDir = os.path.split(thisFileAbsPath)[0]
        dirPsychoPy = os.path.split(prefSpecDir)[0]
        exePath = sys.executable

        # path to Resources (icons etc)
        dirApp = join(dirPsychoPy, 'app')
        if os.path.isdir(join(dirApp, 'Resources')):
            dirResources = join(dirApp, 'Resources')
        else:
            dirResources = dirApp

        self.paths['psychopy'] = dirPsychoPy
        self.paths['appDir'] = dirApp
        self.paths['appFile'] = join(dirApp, 'PsychoPy.py')
        self.paths['demos'] = join(dirPsychoPy, 'demos')
        self.paths['resources'] = dirResources
        self.paths['assets'] = join(dirPsychoPy, "assets")
        self.paths['tests'] = join(dirPsychoPy, 'tests')
        # path to libs/frameworks
        if 'PsychoPy.app/Contents' in exePath:
            self.paths['libs'] = exePath.replace("MacOS/python", "Frameworks")
        else:
            self.paths['libs'] = ''  # we don't know where else to look!
        if not Path(self.paths['appDir']).is_dir():
            # if there isn't an app folder at all then this is a lib-only psychopy
            # so don't try to load app prefs etc
            NO_APP = True
        if sys.platform == 'win32':
            self.paths['prefsSpecFile'] = join(prefSpecDir, 'Windows.spec')
            self.paths['userPrefsDir'] = join(os.environ['APPDATA'],
                                              'psychopy3')
        else:
            self.paths['prefsSpecFile'] = join(prefSpecDir,
                                               platform.system() + '.spec')
            self.paths['userPrefsDir'] = join(os.environ['HOME'],
                                              '.psychopy3')

        # directory for files created by the app at runtime needed for operation
        self.paths['userCacheDir'] = join(self.paths['userPrefsDir'], 'cache')

        # paths in user directory to create/check write access
        userPrefsPaths = (
            'userPrefsDir',  # root dir
            'themes',  # define theme path
            'fonts',  # find / copy fonts
            'packages',  # packages and plugins
            'configs',  # config files for plugins
            'cache',  # cache for downloaded and other temporary files
        )

        # build directory structure inside user directory
        for userPrefPath in userPrefsPaths:
            # define path
            if userPrefPath != 'userPrefsDir':  # skip creating root, just check
                self.paths[userPrefPath] = join(
                    self.paths['userPrefsDir'],
                    userPrefPath)
            # avoid silent fail-to-launch-app if bad permissions:
            try:
                os.makedirs(self.paths[userPrefPath])
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise

        # site-packages root directory for user-installed packages
        userPkgRoot = Path(self.paths['packages'])

        # Package paths for custom user site-packages, these should be compliant
        # with platform specific conventions.
        if sys.platform == 'win32':
            pyDirName = "Python" + sys.winver.replace(".", "")
            userPackages = userPkgRoot / pyDirName / "site-packages"
            userInclude = userPkgRoot / pyDirName / "Include"
            userScripts = userPkgRoot / pyDirName / "Scripts"
        elif sys.platform == 'darwin' and sys._framework:  # macos + framework
            pyVersion = sys.version_info
            pyDirName = "python{}.{}".format(pyVersion[0], pyVersion[1])
            # Standard scheme of lib directories for OSX framework does not
            # distinguish between python versions. We must modify the
            # site-packages root directory to provide a unique path for
            # each python version.
            self.paths['packages'] = join(self.paths['packages'], pyDirName)
            try:
                os.makedirs(self.paths[userPrefPath])
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
            userPkgRoot = Path(self.paths['packages'])  # reload userPkgRoot
            # See the ox_framework_user scheme standard:
            # https://docs.python.org/3/library/sysconfig.html#osx-framework-user
            userPackages = userPkgRoot / "lib" / "python" / "site-packages"
            userInclude = userPkgRoot / "include" / pyDirName
            userScripts = userPkgRoot / "bin"
        else:  # posix (including linux and macos without framework)
            pyVersion = sys.version_info
            pyDirName = "python{}.{}".format(pyVersion[0], pyVersion[1])
            userPackages = userPkgRoot / "lib" / pyDirName / "site-packages"
            userInclude = userPkgRoot / "include" / pyDirName
            userScripts = userPkgRoot / "bin"

        # populate directory structure for user-installed packages
        if not userPackages.is_dir():
            userPackages.mkdir(parents=True)
        if not userInclude.is_dir():
            userInclude.mkdir(parents=True)
        if not userScripts.is_dir():
            userScripts.mkdir(parents=True)

        # add paths from plugins/packages (installed by plugins manager)
        self.paths['userPackages'] = userPackages
        self.paths['userInclude'] = userInclude
        self.paths['userScripts'] = userScripts

        # Get dir for base and user themes
        baseThemeDir = Path(self.paths['appDir']) / "themes" / "spec"
        userThemeDir = Path(self.paths['themes'])
        # Check what version user themes were last updated in
        if (userThemeDir / "last.ver").is_file():
            with open(userThemeDir / "last.ver", "r") as f:
                lastVer = Version(f.read())
        else:
            # if no version available, assume it was the first version to have themes
            lastVer = Version("2020.2.0")
        # If version has changed since base themes last copied, they need updating
        updateThemes = lastVer < Version(__version__)
        # Copy base themes to user themes folder if missing or need update
        for file in baseThemeDir.glob("*.json"):
            if updateThemes or not (Path(self.paths['themes']) / file.name).is_file():
                shutil.copyfile(
                    file,
                    Path(self.paths['themes']) / file.name
                )

    def loadAll(self):
        """Load the user prefs and the application data
        """
        self._validator = validate.Validator()

        # note: self.paths['userPrefsDir'] gets set in loadSitePrefs()
        self.paths['appDataFile'] = join(
            self.paths['userPrefsDir'], 'appData.cfg')
        self.paths['userPrefsFile'] = join(
            self.paths['userPrefsDir'], 'userPrefs.cfg')

        # If PsychoPy is tucked away by Py2exe in library.zip, the preferences
        # file cannot be found. This hack is an attempt to fix this.
        libzip = "\\library.zip\\psychopy\\preferences\\"
        if libzip in self.paths["prefsSpecFile"]:
            self.paths["prefsSpecFile"] = self.paths["prefsSpecFile"].replace(
                libzip, "\\resources\\")

        self.userPrefsCfg = self.loadUserPrefs()
        self.appDataCfg = self.loadAppData()
        self.validate()

        # simplify namespace
        self.general = self.userPrefsCfg['general']
        self.app = self.userPrefsCfg['app']
        self.coder = self.userPrefsCfg['coder']
        self.builder = self.userPrefsCfg['builder']
        self.hardware = self.userPrefsCfg['hardware']
        self.piloting = self.userPrefsCfg['piloting']
        self.connections = self.userPrefsCfg['connections']
        self.appData = self.appDataCfg

        # keybindings:
        self.keys = self.userPrefsCfg['keyBindings']

    def loadUserPrefs(self):
        """load user prefs, if any; don't save to a file because doing so
        will break easy_install. Saving to files within the psychopy/ is
        fine, eg for key-bindings, but outside it (where user prefs will
        live) is not allowed by easy_install (security risk)
        """
        self.prefsSpec = ConfigObj(self.paths['prefsSpecFile'],
                                   encoding='UTF8', list_values=False)

        # check/create path for user prefs
        if not os.path.isdir(self.paths['userPrefsDir']):
            try:
                os.makedirs(self.paths['userPrefsDir'])
            except Exception:
                msg = ("Preferences.py failed to create folder %s. Settings"
                       " will be read-only")
                print(msg % self.paths['userPrefsDir'])
        # then get the configuration file
        cfg = ConfigObj(self.paths['userPrefsFile'],
                        encoding='UTF8', configspec=self.prefsSpec)
        # cfg.validate(self._validator, copy=False)  # merge then validate
        # don't cfg.write(), see explanation above
        return cfg

    def saveUserPrefs(self):
        """Validate and save the various setting to the appropriate files
        (or discard, in some cases)
        """
        self.validate()
        if not os.path.isdir(self.paths['userPrefsDir']):
            os.makedirs(self.paths['userPrefsDir'])
        self.userPrefsCfg.write()

    def loadAppData(self):
        """Fetch app data config (unless this is a lib-only installation)
        """
        appDir = Path(self.paths['appDir'])
        if not appDir.is_dir():  # if no app dir this may be just lib install
            return {}
        # fetch appData too against a config spec
        appDataSpec = ConfigObj(join(self.paths['appDir'], 'appData.spec'),
                                encoding='UTF8', list_values=False)
        cfg = ConfigObj(self.paths['appDataFile'],
                        encoding='UTF8', configspec=appDataSpec)
        resultOfValidate = cfg.validate(self._validator,
                                        copy=True,
                                        preserve_errors=True)
        self.restoreBadPrefs(cfg, resultOfValidate)
        # force favComponent level values to be integers
        if 'favComponents' in cfg['builder']:
            for key in cfg['builder']['favComponents']:
                _compKey = cfg['builder']['favComponents'][key]
                cfg['builder']['favComponents'][key] = int(_compKey)
        return cfg

    def saveAppData(self):
        """Save the various setting to the appropriate files
        (or discard, in some cases)
        """
        # copy means all settings get saved:
        self.appDataCfg.validate(self._validator, copy=True)
        if not os.path.isdir(self.paths['userPrefsDir']):
            os.makedirs(self.paths['userPrefsDir'])
        self.appDataCfg.write()

    def validate(self):
        """Validate (user) preferences and reset invalid settings to defaults
        """
        result = self.userPrefsCfg.validate(self._validator, copy=True)
        self.restoreBadPrefs(self.userPrefsCfg, result)

    def restoreBadPrefs(self, cfg, result):
        """result = result of validate
        """
        if result == True:
            return
        vtor = validate.Validator()
        for sectionList, key, _ in configobj.flatten_errors(cfg, result):
            if key is not None:
                _secList = ', '.join(sectionList)
                val = cfg.configspec[_secList][key]
                cfg[_secList][key] = vtor.get_default_value(val)
            else:
                msg = "Section [%s] was missing in file '%s'"
                print(msg % (', '.join(sectionList), cfg.filename))

prefs = Preferences()
