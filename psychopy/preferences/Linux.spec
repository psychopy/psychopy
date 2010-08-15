# This specifies defaults for the psychopy prefs
# A prefsSite.cfg will be created from it when psychopy is first run
# these settings can be over-ridden in a platform-dependent way
# e.g., prefsDarwin.cfg makes PsychpoPy feel more Mac-like by default
# users can then further customize their prefs by editing the user prefs page within PsychoPy

# in this spec file, '# NOT_IMPLEMENTED' --> hide / delete prefs that have not been implemented, yet retain for later implementation

# each line should have a default= ___, and it should appear as the last item on the line

### General settings
[general]
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
    outputFont = list(default=list('Courier', 'Courier New'))
    # Font size (in pts) takes an integer between 6 and 24
    codeFontSize = integer(6,24, default=12)
    outputFontSize = integer(6,24, default=12)
    showSourceAsst = boolean(default=False)
    analysisLevel = integer(0,10,default=1)
    analyseAuto = boolean(default=True)
    showOutput = boolean(default=True)
    reloadPrevFiles = boolean(default=True)

[builder]
    # NOT_IMPLEMENTED defaultTimeUnits = option('sec', 'frames', default='sec')
    reloadPrevExp = boolean(default=False)
    # if False will create scripts with an 'easier' but more cluttered namespace
    unclutteredNamespace = boolean(default=False)
    # for the user to add custom components (comma-separated list)
    componentsFolders = list(default=list('/Users/Shared/PsychoPy2/components'))
    # a list of components to hide (eg, because you never use them)
    hiddenComponents = list(default=list())
  
[connections]
    # the http proxy (for usage stats and auto-updating, format is 000.000.000.000:0000)
    proxy = string(default="")
    # autoProxy means override above proxy with values found in environment if possible
    autoProxy = boolean(default=True)
    allowUsageStats = boolean(default=True)
    checkForUpdates = boolean(default=True)
  
[keyBindings]
    # File:
    open = string(default='Ctrl+O')
    new = string(default='Ctrl+N')
    save = string(default='Ctrl+S')
    saveAs = string(default='Ctrl+Shift+S')
    close = string(default='Ctrl+W')
    quit = string(default='Ctrl+Q')

    # Edit:
    cut = string(default='Ctrl+X')
    copy = string(default='Ctrl+C')
    paste = string(default='Ctrl+V')
    duplicate = string(default='Ctrl+D')
    indent = string(default='Ctrl+]')
    dedent = string(default='Ctrl+[')
    smartIndent = string(default='Shift+Tab')
    find = string(default='Ctrl+F')
    findAgain = string(default='Ctrl+G')
    undo = string(default='Ctrl+Z')
    redo = string(default='Ctrl+Shift+Z')
    comment = string(default="Ctrl+'")
    uncomment = string(default="Ctrl+Shift+'")
    fold = string(default='Ctrl+Home')

    # Tools:
    analyseCode = string(default='F4')
    compileScript = string(default='F5')
    runScript = string(default='Ctrl+R')
    stopScript = string(default='Ctrl+.')

    # View:
    toggleWhitespace = string(default='Ctrl+Shift+W')
    toggleEOLs = string(default='Ctrl+Shift+L')
    toggleIndentGuides = string(default='Ctrl+Shift+I')
    toggleOutputPanel = string(default='Ctrl+Shift+O')
    switchToBuilder = string(default='Ctrl+L')
    switchToCoder = string(default='Ctrl+L')
    
    # Experiment (Builder only)
    newRoutine = string(default='Ctrl+Shift+N')
    copyRoutine = string(default='Ctrl+Shift+C')
    pasteRoutine = string(default='Ctrl+Shift+V')