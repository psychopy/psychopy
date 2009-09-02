Changelog
====================

.. note:: Version numbers
  In general, when a new feature is added the first or the second number is incremented (e.g. 1.00.05 -> 1.01.00). Those releases might break previous code you've written because new features often need slight changes to other things. 
  Changes to the final digit (1.00.05 -> 1.00.06) implies a bug-fixing release or very minor new features that shouldn't require code changes form the user.

PsychoPy 1.50
------------------------------

PsychoPy 1.50.00
~~~~~~~~~~~~~~~~~~~~~~
* ADDED A preview of the new application structure and GUI
* ADDED performance enhancements (OS X now blocks on vblank, all platforms rush() if user has permissions)
* ADDED config files. These are already used by the app, but not the library.
* ADDED data.getDateStr() for convenience
* FIXED bug on certain intel gfx cards (shaders now require float extension as well as opengl2.0) 
* FIXED bug scaling pygame text (which caused pygame TextStims not to appear)
* BACKWARDS NONCOMPAT: monitors is moved to be a subpackage of psychopy
* BACKWARDS NONCOMPAT: added 'all_mean' (and similar) data types to TrialHandler.saveAsText and these are now default
* ADDED TrialType object to data (extends traditional dicts so that trial.SF can be used as well as trial['SF'])
* converted docs/website to sphinx rather than wiki (contained in svn)
* FIXED bug with MovieStim not displaying correctly after SimpleImageStim
* FIXED incorrect wx sizing of app(IDE) under OS X on opening
* CHANGED license to GPL (more restrictive, preventing proprietary use)
* CHANGED gui dialogs are centered on screen rather than wx default position
* new dependency on lxml (for saving/loading builder files)

PsychoPy 1.00
------------------------------

PsychoPy 1.00.04
~~~~~~~~~~~~~~~~~~~~~~
* DotStim can have fieldShape of 'sqr', 'square' or 'circle' (the first two are equiv)
* CHANGED intepreters in all .py scripts to be the same (#!/usr/bin/env python). Use PATH env variable to choose non-default python version for your Python scripts
* CHANGED pyglet textures to use numpy->ctypes rather than numpy->string
* FIXED systemInfo assigned on Linux systems

PsychoPy 1.00.03
~~~~~~~~~~~~~~~~~~~~~~
* FIXED initialisation bug with SimpleImageStimulus
* FIXED "useShaders" buglet for TextStim
* CHANGED IDE on win32 to run scripts as processes rather than imports (gives better error messages)
* ADDED mipmap support for textures (better antialiasing for down-scaling)
* CHANGED win32 standalone to include the whole raw python rather than using py2exe

PsychoPy 1.00.02
~~~~~~~~~~~~~~~~~~~~~~
* ADDED SimpleImageStimulus for simple blitting of raw, unscaled images
* ADDED collection of anonymous usage stats (e.g.: OSX_10.5.6_i386 1.00.02 2009-04-27_17:26 )
* RENAMED DotStim.setDirection to setDir for consistency (the attribute is dir not direction)
* FIXED bug with DotStim updating for 'walk' and 'position' noise dots (thanks Alex Holcombe)
* FIXED bug with DotStim when fieldSize was initialised with a list rather than an array
* FIXED buglet using event.getKeys in pygame (nothing fetched if pyglet installed)
* CHANGED image loading code to check whether the image is a file, rather than using try..except
* FIXED buglet raising trivial error messages on closing final window in IDE  
* FIXED problem pasting into find dlg in IDE

PsychoPy 1.00.01
~~~~~~~~~~~~~~~~~~~~~~
* FIXED buglet in windows standalone installer

PsychoPy 1.00.00
~~~~~~~~~~~~~~~~~~~~~~
* ADDED ShapeStim, for drawing geometric stimuli (see demos/shapes.py and new clockface.py)
* ADDED support for the tristate ctrl bit on parallel ports (thanks Gary Strangman for the patch)
* ADDED standalone installer support for windows (XP, vista?)
* FIXED minor bug in Window.flip() with frame recording on (average -> numpy.average)
* FIXED minor bug in sound, now forcing pygame.mixer to use numpy (thanks Konstantin for the patch)
* FIXED visual stimulus positions forced to be floats on init (thanks C Luhmann)

~~~~~~~~~~~~~~~~~~~~~~

PsychoPy 0.97:
------------------------------

PsychoPy 0.97.01:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED bug with IDE not closing properly (when current file was not right-most)
* ADDED parallel.readPin(pinN) so that parallel port can be used for input as well as output
* FIXED bug in parallel.setPortAddress(addr) 
* ADDED check for floats as arguments to ElementArrayStim set___ methods 
* CHANGED: frame time recording to be *off* by default (for plotting, for Window.fps() and for warnings). To turn it on use Window.setRecordFrameIntervals(True), preferably after first few frames have elapsed
* IMPROVED detection of the (truly) dropped frames using log.console.setLevel(log.WARNING)
* FIXED bug that was preventing bits++ from detecting LUT on the Mac (ensure screen gamma is 1.0 first)
* FIXED buglet with .setRGB on stimuli - that method should require an operation argument (def=None)
* ADDED fieldDepth and depths (for elements, releative to fieldDepth) as separate arguments to the ElementArrayStim

PsychoP 0.97.00:
~~~~~~~~~~~~~~~~~~~~~~
* ADDED options to DotStim motions. Two args have been added:
  * signalDots can be 'different' from or 'same' as the noise dots (from frame to frame)
  * noiseDots determines the update rule for the distractor dots (random 'position', 'walk', 'direction')
  * dotLife now works (was previously just a placeholder). Default is -1 (so should be same as before)
  see Scase, Braddick & Raymond (1996) for further info on the importance of these
* ADDED options to event.getKeys
  * keyList to limit which keys are checked for (thanks Gary Strangman)
  * timeStamped=False/True/Clock (thanks Dave Britton)
* CHANGED pyglet key checking now returns '1' as the key irrespective of numpad or otherwise (used to return '1' or 'NUM_1')
* FIXED bug in event.py for machines where pyglet is failing to import
* REMOVED AlphaStim (after a long period of 'deprecated')

----------

PsychoPy 0.96:
------------------------------

PsychoPy 0.96.02:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED bug introduced with clipping of text in 0.96.01 using textstimuli with shaders  under pygame
* FIXED bug with rendering png alpha layer using pyglet shaders

PsychoPy 0.96.01:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED problem with write errors running demos from Mac IDE
* ADDED frameWidth to textStim for multiline
* ADDED setRecordFrameIntervals, saveFrameTimes() to Window and misc.plotFrameIntervals()
* FIXED had accidentally made pygame a full dependency in visual.py
* FIXED MovieStim was being affected by texture color of other stimuli
* FIXED window now explicitly checks for GL_ARB_texture_float before using shaders

PsychoPy 0.96.00:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED pygame back-end so that can be used as a valid alternative to pyglet (requires pygame1.8+ and PyOpenGL3.0+, both included in mac app)
* CHANGED default sound handler to be pygame again. Although pyglet looked promising for this
  it has turned out to be buggy. Timing of sounds can be very irregular and sometimes they don't even play
  Although pygame has longer overall latencies (20-30ms) it's behaviour is at least robust. This will be 
  revisited one day when i have time to write driver-specific code for sounds
* FIXED image importing - scaling from square image wasn't working and CMYK images weren't imported
  properly. Both are now fine.
  
----------


PsychoPy 0.95:
------------------------------

PsychoPy 0.95.11:
~~~~~~~~~~~~~~~~~~~~~~
* ADDED sound.Sound.getDuration() method
* FIXED spurious (unimportant but ugly) error messages raised by certain threads on core.quit()

PsychoPy 0.95.9:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED further bug in sound.Sound on win32 (caused by thread being polled too frequently)
* FIXED new bug in notebook view (introduced in 0.95.8)

PsychoPy 0.95.8:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED bug in sound.Sound not repeating when play() is called repeatedly
* IDE uses improved notebook view for code pages
* IDE line number column is larger
* IDE SaveAs no longer raises (inconsequential) error
* IDE Cmd-S or Ctrl-S now clears autocomplete
    
PsychoPy 0.95.7:
~~~~~~~~~~~~~~~~~~~~~~
* ADDED misc.cart2pol()
* ADDED highly optimised ElementArrayStim, suitable for drawing large numbers of elements. Requires fast OpenGL 2.0 gfx card - at least an nVidia 8000 series or ATI HD 2600 are recommended.
* FIXED bug in calibTools with MonitorFolder (should have been monitorFolder)
* FIXED bug in Sound.stop() for pyglet contexts
* FIXED bug in running scripts with spaces in the filename/path (Mac OS X)

PsychoPy 0.95.6:
~~~~~~~~~~~~~~~~~~~~~~
* DISABLED the setting of gamma if this is [1,1,1] (allows the user to set it from a control panel and not have this adjusted)
* FIXED gamma setting on linux (thanks to Luca Citi for testing)
* FIXED bug in TextStim.setRGB (wasn't setting properly after text had been created)
* FIXED bug searching for shaders on ATI graphics cards
* FIXED - now no need to download avbin for the mac IDE installation

PsychoPy 0.95.5:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED bug in event.clearEvents() implementation in pyglet (wasn't clearing)
* FIXED - psychopy no longer disables ipython shortcut keys
* FIXED bug in sound.Sound initialisation without pygame installeds
* ADDED core.rush() for increasing thread priority on win32
* ADDED Window._haveShaders, XXXStim._useShaders and XXXStim.setUseShaders
* FIXED crashes on win32, running a pyglet context after a DlgFromDict
* ADDED gamma correction for pyglet contexts (not tested yet on linux)

PsychoPy 0.95.4:
~~~~~~~~~~~~~~~~~~~~~~
* CHANGED PsychoPy options (IDE and monitors) now stored the following, rather than with the app. (monitor calib files will be moved here if possible)
    * ~/.PsychoPy/IDE (OS X, linux)
    * <Docs and Settings>/<user>/Application Data/PsychoPy
* FIXED bug in text rendering (ATI/win32/pyglet combo only)
* FIXED minor bug in handling of images with alpha channel

PsychoPy 0.95.3:
~~~~~~~~~~~~~~~~~~~~~~
* ADDED a .clearTextures() method to PatchStim and RadialStim, which should be called before de-referencing a stimulus
* CHANGED input range for numpy array textures to -1:1
* ADDED sysInfo.py to demos

PsychoPy 0.95.2:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED quitting PsychoPyIDE now correctly cancels when saving files

PsychoPy 0.95.1:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED problem with saving files from the IDE on Mac
* FIXED Cmd-C now copies from the output window of IDE
* even nicer IDE icons (thanks to the Crystal project at everaldo.com)
* FIXED bug in the shaders code under pyglet (was working fine in pygame already)
* (refactored code to use a template visual stimulus)

PsychoPy 0.95.0:
~~~~~~~~~~~~~~~~~~~~~~
* FIXED linux bug preventing repeated dialogs (thanks Luca Citi)
* REWRITTEN stimuli to use _BaseClass, defining ._set() method
* MAJOR IMPROVEMENTS to IDE:
  * Intel mac version available as app bundle, including python
  * FIXED double help menu 
  * cleaned code for fetching icons
  * fixed code for updating SourceAssistant (now runs from .OnIdle())

Older
----------------------

PsychoPy 0.94.0:
~~~~~~~~~~~~~~~~~~~~~~
* pyglet:
  * can use multiple windows and multiple screens (see screensAndWindows demo)
  * sounds are buffered faster and more precisely (16ms with <0.1ms variability on my system)
  * creating sounds in pyglet starts a separate thread. If you use sounds in your script you must call core.quit() when you're done to exit the system (or this background thread will continue).
  * pyglet window.setGamma and setGammaRamp working on win and mac (NOT LINUX)
  * pyglet event.Mouse complete (and supports wheel as well as buttons)
  * pyglet is now the default context. pygame will be used if explicitly called or if pyglet (v1.1+) isn't found
  * pyglet can now get/save movie frames (like pygame)
  * TextStims are much cleaner (and a bit bigger?) Can use multiple lines too. New method for specifying font 
* added simpler parallel.py (wraps _parallel which will remain for now)
* removed the C code extensions in favour of ctypes (so compiler no longer necessary)
* converted "is" for "==" where appropriate (thanks Luca)
* Window.getMovieFrame now takes a buffer argument ('front' or 'back')
* monitor calibration files now stored in HOME/.psychopy/monitors rather than site-packages
* Window.flip() added and supports the option not to clear previous buffer (for incremental drawing). Window.update() is still available for now but can be replaced with flip() commands 
* updated demos

PsychoPy 0.93.6:
~~~~~~~~~~~~~~~~~~~~~~
* bug fixes for OS X 10.5 and ctypes OpenGL
* new improved OS X installer for dependencies
* moved to egg for OS X distribution

PsychoPy 0.93.5:
~~~~~~~~~~~~~~~~~~~~~~

* added rich text ctrl to IDE output, including links to lines of errors
* IDE now only opens one copy of a given text file
* improved (chances of) sync-to-vertical blank on windows without adjusting driver settings (on windows it's still better to set driver to force sync to be safe!)
* added center and radius arguments to filters.makeMask and filters.makeRadialMatrix
* implemented pyglet backend for;
    * better screen handling (can specify which screen a window should appear in)
    * fewer dependencies (takes care of pygame and opengl)
    * faster sound production
    * TextStims can be multi-line
    * NO GAMMA-SETTING as yet. Don't use this backend if you need a gamma-corrected window and aren't using Bits++.
* changed the behaviour of Window winTypes
    If you leave winType as None PsychoPy tries to use Pygame, Pyglet, GLUT in that order 
    (when Pyglet can handle gamma funcs it will become default). Can be overridden by specifying winType.
* turned off depth testing for drawing of text (will simply be overlaid in the order called) 
* changes to TextStim: pyglet fonts are loaded by name only, not filename. PsychoPy TextStim now has an additional argument called 'fontFiles=[]' to allow the adding of custom ttf fonts, but the font name should be used as the font=" " argument.    
* updated some of the Reference docs

PsychoPy 0.93.3:
~~~~~~~~~~~~~~~~~~~~~~
* fixed problem with 'dynamic loading of multitextureARB' (only found on certain graphics cards)

PsychoPy 0.93.2:
~~~~~~~~~~~~~~~~~~~~~~
* improved detection of non-OpenGL2.0 drivers

PsychoPy 0.93.1:
~~~~~~~~~~~~~~~~~~~~~~
* now automatically uses shaders only if available (older machines can use this version but will not benefit from the speed up)
* slight speed improvement for TextStim rendering (on all machines)

PsychoPy 0.93.0:
~~~~~~~~~~~~~~~~~~~~~~
* new requirement of PyOpenGL3.0+ (and a graphics card with OpenGL2.0 drivers?)
* much faster implementation of setRGB, setContrast and setOpacity (using fragment shaders)
* images (and other textures) need not be square. They will be automatically resampled if they arent. Square power-of-two image textures are still recommended
* Fixed problem in calibTools.DACrange caused by change in numpy rounding behaviour. (symptom was strange choice of lum values for calibrations)
* numpy arrays as textures currently need to be NxM intensity arrays
* multitexturing now handled by OpenGL2.0 rather than ARB
* added support for Cedrus response pad
* if any component of rgb*contrast>1 then the stimulus will be drawn as low contrast and b/y (rgb=[0.2,0.2,-0.2]) in an attempt to alert the user that this is out of range

PsychoPy 0.92.5:
~~~~~~~~~~~~~~~~~~~~~~
* Fixed issue with stairhandler (it was terminating based only on the nTrials). It does now terminate when both the nTrials and the nReversals [or length(stepSizes) if this is greater] are exceeded.
* Minor enhancements to IDE (added explicit handlers to menus for Ctrl-Z, Ctrl-Y, Ctrl-D)

PsychoPy 0.92.4:
~~~~~~~~~~~~~~~~~~~~~~
* fixed some source packaging problems for linux (removed trademark symbols from serialposix.py and fixed directory capitalisation of IDE/Resources in setup.py). Thanks to Jason Locklin and Samuele Carcagno for picking them up.
* numerous minor improvements to the IDE
* reduced the buffer size of sound stream to reduce latency of sound play
* fixed error installing start menu links (win32)

PsychoPy 0.92.3:
~~~~~~~~~~~~~~~~~~~~~~
* new source .zip package (switched away from the use of setuptools - it didn't include files properly in a source dist)
* Fixed problem on very fast computers that meant error messages weren't always displayed in the IDE

PsychoPy 0.92.2:
~~~~~~~~~~~~~~~~~~~~~~
* have been trying (and failing) to make scripts run faster from the IDE under Mac OS X. Have tried using threads and debug modules (which would mean you didn't need to import all the libs every time). All these work fine under win32 but not under OS X every time :-( If anyone has a new idea for how to run a pygame window in the same process as the IDE thread I'd love hear it
* removed the messages from the new TextStim stimuli 
* fixed bug in IDE that caused it to crash before starting if pythonw.exe was run rather than python.exe on first run(!)
* improvements to the source assistant window (better help and now fetches function arguments)

Known Problems:
* The IDE isn't collecting all errors that are returned - a problem with the process redirection mechanism? FIXED in 0.92.3

PsychoPy 0.92.1
~~~~~~~~~~~~~~~~~~~~~~
* fixed minor bug in IDE - wouldn't open if it had been closed with no open docs.
* fixed problem with pushing/popping matrix that caused the stimuli to disappear (only if a TextStim was rendered repeatedly)

PsychoPy 0.92.0:
~~~~~~~~~~~~~~~~~~~~~~
* 'sequential' ordering now implemented for data.TrialHandler (thx Ben Webb)
* moved to pygame fonts (with unicode support and any TT font onthe system). The switch will break any code that was using TextStim with lineWidth or letterWidth as args. Users wanting to continue using the previous TextStim can call textStimGLUT instead (although I think the new pygame fonts are superior in every way).
* improved IDE handling of previous size (to cope with being closed in the maximised or minimised state, which previously caused the window not to return)
  
PsychoPy 0.91.5:
~~~~~~~~~~~~~~~~~~~~~~
* fixed minor bug in using numpy.array as a mask (was only working if array was 128x128)
* faster startup for IDE (added threading class for importing modules)
* fixed very minor bug in IDE when searching for attributes that dont exist
* fixed minor bug where scripts with syntax errors didn't run but didn't complain either
* IDE FileOpen now tries the folder that the current file is in first
* IDE removed threading class for running scripts

PsychoPy 0.91.4
~~~~~~~~~~~~~~~~~~~~~~
* fixed the problem of stimulus order/depth. Now the default depth is set (more intuitively) by the order of drawing not creating.
* IDE added recent files to file menu
* IDE minor bug fixes
* IDE rewrite of code inspection using wx.py.instrospect

PsychoPy 0.91.3
~~~~~~~~~~~~~~~~~~~~~~
* added find dialog to IDE
* added ability of data.FunctionFromStaircase to create unique bins rather than averaging several x values. Give bins='unique' (rather than bins=someInteger). Also fixed very minor issue where this func would only take a list of lists, rather than a single list. 

PsychoPy 0.91.2
~~~~~~~~~~~~~~~~~~~~~~
* fixed IDE problem running filenames containing spaces (only necessary on win32)

PsychoPy 0.91.1
~~~~~~~~~~~~~~~~~~~~~~
* added reasonable SourceAssistant to IDE
* added a stop button to abort scripts in IDE
* IDE scripts now run as sub process rather than within the main process: slower but safer
* added an autoflushing stdout to psychopy.__init__. Where lots of text is written to stdout this may be a problem, but turing it off means that stdout doesn't get properly picked up by the IDE :-(

PsychoPy 0.91.0
~~~~~~~~~~~~~~~~~~~~~~
* PsychoPy now has its own IDE!! With syntax-highlighting, code-folding and auto-complete!! :-)
* gui.py had to be refactored a little but (I think) should not be noticed by the end user (gui.Dlg is now a subclass of wx.Dialog rather than a modified instance)
* gui.Dlg and DlgFromDict now end up with an attribute .OK that is either True or False 
* fixed bug in data.StairHandler that could result in too many trials being run (since v0.89)

PsychoPy 0.90.4
~~~~~~~~~~~~~~~~~~~~~~
* resolved deprecation warning with wxPython (now using "import wx")

PsychoPy 0.90.3
~~~~~~~~~~~~~~~~~~~~~~
* used the new numpy.mgrid commands throughout filters and visual modules
* sorted out the rounding probs on RadialStim
* fixed import bug in calibtools.py

PsychoPy 0.90.2
~~~~~~~~~~~~~~~~~~~~~~
* fixed new bug in the minVal/maxVal handling of StairHandler (where these have not been specified)
* changed the default console log level to be ERROR, due to too much log output! 

PsychoPy 0.90.1
~~~~~~~~~~~~~~~~~~~~~~
* fixed new bug in Sound object
* changed the default log file to go to the script directory rather than site-packages/psychopy

PsychoPy 0.90
~~~~~~~~~~~~~~~~~~~~~~
* sounds now in stereo and a new function to allow you to choose the settings for the sound system.
* LMS colours (cone-isolating stimuli) are now tested and accurate (when calibrated)
* added logging module (erros, warnings, info). And removed other messages:
     * @Verbose@ flags have become log.info messages
     * @Warn@ commands have become log.warning messages
* added minVal and maxVal arguments to data.StairHandler so that range can be bounded
* @import psychopy@ no longer imports anything other than core

Psychopy 0.89.1
~~~~~~~~~~~~~~~~~~~~~~
* fixed bug in new numpy's handling of bits++ header

Psychopy 0.89
~~~~~~~~~~~~~~~~~~~~~~
* optimised DotStim to use vertex arrays (can now draw several thousand dots)
* optimised RadialStim to use vertex arrays (can increase radial resolution without much loss)

Psychopy 0.88
~~~~~~~~~~~~~~~~~~~~~~
* fixed problem with MonitorCenter on OSX (buttons not working on recent version of wxPython)

Psychopy 0.87
~~~~~~~~~~~~~~~~~~~~~~
* added sqrXsqr to RadialStim and made it default texture
* fixed a minor bug in RadialStim rendering (stimuli failed to appear under certain stimulus orderings)
* changed RadialStim size parameter to be diameter rather than radius (to be like AlphaStim)
* namechange: introduced PatchStim (currently identical to AlphaStim which may one day become deprecated)

Psychopy 0.86
~~~~~~~~~~~~~~~~~~~~~~
* distributed as an .egg

Psychopy 0.85
~~~~~~~~~~~~~~~~~~~~~~
* upgraded for numpy1.0b and scipy0.50. Hopefully those packages are now stable enough that they won't need further PsychoPy compatibility changes

Psychopy 0.84
~~~~~~~~~~~~~~~~~~~~~~
* NEW (alpha) support for radial patterns rather than linear ones
* changed Clock behaviour to use time.clock() on win32 rather than time.time()
* fixed a bug in the shuffle seeding behaviour
* added a noise pattern to bacground in monitor calibration

Psychopy 0.83
~~~~~~~~~~~~~~~~~~~~~~
* NEW post-install script for Win32 installs shortcuts to your >>Start>Programs menu
* NEW parallel port code (temporary form) using DLportIO.dll can be found under _parallel
* NEW hardware module with support for fORP response box (for MRI) using serial port
* added iterator functionality to data.TrialHandler and data.StairHandler you can now use ::
    for thisTrial in allTrials:
    
but a consequence was that .nextTrial() will be deprecated in favour of .next(). 
Also, when the end of the trials is reached a StopIteration is raised.
* added the ability to seed the shuffle mechanism (and trial handler) so you can repeat experiments with the same trial sequence

Psychopy 0.82
~~~~~~~~~~~~~~~~~~~~~~
* rewritten code for bits++ LUT drawing, raised by changes in pyOpenGL(2.0.1.09) call to drawpixels
* minor change to exit behaviour. pyGame.quit() is now called and then sys.exit(0) rather than sys.exit(1)
* bug fixes in type handling (from Numeric to numpy)

Psychopy 0.81
~~~~~~~~~~~~~~~~~~~~~~
* changes to gui caused by new threading behaviour of wxPython and PyGame (DlgFromDict must now be a class not a function).

Psychopy 0.80
~~~~~~~~~~~~~~~~~~~~~~
* switching numeric code to new python24 and new scipy/numpy. MUCH nicer
* new (reduced requirements):
  * numpy 0.9 or newer (the replacement for Numeric/numarray)
  * numpy 0.4.4 or newer
  * pyOpenGL
  * pygame
  * PIL
  * matplotlib (for data plotting)

PsychoPy 0.72
~~~~~~~~~~~~~~~~~~~~~~
* tested (and fixed) compatibility with wxPython 2.6. Will now be using this as my primary handler for GUIs
* ADDED ability to quit during run of getLumSeries

PsychoPy 0.71
~~~~~~~~~~~~~~~~~~~~~~
* FIXED filename bug in makeMovies.makeAnimatedGIF
* slight change to monitors that it uses testMonitor.calib as a default rather than default.calib (testMonitor.calib is packaged with the installation)

PsychoPy 0.70
~~~~~~~~~~~~~~~~~~~~~~
* FIXED bug in setSize. Wasn't updating correctly
* ADDED ability to append to a data file rather than create new
* bits.lib (from CRS) is now distributed directly with psychopy rather than needing separate install)
* ADDED db/log/linear step methods to StairHandler
* ADDED logistic equation to data.FitFunction

PsychoPy 0.69
~~~~~~~~~~~~~~~~~~~~~~
* ADDED a testMonitor to the monitors package so that demos can use it for pseudo*calibrated stimuli.
* REDUCED the attempt to use _bits.pyd. Was only necessary for machines that had bits++ monitor center
* ADDED basic staircase method
* CHANGED dlgFromDict to return None on cancel rather than 0
* CHANGED the description of sin textures so that the centre of the patch had the color of dkl or rgb rather
  than the edge. (Effectively all sin textures are now shifted in phase by pi radians).
  -Demos removed from the main package - now ONLY distributed as a separate library

PsychoPy 0.68
~~~~~~~~~~~~~~~~~~~~~~
* FIXED toFile and fromFile so they work!?
* Demos being distributed as a separate .zip file (may be removed from the main package someday)

PsychoPy 0.67
~~~~~~~~~~~~~~~~~~~~~~
* ADDED toFile, fromFile, pol2cart functions to psychopy.misc
* CHANGED waitKeys to return a list of keys (usually of length one) so that it's compatible with getKeys

PsychoPy 0.66
~~~~~~~~~~~~~~~~~~~~~~
* serial is now a subpackage of psychopy and so doesn't need additional installation
* REMOVED the code to try and query the graphics card about the scr dimensions. From now on, if yo uwish to use real world units, you MUST specify scrWidthPIX and scrWidthCM when you make your visual.Window
* ADDED flag to data output to output matrixOnly (useful for matlab imports)
* REVERTED the default numeric handler to be Numeric rather than numarray (because it looks like numarray hasn't taken off as much as thought)
* FIXED minor bug in text formatting for TrialHandler.saveAsText()
* CHANGED visual.Window so that the monitor argument prefers to receive a Monitor object (rather than just a dictionary) or just the name of one. MonitorCenter makes it so easy to create these now that they should be the default.
* CHANGED Photometer initialisation behaviour - used to raise an error on a fail but now sets an internal attribute .OK to False rather than True

PsychoPy 0.65
~~~~~~~~~~~~~~~~~~~~~~
* MonitorCenter now complete. Plots and checks gamma correction.
* can write movies out to animated gifs(any platform) or mpg/avi (both windows only)

PsychoPy 0.64
~~~~~~~~~~~~~~~~~~~~~~
* ChANGED monitor key dkl_rgb_matrix to dkl_rgb (also for lms)
* ADDED code for PR650 to get the monitor color calibration and calculate the color conversion matrices automatically. Will be implemented via the MonitorCenter application.
* ADDED pyserial2.0 as a subpackage of psychopy so that it needn't be separately installed
* Much improved MonitorCenter with DKL and LMS calibration buttons and matrix output
* Double-click installer for Mac now available

PsychoPy 0.63
~~~~~~~~~~~~~~~~~~~~~~
* ADDED ability to capture frames from the window as images (tif, jpg...) or as animated GIF files :) see demo
* ADDED ability for elements in DotStim to be any arbitrary stimulus with a methods for .setPos(), .draw()

PsychoPy 0.62
~~~~~~~~~~~~~~~~~~~~~~
* FIXED the circular mask for DotStim
* FIXED bug in the new text alignment method (was being aligned but not positioned?!)

PsychoPy 0.61
~~~~~~~~~~~~~~~~~~~~~~
* FIXED minor bug in MonitorCenter (OS X only)

PsychoPy 0.60
~~~~~~~~~~~~~~~~~~~~~~
* ADDED a GUI application for looking after monitors and calibrations. SEE MonitorCenter.py in the new package monitors
* MOVED "psychopy.calib" subpackage to a whole separate package "monitors". Calibration files will now be stored alongside the calibration code. This makes it easier to develop the new calibration GUI application that I'm working on. Also means that if you delete the psychopy folder for a new installation you won't lose your calibration files.
* ADDED optional maxWait argument to event.waitKeys()
* CHANGED TextStim to take the font as a name rather than font number
* ADDED alignment to text stimuli (alignVert, alignHoriz)
* CHANGED waitKeys to implicitly clear keys from the event queue so that it only finds the first keypress after its called. As result it now returns a single character rather than list of them
* CHANGED visual.Window so that it no longer overrides monitor settings if arguments are specified. Easy now to create a monitor in the monitors GUI and use that instead
* ADDED the circular mask for DotStimulus
