Preferences
====================================

.. _generalSettings:

General settings
-------------------
winType:
    PsychoPy can use one of two 'backends' for creating windows and drawing; pygame and pyglet. Here 
    you can set the default backend to be used.
    
units:
    Default units for windows and visual stimuli ('deg', 'norm', 'cm', 'pix'). See :ref:`units`.  Can be overridden by individual experiments.
    
fullscr:
    Should windows be created full screen by default? Can be overridden by individual experiments.

allowGUI:
    When the window is created, should the frame of the window and the mouse pointer be visible.
    If set to False then both will be hidden.

.. _applicationSettings:

Application settings
---------------------------
These settings are common to all components of the application (Coder and Builder etc)

largeIcons:
    Do you want large icons (on some versions of wx on OS X this has no effect)
    
defaultView:
    Determines which view(s) open when the PsychoPy app starts up. Default is 'last',
    which fetches the same views as were open when PsychoPy last closed.
    
runScripts:
    Don't ask. ;-) Just leave this option as 'process' for now!
    
allowModuleImports (only used by win32):
    Allow modules to be imported at startup for analysis by source assistant. This will
    cause startup to be slightly slower but will speedup the first analysis of a script. 
  
.. _coderSettings:

Coder settings
---------------------------
outputFont:
    a list of font names to be used in the output panel. The first found on the system will be used
    
fontSize (in pts):
    an integer between 6 and 24 that specifies the size of fonts
    
codeFontSize = integer(6,24, default=12)

outputFontSize = integer(6,24, default=12)

showSourceAsst:
    Do you want to show the `source assistant` panel (to the right of the Coder view)?
    On windows this provides help about the current function if it can be found. On
    OS X the source assistant is of limited use and is disabled by default.
    
analysisLevel:
    If using the source assistant, how much depth should PsychoPy try to analyse the 
    current script? Lower values may reduce the amount of analysis performed and
    make the Coder view more responsive (particularly for files that import many modules
    and sub-modules).

analyseAuto:
    If using the source assistant, should PsychoPy try to analyse the current script 
    on every save/load of the file? The code can be analysed manually from the tools menu
    
showOutput:
    Show the output panel in the Coder view. If shown all python output from the session
    will be output to this panel. Otherwise it will be directed to the original location
    (typically the terminal window that called PsychoPy application to open).

reloadPrevFiles:
    Should PsychoPy fetch the files that you previously had open when it launches?

.. _builderSettings:

Builder settings
---------------------------
reloadPrevExp (default=False):
    for the user to add custom components (comma-separated list)
    
componentsFolders:
    a list of folder pathnames that can hold additional custom components for the Builder view
    
hiddenComponents:
    a list of components to hide (e.g., because you never use them)
  
.. _connectionSettings:

Connection settings
---------------------------
proxy:
    The proxy server used to connect to the internet if needed. Must be of the form `http://111.222.333.444:5555`
    
autoProxy:
    PsychoPy should try to deduce the proxy automatically (if this is True and autoProxy is successful 
    then the above field should contain a valid proxy address).
    
allowUsageStats:
    Allow PsychoPy to ping a website at when the application starts up. **Please** leave this
    set to True. The info sent is simply a string that gives the date, PsychoPy version and platform info.
    There is no cost to you: no data is sent that could identify you and PsychoPy will not be delayed in starting as a result.
    The aim is simple: if we can show that lots of people are using PsychoPy there is a greater chance of it being
    improved faster in the future.
    
checkForUpdates:
    PsychoPy can (hopefully) automatically fetch and install updates. This will only work for minor updates
    and is still in a very experimental state (as of v1.51.00).
  
.. _keyBindings:

Key bindings
------------------
There are many shortcut keys that you can use in PsychoPy. For instance did you realise that
you can indent or outdent a block of code with Ctrl-[ and Ctrl-] ?
