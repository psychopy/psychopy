# This specifies defaults for the psychopy prefs
# A prefsSite.cfg will be created from it when psychopy is first run
# these settings can be over-ridden in a platform-dependent way
# e.g., prefsDarwin.cfg makes PsychpoPy feel more Mac-like by default
# users can then further customize their prefs by editing the user prefs page within PsychoPy

# 'NOT_IMPLEMENTED' --> hide prefs that have not been implemented, yet retain for later implementation
# idea: corrupting that pref --> config(_validate) fails, so that pref is ignored (along with its comment on the preceeding line)
# to restore: just remove the text 'NOT_IMPLEMENTED'

[general]
# a template used for all user prefs filenames: 'USERNAME' is replaced with user login)
userPrefsTemplate = string(default='')
# winType is the backend for drawing ('pyglet' or 'pygame')
winType = option('pyglet', 'pygame', default='pyglet')
# default units for windows and visual stimuli (deg', 'norm', 'cm', 'pix')
units = option('deg', 'norm', 'cm', 'pix', default='norm')
fullscr = boolean(default='False')
allowGUI = boolean(default='True')
# 'version' is for internal usage, not for the user
version = string(default='')

##  Application settings, applied to coder and builder windows -----  ##
[app]
# NB: icons on OS X are always large, unless you have a recent version of wx (2.8.7.1 works)
largeIcons = boolean(default='True')
# defaultView can be 'last' (retrieve prev windows), 'builder' or 'coder'
defaultView = option('last', 'builder', 'coder', default='last')
# leave runScripts as 'process':
runScripts = option('process','thread', 'inline', default='process')
# on win32 only, we can allow module imports for analysis of code:
allowModuleImports = boolean(default='False')
# should common libs be imported during launch ('none', 'thread', 'inline')
importLibs = option('none', 'thread', 'inline', default='none')
# will reset site & key prefs to defaults immediately (see 'help' page)
resetSitePrefs = boolean(default='False')

##  Settings for the coder and builder windows, and connections -----  ##
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
defaultTimeUnits = NOT_IMPLEMENTED option('sec', 'ms', default='sec')
reloadPrevExp = boolean(default=False)
# add your own components (comma-separated list; just a comma means an empty list):
componentsFolders = list(default=list('~/.psychopy2/components',))
# or hide components that you'll never use
hiddenComponents = list(default=list(),)

[connections]
# the http proxy (for usage stats and auto-updating, format is 000.000.000.000:0000)
proxy = string(default="")
# autoProxy means override above proxy with values found in environment if possible
autoProxy = boolean(default=True)
# please DO allow anonymous stats to be sent to www.psychopy.org/usage, its helpful for development
allowUsageStats = boolean(default=True)
# checkForUpdates is not yet implemented:
checkForUpdates = NOT_IMPLEMENTED boolean(default=True)  

