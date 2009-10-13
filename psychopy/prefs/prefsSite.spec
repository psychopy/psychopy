# This specifies defaults for the psychopy prefs
# A prefsSite.cfg will be created from it when psychopy is first run
# these settings can be over-ridden in a platform-dependent way
# e.g., prefsDarwin.cfg makes PsychpoPy feel more Mac-like by default
# users can then further customize their prefs by editing the user prefs page within PsychoPy

# in this spec file, '# NOT_IMPLEMENTED' --> hide / delete prefs that have not been implemented, yet retain for later implementation

# each line should have a default= ___, and it should appear as the last item on the line

### General settings
[general]
  # userPrefsTemplate is a template used for all user prefs filenames: 'USERNAME' is replaced with user login
  # (don't change 'USERNAME' or 'prefsUser.cfg', or there will be errors) 
  userPrefsTemplate = string(default='')
  # winType is the backend for drawing ('pyglet' or 'pygame')
  winType = option('pyglet', 'pygame', default='pyglet')
  # default units for windows and visual stimuli ('deg', 'norm', 'cm', 'pix')
  units = option('deg', 'norm', 'cm', 'pix', default='norm')
  fullscr = boolean(default='False')
  allowGUI = boolean(default='True')
  # 'version' is for internal usage, not for the user
  version = string(default='')

###  Application settings, applied to coder, builder, & prefs windows -----
[app]
  # NB: icons on OS X are large (?: unless you have a recent version of wx? wx 2.8.7.1 gives me small icons)
  largeIcons = boolean(default='True')
  # defaultView can be 'builder', 'coder', 'both', or 'last' (retrieve previous windows)
  defaultView = option('last', 'builder', 'coder', 'both', default='last')
  # leave runScripts as 'process':
  runScripts = option('process','thread', 'inline', default='process')
  # on win32 only, we can allow module imports for analysis of code:
  allowModuleImports = boolean(default='False')
  # should common libs be imported during launch ('none', 'thread', 'inline')
  importLibs = option('none', 'thread', 'inline', default='none')
  # will reset site & key prefs to defaults immediately (see 'help' page)
  resetSitePrefs = boolean(default='False')
  # automatically save any unsaved prefences before closing the window
  autoSavePrefs = boolean(default='False')

###  Settings for the coder and builder windows, and connections -----
[coder]
  # Font is a list of font names - the first found on the system will be used
  outputFont = list(default=list('courier', 'Courier New'))
  # Font size (in pts) takes an integer between 6 and 24
  codeFontSize = integer(6,24, default=12)
  outputFontSize = integer(6,24, default=12)
  showSourceAsst = boolean(default=False)
  analysisLevel = integer(0,10,default=1)
  analyseAuto = boolean(default=True)
  showOutput = boolean(default=True)
  reloadPrevFiles = boolean(default=True)

[builder]
  # default time units can be 'sec' or 'ms'
# NOT_IMPLEMENTED defaultTimeUnits = option('sec', 'ms', default='sec')
  reloadPrevExp = boolean(default=False)
  # add your own components (comma-separated list; just a comma means an empty list):
  componentsFolders = list(default=list('~/.psychopy2/components',))
  # a list of components to hide (eg, because you never use them)
  hiddenComponents = list(default=list(),)

[connections]
  # the http proxy (for usage stats and auto-updating, format is 000.000.000.000:0000)
  proxy = string(default="")
  # autoProxy means override above proxy with values found in environment if possible
  autoProxy = boolean(default=True)
  allowUsageStats = boolean(default=True)
  # checkForUpdates is not yet implemented:
# NOT_IMPLEMENTED checkForUpdates = boolean(default=True)  
