Preferences
====================================

The Preferences dialog allows to adjust general settings for different parts of |PsychoPy|. The preferences settings are saved in the configuration file :ref:`userPrefs.cfg<cleanPrefs>`. The labels in brackets for the different options below represent the abbreviations used in the *userPrefs.cfg* file.

In rare cases, you might want to adjust the preferences on a per-experiment basis. See the API reference for the :doc:`Preferences class here </api/preferences>`.

.. _generalSettings:

General settings (General)
--------------------------
window type (winType) :
    |PsychoPy| can use one of two 'backends' for creating windows and drawing; pygame, pyglet and glfw. Here you can set the default backend to be used.

units (units) :
    Default units for windows and visual stimuli ('deg', 'norm', 'cm', 'pix'). See :ref:`units`.  Can be overridden by individual experiments.

full-screen (fullscr) :
    Should windows be created full screen by default? Can be overridden by individual experiments.

allow GUI (allowGUI) :
	    When the window is created, should the frame of the window and the mouse pointer be visible. If set to False then both will be hidden.

paths (paths) :
    Paths for additional Python packages can be specified. See more :ref:`information on paths here <addModules>`.

flac audio compression (flac) :
    Set flac audio compression.

parallel ports (parallelPorts) :
    This list determines the addresses available in the drop-down menu for the :doc:`/builder/components/parallelout`.

.. _applicationSettings:

Application settings (App)
---------------------------
These settings are common to all components of the application (Coder and Builder etc)

show start-up tips (showStartupTips) :
    Display tips when starting |PsychoPy|.

large icons (largeIcons) :
    Do you want large icons (on some versions of wx on macOS this has no effect)?

default view (defaultView) :
    Determines which view(s) open when the |PsychoPy| app starts up. Default is ‘last’, which fetches the same views as were open when |PsychoPy| last closed.

reset preferences (resetPrefs) :
    Reset preferences to defaults on next restart of |PsychoPy|.

auto-save prefs (autoSavePrefs) :
    Save any unsaved preferences before closing the window.

debug mode (debugMode) :
    Enable features for debugging |PsychoPy| itself, including unit-tests.

locale (locale) :
    Language to use in menus etc.; not all translations are available. Select a value, then restart the app. Think about :doc:`adding translations for your language</developers/localization>`.


.. _builderSettings:

Builder settings (Builder)
---------------------------
reload previous exp (reloadPrevExp) :
    Select whether to automatically reload a previously opened experiment at start-up.

uncluttered namespace (unclutteredNamespace) :
    If this option is selected, the scripts will use more complex code, but the advantage is that there is less of a chance that name conflicts will arise.

components folders (componentsFolders) :
    A list of folder path names that can hold additional custom components for the Builder view; expects a comma-separated list.

hidden components (hiddenComponents) :
    A list of components to hide (e.g., because you never use them)

unpacked demos dir (unpackedDemosDir) :
    Location of Builder demos on this computer (after unpacking).

saved data folder (savedDataFolder) :
    Name of the folder where subject data should be saved (relative to the script location).

Flow at top (topFlow) :
    If selected, the “Flow” section will be shown topmost and the “Components” section will be on the left. Restart |PsychoPy| to activate this option.

always show readme (alwaysShowReadme) :
    If selected, |PsychoPy| always shows the Readme file if you open an experiment. The Readme file needs to be located in the same folder as the experiment file.

max favorites (maxFavorites) :
    Upper limit on how many components can be in the Favorites menu of the Components panel.


.. _coderSettings:

Coder settings (Coder)
---------------------------
code font (codeFont) :
    A list of font names to be used for code display. The first found on the system will be used.

comment font (commentFont) :
    A list of font names to be used for comments sections. The first found on the system will be used

output font (outputFont) :
    A list of font names to be used in the output panel. The first found on the system will be used.

code font size (codeFontSize) :
    An integer between 6 and 24 that specifies the font size for code display in points.

output font size (outputFontSize) :
    An integer between 6 and 24 that specifies the font size for output display in points.

show source asst (showSourceAsst) :
    Do you want to show the source assistant panel (to the right of the Coder view)? On Windows this provides help about the current function if it can be found. On macOS the source assistant is of limited use and is disabled by default.

show output (showOutput) :
    Show the output panel in the Coder view. If shown all python output from the session will be output to this panel. Otherwise it will be directed to the original location (typically the terminal window that called |PsychoPy| application to open).

reload previous files (reloadPrevFiles) :
    Should |PsychoPy| fetch the files that you previously had open when it launches?

preferred shell (preferredShell) :
    Specify which shell should be used for the coder shell window.

newline convention (newlineConvention) :
    Specify which character sequence should be used to encode newlines in code files: unix = \n (line feed only), dos = \r\n (carriage return plus line feed). 


.. _connectionSettings:

Connection settings (Connections)
---------------------------------

proxy (proxy) :
    The proxy server used to connect to the internet if needed. Must be of the form \http://111.222.333.444:5555

auto-proxy (autoProxy) :
    |PsychoPy| should try to deduce the proxy automatically. If this is True and autoProxy is successful, then the above field should contain a valid proxy address.

allow usage stats (allowUsageStats) :
    Allow |PsychoPy| to ping a website at when the application starts up. Please leave this set to True. The info sent is simply a string that gives the date, |PsychoPy| version and platform info. There is no cost to you: no data is sent that could identify you and |PsychoPy| will not be delayed in starting as a result. The aim is simple: if we can show that lots of people are using |PsychoPy| there is a greater chance of it being improved faster in the future.

check for updates (checkForUpdates) :
    |PsychoPy| can (hopefully) automatically fetch and install updates. This will only work for minor updates and is still in a very experimental state (as of v1.51.00).

timeout (timeout) :
    Maximum time in seconds to wait for a connection response.


.. _hardwareSettings:

Hardware settings
---------------------

audioLib :
    Select your choice of audio library with a list of names specifying the order they should be tried.
    We recommend `['PTB', 'sounddevice', 'pyo', 'pygame']` for lowest latency.

audioLatencyMode : 0, 1, 2, 3 (default), 4
    Latency mode for PsychToolbox audio. See :ref:`PTB_latency_modes`.

audioDriver : 'portaudio'
    Some of PsychoPy's audio engines provide the option not to use portaudio but go directly to another lib (e.g. to coreaudio) but some don't allow that.

audioDevice :
    The name of the audio driver to use.

parallelPorts :
    A list of parallel ports. The default is ``['0x0378', '0x03BC']``.

qmixConfiguration :
    The name of the Qmix pump configuration to use. The default is ``'qmix_config'``.

.. _keyBindings:

Key bindings
------------------
There are many shortcut keys that you can use in |PsychoPy|. For instance did you realise that you can indent or outdent a block of code with Ctrl-[ and Ctrl-] ?
