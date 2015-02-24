Preferences
====================================

.. _applicationSettings:

Application settings
---------------------------
These settings are common to all components of the application (Coder and Builder etc)

showTips:
    Display tips when starting PsychoPy.

largeIcons:
    Do you want large icons (on some versions of wx on OS X this has no effect)?

defaultView:
    Determines which view(s) open when the PsychoPy app starts up. Default is ‘last’, which fetches the same views as were open when PsychoPy last closed.

resetPrefs:
    Reset preferences to defaults on next restart of PsychoPy.

autosavePrefs:
    Save any unsaved preferences before closing the window.

debugMode:
    Enable features for debugging PsychoPy itself, including unit-tests.

locale:
    Language to use in menus etc.; not all translations are available. Select a value, then restart the app. Think about :doc:`adding translations for your language</developers/localization>`.


.. _builderSettings:

Builder settings
---------------------------
reloadPrevExp (default=False):
    Select whether to automatically reload a previously opened experiment at start-up.

unclutteredNamespace:
    If this option is selected, the scripts will use more complex code, but the advantage is that there is less of a chance that name conflicts will arise.

componentsFolders:
    A list of folder path names that can hold additional custom components for the Builder view; expects a comma-separated list.

hiddenComponents:
    A list of components to hide (e.g., because you never use them)

unpackedDemosDir:
    Location of Builder demos on this computer (after unpacking).

savedDataFolder:
    Name of the folder where subject data should be saved (relative to the script location).

flowAtTop:
    If selected, the “Flow” section will be shown topmost and the “Components” section will be on the left. Restart PsychoPy to activate this option.

showReadme:
    If selected, PsychoPy always shows the Readme file if you open an experiment. The Readme file needs to be located in the same folder as the experiment file.

maxFavorites:
    Upper limit on how many components can be in the Favorites menu of the Components panel.


.. _coderSettings:

Coder settings
---------------------------
codeFont:
    A list of font names to be used for code display. The first found on the system will be used.

commentFont:
    A list of font names to be used for comments sections. The first found on the system will be used

outputFont:
    A list of font names to be used in the output panel. The first found on the system will be used.

fontSize (in pts):
    an integer between 6 and 24 that specifies the size of fonts

codeFontSize (in pts, default=12):
    An integer between 6 and 24 that specifies the font size for code display.

outputFontSize (in pts, default=12):
    An integer between 6 and 24 that specifies the font size for output display.

showSourceAsst:
    Do you want to show the source assistant panel (to the right of the Coder view)? On Windows this provides help about the current function if it can be found. On OS X the source assistant is of limited use and is disabled by default.

showOutput:
    Show the output panel in the Coder view. If shown all python output from the session will be output to this panel. Otherwise it will be directed to the original location (typically the terminal window that called PsychoPy application to open).

reloadPrevFiles:
    Should PsychoPy fetch the files that you previously had open when it launches?

preferredShell:
    Specify which shell should be used for the coder shell window.

newlineConvention:
    Specify which character sequence should be used to encode newlines in code files: unix = \n (line feed only), dos = \r\n (carriage return plus line feed). 


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
	    When the window is created, should the frame of the window and the mouse pointer be visible. If set to False then both will be hidden.

paths:
    Paths for additional Python packages can be specified. See more information :ref:`here<addModules>`.

audioLib:
    As explained in the :doc:`Sound</api/sound>` documentation, currently two sound libraries are available, pygame and pyo.

audioDriver:
    Also, different audio drivers are available.

audioFlac:
    Set flac audio compression.

parallelPorts:
    This list determines the addresses available in the drop-down menu for the :doc:`/builder/components/parallelout`.


.. _connectionSettings:

Connection settings
---------------------------

proxy:
    The proxy server used to connect to the internet if needed. Must be of the form ``http://111.222.333.444:5555``

autoProxy:
    PsychoPy should try to deduce the proxy automatically. If this is True and autoProxy is successful, then the above field should contain a valid proxy address.

allowUsageStats:
    Allow PsychoPy to ping a website at when the application starts up. Please leave this set to True. The info sent is simply a string that gives the date, PsychoPy version and platform info. There is no cost to you: no data is sent that could identify you and PsychoPy will not be delayed in starting as a result. The aim is simple: if we can show that lots of people are using PsychoPy there is a greater chance of it being improved faster in the future.

checkForUpdates:
    PsychoPy can (hopefully) automatically fetch and install updates. This will only work for minor updates and is still in a very experimental state (as of v1.51.00).

timeout:
    Maximum time in seconds to wait for a connection response.


.. _keyBindings:

Key bindings
------------------
There are many shortcut keys that you can use in PsychoPy. For instance did you realise that you can indent or outdent a block of code with Ctrl-[ and Ctrl-] ?