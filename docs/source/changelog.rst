Changelog
====================


.. raw:: html

    <style> .blue {color:blue} </style>

.. role:: blue

.. note::
  Version numbers

  In general, when a new feature is added the second number is incremented (e.g. 1.00.05 -> 1.01.00). Those releases might break previous code you've written because new features often need slight changes to other things.
  Changes to the final digit (1.00.05 -> 1.00.06) indicate a bug-fixing release or very minor new features that shouldn't require code changes from the user.

:blue:`Changes in blue typically indicate things that alter the PsychoPy behaviour in a way that could break compatibility. Be especially wary of those!`

PsychoPy 1.75
------------------------------

PsychoPy 1.75.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* IMPROVED: Experiment info dialog box easier to control now from experiment settings (user doesn't need to write a dictionary by hand any more)
* IMPROVED: Components in the Builder are now arranged in categories, including a special 'Favorites' category
* IMPROVED: Code Components now support full syntax highlighting and code folding (but still aren't quite big enough!)
* ADDED: Builder undo/redo now gives info about what is going to be un/redone
* ADDED: Window now supports a `stereo` flag to provide support for quad-buffers (advanced graphics cards only)
* FIXED: bug with copying/pasting Routines that was breaking Flow in certain situations and corrupting the experiment file
* FIXED: fatal typo in QuestHandler code (Gary Lupyan)
* FIXED: data outputs for multiple key/mouse presses
* ADDED: Microphone now supports `stop` to abort recording early (Jeremy Gray)
* ADDED: beginning of error reporting when generating Builder experiments (thanks Piotr Iwaniuk)
* FIXED: csv files now generated from Builder as expected not dlm files (tab-delimited)

PsychoPy 1.74
------------------------------

PsychoPy 1.74.04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* IMPROVED: larger Code Component boxes (and fixed bug with being only one line on linux)
* FIXED: Builder code syntax error when using Mouse set state 'every frame'
* FIXED: Builder was erroneously using 'estimated duration' for constraining non-slip timing
* FIXED: Builder couldn't open Experiment Settings if the expected screen number didn't exist on this system

PsychoPy 1.74.03
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Aug 2012)

* FIXED: the multiline text entry box in the Builder Text Component was broken (thanks Piotr Iwaniuk)
* IMPROVED: serial (RS232) interface to fORP button box to avoid recording repeated presses (thanks Nate Vack). Does not affect use of fORP box from USB interface.

PsychoPy 1.74.02
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Aug 2012)

* FIXED: bug leading to message: `IndexError: string index out of range.` This was caused by problem saving excel files
* FIXED: bug leading to message: `AttributeError: ImageStim instance has no attribute 'rgbPedestal'.` Was only occurring on non-shaders machines using the new ImageStim.
* FIXED: problem loading old ExperimentHandlers that contained MultiStairHandlers
* FIXED: Builder Text Components gave an error if letter height was a variable
* ADDED: Window.flip() now returns the timestamp for the flip if possible (thanks Sol Simpson)
* ADDED: misc.sph2cart (Becky Sharman)
* ADDED: warning when user presents SimpleImageStim that seems to extend beyond screen (James McMurray)

PsychoPy 1.74.01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released July 2012)

* FIXED: the pyo package is now included in the windows Standalone distribution (making audio input available as intended)
* FIXED: error saving excel data from numpy.int formats (Erik Kastman)
* FIXED: error at end of automated gamma calibration (which was causing a crash of the calibration script)
* FIXED: misc.getDateStr() returns numeric date if there's an error with unicode encoding (Jeremy)
* FIXED: added partial support for non-ASCII keyboards (Sebastiaan Mathot)

PsychoPy 1.74.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released July 2012)

Highlights (and compatibility changes):

* :blue:`CHANGED`: Builder experiments saved from this version will NOT open in older versions
* :blue:`ADDED: 'non-slip' timing methods to the Builder interface (improved timing for imaging experiments)` See :ref:`nonSlip` for further info
* :blue:`ADDED: Long-wide data file outputs, which are now the default for all new Builder experiments.` See :ref:`longWide` outputs
* :blue:`CHANGED: The psydat output files from Builder` have also changed. They are now :class:`~psychopy.data.ExperimentHandler` objects, which contain all loops in a single file. Previously they were TrialHandlers, which required one file for each loop of the experiment. Analysis scripts will need slight modifications to handle this
* :blue:`CHANGED: The summarised excel/csv outputs now have an additional column for the order of the stimulus as presented.` This may affect any automated analysis you perform on your spreadsheet outputs
* :blue:`RESTRUCTURED:` the generation of 'summarised' data outputs (text and excel) were also rewritten in this version, so make sure that your data files still contain all the data you were expecting
* ADDED: basic audio capture (and speech recognition via google!). Builder now has a Microphone Component to record inputs, but does not yet use the speech recognition facility. See :ref:`psychopy.microphone <microphone>` library, Coder demo "input/say_rgb.py" and Builder demo "voiceCapture".  (Jeremy)
* ADDED: HSV color space for all stimuli
* :blue:`CHANGED: in Builder the default :class:`~psychopy.visual.DotStim` has signal dots='same' (once a signal dot, always a signal dot).` Only affects new experiments
* :blue:`CHANGED: data.FitCumNormal now uses a slightly different equation that has a slightly different equation`, which alters the interpretation of the parameters (but not the quality of fit). Parameters from this function before version 1.74 cannot to be compared with new values.
* :blue:`CHANGED: pygame is no longer being formally supported/tested` although it will probably continue to work for some time.

Additional changes:

* ADDED: contains() and intersects() methods to visual shape stimuli (including Rect etc) to determine whether a point or array of points is within the present stimulus boundaries
* FIXED: missing parameter name in conditions file is detected, triggers more informative error message
* ADDED: fORP: option asKeys to handle button presses as pyglet keyboard events (when using a serial port); faster getUniqueEvents()
* ADDED: basic file encryption (beta) using RSA + AES-256; see API encryption for usage and caveats
* ADDED: upload a file to a remote server over http (libs: web.upload) with coder demo, php scripts for server (contrib/http/*)
* ADDED: Builder demo (dualRatingScales): show a stim, get two different ratings side by side [unpack the demos again]
* ADDED: rating scale options: 'maxTime' to time-out, 'disappear' to hide after a rating; see new Builder demo
* FIXED: rating scale bug: skipKeys was not handling 'tab' properly (no skip for tab-key, do skip for 't', 'a', or 'b')
* ADDED: new locale pref for explicitly setting locale, used in date format and passed to builder scripts (Jeremy, Hiroku Sogo)
* ADDED: 'enable escape' option in experiment settings, default is 'enabled'
* ADDED: support for :class:`~psychopy.visual.ElementArrayStim` to use the same set of color spaces as other stimuli
* CHANGED: removed python 2.4's version of sha1 digest from :class:`~psychopy.info.RunTimeInfo`
* CHANGED: removed any need for PyOpenGL (pyglet.gl now used throughout even for pygame windows)
* FIXED: Builder was ignoring changes to :class:`~psychopy.visual.DotStim` FieldPos (thanks Mike MacAskill)
* FIXED: Builder Flow is smarter about Loops and now stops you creating 'broken' ones (e.g. Loops around nothing)
* FIXED: MovieStim used from Builder was not working very well. Sounds continued when it was told to stop and the seek(0.0001) line was causing some file formats not to work from Builder only (those that don't support seeking)
* FIXED: Mouse component was not saving clicks in Builder experiments if forceEndOnClick was set to be False
* FIXED: DotStim.setFieldCoherence was having no effect if noise dots were updating by 'position'
* FIXED: TextStim.setColor() was not updating stimulus properly when haveShaders=False
* FIXED: In Builder, sound duration was not being used in creating new sounds
* CHANGED: Under linux, although you will be warned if a new version is available, it will not be auto-installed by PsychoPy (that should be done by your package manager)
* FIXED: csv/dlm data outputs no longer have a trailing delimitter at end of line
* FIXED: all test suite tests should now pass :-)

PsychoPy 1.73
------------------------------

PsychoPy 1.73.06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released April 2012)

* FIXED: xlsx outputs were collapsing raw data from trials with non-response
* FIXED: monitor gamma grids are now returned as arrays rather than lists (Ariel Rokem)
* FIXED: bug with Window.setColor being incorrectly scaled for some spaces
* FIXED: buglet preventing unicode from being used in TrialHandler parameter names (William Hogman) and saving to data files (Becky Sharman)
* FIXED: StairHandler in Builder now saves the expInfo dictionary (Jeremy)
* FIXED: can unpickle from either old-style or new-style data files (using psychopy.compatibility.fromFile()) (Erik Kastman)

PsychoPy 1.73.05
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(Released March 2012)

* FIXED: Joystick error when calling :class:`~psychopy.hardware.joystick.Joystick.getHat()` or :class:`~psychopy.hardware.joystick.Joystick.getHats()` (fixed by Gary Lupyan)
* FIXED: BufferImageStim crashing on some linux boxes (due to bug with checking version of OpenGL) (fixed by Jonas Lindelov)
* FIXED: fMRI emulator class was providing old-format key events (fixed by Erik Kastman and Jeremy)
* FIXED: Win.setRecordFrameIntervals(True) was including the time since it was turned off as a frame interval (fixed by Alex Holcombe)
* FIXED: using forceEndtrial from a mouse component in Builder wasn't working (thanks Esteban for the heads-up)
* FIXED: visual.Circle now respects the edges parameter (fixed by Jonas Lindelov)
* FIXED: having IPython v0.12 should no longer crash psychopy on startup (Jeremy)
* FIXED: non-ascii month-name (eg Japanese) from %B is now filtered out to avoid crash when compile a psyexp script (Jeremy)
* ADDED: support for usb->serial devices under linux (William Hogman)
* ADDED: option to vertically flip a BufferImageStim upon capture (esp for fMRI-related presentation of text) (Jeremy)
* ADDED: option to play a sound (simple tone) during fMRI launchScan simulation (Jeremy)

PsychoPy 1.73.04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Feb 2012)

* :blue:`CHANGED: Builder scripts now silently convert division from integers to float where necessary.` That means 1/3=0.333 whereas previously 1/3=0. This is done simply by adding the line `from __future__ import division` at the top of the script, which people using Coder might want to think about too.
* FIXED: problem with loading .psydat files using misc.fromFile (thanks Becky)
* FIXED: issue on OSX with updating from 1.70 binaries to 1.73 patch release

PsychoPy 1.73.03
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Jan 2012)

* FIXED: problem with loops crashing during save of xlsx/csv files if conditions were empty
* FIXED: bugs in Builder setting Dots coherence and direction parameters
* FIXED: problem with strange text and image rendering on some combinations of ATI graphics on Windows machines

PsychoPy 1.73.02
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Jan 2012)

* ADDED: loop property to :class:`~psychopy.visual.MovieStim` for coder only so far (thanks Ariel Rokem)
* FIXED: buglet requesting import of pyaudio (thanks Britt for noticing and Dan Shub for fixing)
* FIXED: problem with avbin (win32)
* FIXED: problem with unicode characters in filenames preventing startup
* FIXED: bug with 'fullRandom' method of :class:`~psychopy.data.TrialHandler` missing some trials during data save
* FIXED: :func:`Mouse.clickReset()` now resets the click timers
* FIXED(?): problem with avbin.dll not being found under 64-bit windows

PsychoPy 1.73.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Jan 2012)

* :blue:`CHANGED: psychopy.log has moved to psychopy.logging (Alex Holcombe's suggestion). You'll now get a deprecation warning for using psychopy.log but it will still work (for the foreseeable future)`
* ADDED: new hardware.joystick module supporting pyglet and pyjame backbends for windows and OSX. Demo in Not working on Linux yet. See demos>input
* ADDED: support for CRS ColorCAL mkII for gamma calibrations in Monitor Center.
* ADDED: data.ExpHandler to combine data for multiple separate loops in one study, including output of a single wide csv file. See demos>experimental control>experimentHandler. Support from Builder should now be easy to add
* ADDED: ability to fix (seed) the pseudorandom order of trials in Builder random/full-random loops
* ADDED: auto-update (and usage stats) can now detect proxies in proxy.pac files. Also this now runs in a low-priority background thread to prevent any slowing at startup time.
* FIXED: bug when passing variables to Staircase loops in Builder
* FIXED: mouse in Builder now ignores button presses that began before the 'start' of the mouse
* FIXED: can now use pygame or pyaudio instead of pygame for sounds, although it still isn't recommended (thanks Ariel Rokem for patch)

PsychoPy 1.72.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(rc1 released Nov 2011)

* :blue:`CHANGED: gui.Dlg and gui.dlgFromDict can now take a set of choices and will convert to a choice control if this is used (thanks Manuel Ebert)`
    - for gui.Dlg the `.addField()` method now has `choices` attribute
    - for gui.dlgFromDict if one of the values in the dict is a list it will be interpreted as a set of choices (NB this potentially breaks old code)
    - for info see API docs for psychopy.gui

* ADDED: improvements to drawing of shapes (thanks Manuel Ebert for all)
    - ShapeStim now has a size parameter that scales the locations of vertices
    - new classes; Rect, Line, Circle, Polygon

* FIXED: error with DotStim when fieldSize was a tuple and fieldShape was 'sqr' 
* FIXED: calibration plots in Monitor Center now resize and quit as expected
* FIXED: conditions files can now have lists of numbers [0,0]
* FIXED: buglet with flushing mouse events (thanks Sebastiaan Mathot)
* FIXED: Builder components now draw in order, from top to bottom, so lower items obscure higher ones
* FIXED: problem with Patch Component when size was set to be dynamic
* FIXED: problem with Builder loops not being able to change type (e.g. change 'random' into 'staircase')
* FIXED: data from TrialHandler can be output with unicode contents (thanks Henrik Singmann)


PsychoPy 1.71
------------------------------

PsychoPy 1.71.01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Oct 2011)

* CHANGED: the number of stimulus-resized and frames-dropped warnings is now limited to 5 (could become a preference setting?)
* FIXED: Builder now allows images to have size of None (or 'none' or just blank) and reverts to using the native size of the image in the file
* FIXED: occasional glitch with rendering caused by recent removal of depth testing (it was getting turned back on by TextStim.draw())
* FIXED: opening a builder file from coder window (and vice versa) switches view and opens there
* FIXED: problem showing the About... item on OS X Builder view
* FIXED problem with loops not showing up if the conditions file wasn't found
* FIXED: runTimeInfo: better handling of cwd and git-related info
* FIXED: rating scale: single click with multiple rating scales, auto-scale with precision = 1
* IMPROVED: rendering speed on slightly older nVidia cards (e.g. GeForce 6000/7000 series) under win32/linux. ElementArrays now render at full speed. Other cards/systems should be unchanged.
* IMPROVED: rating scale: better handling of default description, scale=None more intuitive
* ADDED: new function getFutureTrial(n=1) to TrialHandler, allowing users to find out what a trial will be without actually going to that trial
* ADDED: misc.createXYs() to help creating a regular grid of xy values for ElementArrayStim

PsychoPy 1.71.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(released Sept 2011)

* :blue:`CHANGED: Depth testing is now disabled. It was already being recommended that depth was controlled purely by drawing order (not depth settings) but this is now the *only* way to do that`
* CHANGED: The Builder representation of the Components onset/offset is now based on 'estimatedStart/Stop' where a value has been given. NB this does not affect the actual onset/offset of Components merely its representation on the timeline.
* ADDED: Builder loop conditions mini-editor: (right-click in the filename box in a loop dialog)
    - create, edit, and save conditions from within PsychoPy; save & load using pickle format
    - preview .csv or .xlsx conditions files (read-only)
* ADDED: RatingScale method to allow user to setMarkerPosition()
* ADDED: Builder dialogs display a '$' to indicate fields that expect code/numeric input
* ADDED: Text Component now has a wrapWidth parameter to control the bounding box of the text
* ADDED: Opacity parameter to visual stimulus components in the Builder, so you can now draw plaids etc from the builder
* FIXED: can edit or delete filename from loop dialog
* FIXED: bug in RunTimeInfo (no longer assumes that the user has git installed)
* FIXED: bug in BufferImageStim
* FIXED: bug in Builder Ratingscale (was always ending routine on response)
* FIXED: problem with nested loops in Builder. Inner loop was not being repeated. Loops are now only created as they are needed in the code, not at the beginning of the script
* FIXED: rendering of many stimuli was not working beyond 1000 elements (fixed by removal of depth testing)
* FIXED: mouse component now using start/duration correctly (broken since 1.70.00)
* FIXED: when changing the texture (image) of a PatchStim, the stimulus now 'remembers' if it had been created with no size/sf set and updates these for the new image (previously the size/sf got set according to the first texture provided)
* FIXED: putting a number into Builder Sound Component does now produce a sound of that frequency
* FIXED: added 'sound','misc','log' to the component names that PsychoPy will refuse. Also a slightly more informative warning when the name is already taken
* FIXED: Opacity parameter was having no effect on TextStim when using shaders
* FIXED bug with MovieStim not starting at beginning of movie unless a new movie was added each routine


PsychoPy 1.70
------------------------------

PsychoPy 1.70.02
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* FIXED: bug in Builder Ratingscale (was always ending routine on response)
* FIXED: problem with nested loops in Builder. Inner loop was not being repeated. Loops are now only created as they are needed in the code, not at the beginning of the script
* FIXED: rendering of many stimuli was not working beyond 1000 stimuli (now limit is 1,000,000)
* FIXED: mouse component now using start/duration correctly (broken since 1.70.00)
* FIXED: when changing the texture (image) of a PatchStim, the stimulus now 'remembers' if it had been created with no size/sf set and updates these for the new image (previously the size/sf got set according to the first texture provided)
* CHANGED: Depth testing is now disabled. It was already being recommended that depth was controlled purely by drawing order (not depth settings) but this is now the *only* way to do that
* CHANGED: The Builder representation of the Components onset/offset is now based on 'estimatedStart/Stop' where a value has been given. NB this does not affect the actual onset/offset of Components merely its representation on the timeline.

PsychoPy 1.70.01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(Released Aug 2011)

* FIXED: buglet with Builder (1.70.00) importing older files not quite right and corrupting the 'allowedKeys' of keyboard component
* FIXED: buglet with SimpleImageStim. On machines with no shaders some images were being presented strangely
* FIXED: buglet with PatchStim. After a call to setSize, SF was scaling with the stimulus (for unit types where that shouldn't happen)

PsychoPy 1.70.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(Released Aug 2011)

*NB This version introduces a number of changes to Builder experiment files that will prevent files from this version being opened by earlier versions of PsychoPy*

* :blue:`CHANGED use of allowedKeys in Keyboard Component.` You used to be able to type `ynq` to get those keys, but this was confusing when you then needed `'space'` or `'left'` etc. Now you must type 'y','n','q', which makes it more obvious how to include 'space','left','right'...
* CHANGED dot algorithm in DotStim. Previously the signalDots=same/different was using the opposite to Scase et al's terminology, now they match. Also the default method for noiseDots was 'position' and this has been changed to 'direction'. The documentation explaining the algorithms has been clarified. (see :ref:`dots`)
* CHANGED `MovieStim.playing` property to be called `MovisStim.status` (in keeping with other stimuli)
* CHANGED names:

    - `data.importTrialTypes` is now `data.importConditions`
    - `forceEndTrial` in Keyboard Component is now `forceEndRoutine`
    - `forceEndTrialOnPress` in Mouse Component is now `forceEndRoutineOnPress`
    - `trialList` and `trialListFile` in Builder are now `conditions` and `conditionsFile`, respectively
    - 'window units' to set Component units is now 'from exp settings' for less confusion

* :blue:`CHANGED numpy imports in Builder scripts:`

    - only a subset of numpy features are now imported by default: numpy: sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray, random, randint, normal, shuffle
    - all items in the numpy namespace are available as np.*
    - if a pre-v1.70 script breaks due to this change, try prepending 'np.' or 'np.random.'

* :blue:`CHANGED: Builder use of $.` $ can now appear anywhere in the field (previously only the start). To display a '$' character now requires '\\$' in a text field (to prevent interpretation of normal text as being code).

* ADDED flexibility for start/stop in Builder Components. Can now specify stimuli according to;

    - variable values (using $ symbol). You can also specify an 'expected' time/duration so that something is still drawn on the timeline
    - number of frames, rather than time (s), for greater precision
    - an arbitrary condition (e.g. otherStim.status==STOPPED )

* ADDED the option to use a raised cosine as a PatchStim mask (thanks Ariel Rokem)
* ADDED a preference setting for adding custom path locations to Standalone PsychoPy
* ADDED Dots Component to Builder interface for random dot kinematograms
* ADDED wide-format data files (saveAsWideText()) (thanks Michael MacAskill)
* ADDED option for full randomization of repeated lists (loop type 'fullRandom') (Jeremy)
* ADDED builder icons can now be small or large (in prefs)
* ADDED checking of conditions files for parameter name conflicts (thanks Jeremy)
* ADDED emulate sync pulses and user key presses for fMRI or other scanners (for testing); see hardware/launchScan in the API reference, and Coder `demos > experimental control > fMRI_launchScan.py` (Jeremy)
* ADDED right-clicking the expInfo in Experiment Settings tests & previews the dialog box (Jeremy)
* ADDED syntax checking in code component dialog, right-click (Jeremy)
* IMPROVED documentation (thanks Becky Sharman)
* IMPROVED syntax for using $ in code snippets (e.g., "[$xPos, $yPos]" works) (Jeremy)
* IMPROVED Flow and Routine displays in the Builder, with zooming; see the View menu for key-board shortcuts (Jeremy)
* IMPROVED Neater (and slightly faster) changing of Builder Routines on file open/close
* FIXED demos now unpack to an empty folder (Jeremy)
* FIXED deleting an empty loop from the flow now works (Jeremy)
* FIXED further issue in QUEST (the addition in 1.65.01 was being used too widely)
* FIXED bug with updating of gamma grid values in Monitor Center

PsychoPy 1.65
------------------------------

PsychoPy 1.65.02
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Released July 2011

* FIXED Builder keyboard component was storing 'all keys' on request but not all RTs
* FIXED Aperture Component in Builder, which was on for an entire Routine. Now supports start/stop times like other components
* IMPROVED Sound stimuli in Builder:

    * FIXED: sounds could be distorted and would repeat if duration was longer than file
    * ADDED volume parameter to sound stimuli
    * FIXED: duration parameter now stops a file half-way through if needed

* FIXED buglet preventing some warning messages being printed to screen in Builder experiments
* FIXED bug in the copying/pasting of Builder Routines, which was previously introducing errors of the script with invalid _continueName values

PsychoPy 1.65.01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(Released July 2011)

* FIXED buglets in QUEST handler (thanks Gerrit Maus)
* FIXED absence of pygame in 1.65.00 Standalone release
* ADDED shelve module to Standalone (needed by scipy.io)
* ADDED warnings about going outside the monitor gamut for certain colors (thanks Alex Holcombe)

PsychoPy 1.65.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(Released July 2011)

* ADDED improved gamma correction using L=a+(b+kI)**G formula (in addition to industry-standard form). Existing gamma calibrations will continue to use old equation but new calibrations will take the new extended formula by default.
* ADDED MultiStairHandler to run multiple interleaved staircases (also from the Builder)
* ADDED createFactorialTrialList, a convenience function for full factorial conditions (thanks Marco Bertamini)
* CHANGED Builder keyboard components now have the option to discard previous keys (on by default)
* CHANGED RatingScale:

  - ADDED: argument to set lineColor independently (thanks Jeff Bye)
  - CHANGED default marker is triangle (affects windows only)
  - ADDED single-click option, custom-marker support
  - FIXED: bug with precision=1 plus auto-rescaling going in steps of 10 (not 1)

* FIXED errors with importing from 'ext' and 'contrib'
* FIXED error in joystick demos
* FIXED bug in ElementArrayStim depth
* FIXED bug in misc.maskMatrix. Was not using correct scale (0:1) for the mask stage
* FIXED buglet in StairHandler, which was only terminating during a reversal
* FIXED bug when loading movies - they should implicitly pause until first draw() (thanks Giovanni Ottoboni)
* IMPROVED handling of non-responses in Builder experiments, and this can now be the correct answer too (corrAns=None). ie. can now do go/no-go experiments. (Non-responses are now empty cells in excel file, not "--" as before.)

PsychoPy 1.64
------------------------------

PsychoPy 1.64.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released April 2011

* ADDED option to return field names when importing a trial list (thanks Gary Lupyan)
* ADDED Color-picker on toolbar for Coder and context menu for Builder (Jeremy Gray)
* ADDED CustomMouse to visual (Jeremy Gray)
* ADDED Aperture object to visual (thanks Yuri Spitsyn) and as a component to Builder (Jeremy Gray)
* CHANGED RatingScale (Jeremy Gray):
    - FIXED bug in RatingScale that prevented scale starting at zero
    - ADDED RatingScale "choices" (non-numeric); text size, color, font, & anchor labels; pos=(x,y) (Jeremy Gray)
    - CHANGED RatingScale internals; renamed escapeKeys as skipKeys; subject now uses 'tab' to skip (Jeremy Gray)
* ADDED user-configurable code/output font (see coder prefs to change)
* ADDED gui.Dlg now automatically uses checkboxes for bools in inputs (Yuri Spitsyn)
* ADDED RatingScale component for Builder (Jeremy Gray)
* ADDED packages to Standalone distros:
    - pyxid (Cedrus button boxes)
    - labjack (good, fast, cheap USB I/O device)
    - egi (pynetstation)
    - pylink (SR Research eye trackers)
    - psignifit (bootstrapping, but only added on mac for now)
* ADDED option for Builder components to take code (e.g. variables) as start/duration times
* ADDED support for RGBA files in SimpleImageStim
* IMPROVED namespace management for variables in Builder experiments (Jeremy Gray)
* IMPROVED prefs dialog
* IMPROVED test sequence for PsychoPy release (so hopefully fewer bugs in future!)
* FIXED bug with ElementArrayStim affecting the subsequent color of ShapeStim
* FIXED problem with the error dialog from Builder experiments not being a sensible size (since v1.63.03 it was just showing a tiny box instead of an error message)
* FIXED Coder now reloads files changed outside the app when needed (thanks William Hogman)
* FIXED Builder Text Component now respects the font property
* FIXED problem with updating to a downloaded zip file (win32 only)
* FIXED bug with ShapeStim.setOpacity when no shaders are available
* FIXED *long-standing pygame scaling bug*
* FIXED you can now scroll Builder Flow and still insert a Routine way to the right

PsychoPy 1.63
------------------------------

PsychoPy 1.63.04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2011

* FIXED bug in windows prefs that prevents v1.63.03 from starting up
* FIXED bug that prevents minolte LS100 from being found

PsychoPy 1.63.03
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2011

* ADDED Interactive shell to the bottom panel of the Coder view. Choose (in prefs) one of;
    * pyShell (the default, with great tooltips and help)
    * IPython (for people that like it, but beware it crashes if you create a psychopy.visual.Window() due to some threading issue(?))
* ADDED scrollbar to output panel
* FIXED small bug in QUEST which gave an incorrectly-scaled value for the next() trial
* FIXED ElementArrayStim was not drawing correctly to second window in multi-display setups
* FIXED negative sound durations coming from Builder, where sound was starting later than t=0
* FIXED a problem where Builder experiments failed to run if 'participant' wasn't in the experiment info dialog

PsychoPy 1.63.02
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2011

* ADDED clearFrames option to Window.saveMovieFrames
* ADDED support for Spectrascan PR655/PR670
* ADDED 'height' as a type of unit for visual stimuli
    NB. this is likely to become the default unit for new users (set in prefs)
    but for existing users the unit set in their prefs will remain. That means
    that your system may behave differently to your (new user) colleague's
* IMPROVED handling of damaged experiments in Builder (they don't crash the app any more!)
* IMPROVED performance of autoLogging (including demos showing how to turn of autoLog for dynamic stimuli)

PsychoPy 1.63.01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released Jan 2011

* FIXED bug with ElementArrayStim.setFieldPos() not updating
* FIXED mouse release problem with pyglet (since in 1.63.00)
* ADDED ability to retrieve a timestamp for a mouse event, similar to those in keyboard events.
    This is possible even though you may not retrieve the mouse event until later (e.g. waiting
    for a frame flip). Thanks Dave Britton
* FIXED bug with filters.makeGrating: gratType='sqr' was not using ori and phase
* FIXED bug with fetching version info for autoupdate (was sometimes causing a crash on startup
    if users selected 'skip ths version')
* CHANGED optimisation routine from fmin_powell to fmin_bfgs. It seems more robust to starting params.

PsychoPy 1.63.00
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Released Dec 2010

* **ADDED autoLog mechanism:**
    * many more messages sent, but only written when log.flush() is called
    * rewritten backend to logging functions to remove file-writing performance hit
    * added `autoLog` and `name` attributes to visual stimuli
    * added setAutoDraw() method to visual stimuli (draws on every win.flip() until set to False)
    * added logNextFlip() method to visual.Window to send a log message time-stamped to flip
* **FIXED bug in color calibration for LMS color space (anyone using this space should recalibrate immediately)** Thanks Christian Garber for picking up on this one.
* FIXED bug with excel output from StairHandler
* FIXED bug in ElemetArray.setSizes()
* FIXED bug in running QuestHandler (Zarrar Shehzad)
* FIXED bug trying to remove a Routine from Flow when enclosed in a Loop
* FIXED bug with inseting Routines into Flow under Linux
* FIXED bug with playing a MovieStim when another is already playing
* CHANGED default values for Builder experiment settings (minor)
* CHANGED ShapeStim default fillColor to None (from (0,0,0))
* FIXED DotStim now supports a 2-element fieldSize (x,y) again
* CHANGED phase of RadialStim to be 'sin' instead of 'cosine' at phase=0
* FIXED rounding issue in RadialStim phase
* FIXED ElementArrayStim can now take a 2x1 input for setSizes(), setSFs(), setPhases()
* ADDED packages to standalone distributions: pyserial, pyparallel (win32 only), parallel python (pp), IPython
* CHANGED Builder demos are now back in the distributed package. Use >Demos>Unpack... to put them in a folder you have access to and you can then run them from the demos menu
* FIXED bug with ShapeStim initialisation (since 1.62.02)
* UPDATED: Standalone distribution now uses Python2.6 and adds/upgrades;
    * parallel python (pp)
    * pyserial
    * ioLabs
    * ipython (for future ipython shell view in coder)
    * numpy=1.5.1, scipy=0.8.0, matplotlib=1.0
* UPDATED: Builder demos

PsychoPy 1.62
------------------------------

PsychoPy 1.62.02
~~~~~~~~~~~~~~~~~~~~~~~~
Released Oct 2010

* FIXED: problem with RadialStim causing subsequent TextStims not to be visible
* FIXED: bug with saving StairHandler data as .xlsx
* ADDED: option for gui.fileOpenDlg and fileSaveDlg to receive a custom file filter
* FIXED: builder implementation of staircases (initialisation was buggy)
* FIXED: added Sound.setSound() so that sounds in builder can take new values each trial
* FIXED: when a Routine was copied and pasted it didn't update its name properly (e.g. when inserted into the Flow it kept the origin name)
* FIXED: color rendering for stimuli on non-shader machines using dkl,lms, and named color spaces
* ADDED: data.QuestHandler (Thanks to Zarrar Shehzad). This is much like StairHandler but uses the QUEST routine of Watson and Pelli
* **CHANGED: TextStim orientation now goes the other way, for consistency with other stimuli (thanks Manuel Spitschan for noticing)**
* FIXED: Problem with DotStim using 'sqr' fieldShape
* ADDED: MovieStim now has a setMovie() method (a copy of loadMovie())
* FIXED: problem with MovieStim.loadMovie() when a movie had already been loaded

PsychoPy 1.62.01
~~~~~~~~~~~~~~~~~~~~~~~~
Released Sept 2010

* ADDED: clicking on a Routine in the Flow window brings that Routine to current focus above
* ADDED: by setting a loop in the Flow to have 0 repeats, that part of your experiment can be skipped
* CHANGED: builder hides mouse now during fullscreen experiments (should make this a pref or setting though?)
* FIXED: rendering problem with the Flow and Routine panels not updating on some platforms
* ADDED: added .pause() .play() and .seek() to MovieStim (calling .draw() while paused will draw current static frame)
* FIXED: bug in MovieStim.setOpacity() (Ariel Rokem)
* FIXED: bug in win32 - shortcuts were created in user-specific start menu not all-users start menu
* CHANGED: data output now uses std with N-1 normalisation rather than (scipy default) N
* FIXED: bug when .psyexp files were dropped on Builder frame
* FIXED: bug with Builder only storing last letter or multi-key button (e.g. 'left'->'t') under certain conditions
* FIXED: when nReps=0 in Builder the loop should be skipped (was raising error)
* CHANGED: mouse icon is now hidden for full-screen Builder experiments
* FIXED: Builder was forgetting the TrialList file if you edited something else in the loop dialog
* ADDED: visual.RatingScale and a demo to show how to use it (Jeremy Gray)
* ADDED: The Standalone distributions now includes the following external libs:
    - pynetstation (import psychopy.hardware.egi)
    - ioLab library (import psychopy.harware.ioLab)
* ADDED: trial loops in builder can now be aborted by setting someLoopName.finished=True
* ADDED: improved timing. *Support for blocking on VBL for all platforms* (may still not work on intel integrated chips)
* FIXED: minor bug with closing Coder windows generating spurious error messages
* ADDED: 'allowed' parameter to gui.fileOpeNDlg and fileCloseDlg to provide custom file filters

PsychoPy 1.62.00
~~~~~~~~~~~~~~~~~~~~~~~~
Released: August 2010

* ADDED: support for Excel 2007 files (.xlsx) for data output and trial types input:
    - psychopy.data now has importTrialList(fileName) to generate a trial list (suitable for TrialHandler) from .xlsx or .csv files
    - Builder loops now accept either an xlsx or csv file for the TrialList
    - TrialHandler and StairHandler now have saveToExcel(filename, sheetName='rawData', appendFile=True). This can be used to generate almost identical files to the previous delimited files, but also allows multiple (named) worksheets in a single file. So you could have one file for a participant and then one sheet for each session or run.
* CHANGED: for builder experiments the trial list for a loop is now imported from the file on every run, rather than just when the file is initially chosen
* CHANGED: data for TrialHandler are now stored as masked arrays where possible. This means that trials with no response can be more easily ignored by analysis
* FIXED: bug opening loop properties (bug introduced by new advanced params option)
* FIXED: bug in Builder code generation for keyboard (only when using forceEnd=True but store='nothing')
* CHANGED: RunTimeInfo is now in psychopy.info not psychopy.data
* CHANGED: PatchStim for image files now defaults to showing the image at native size in pixels (making SimpleImageStim is less useful?)
* CHANGED: access to the parameters of TrialList in the Builder now (by default) uses a more cluttered namespace for variables. e.g. if your TrialList file has heading rgb, then your components can access that with '$rgb' rather than '$thisTrial.rgb'. This behaviour can be turned off with the new Builder preference 'allowClutteredNamespace'.
* FIXED: if Builder needs to output info but user had closed the output window, it is now reopened
* FIXED: Builder remembers its window location
* CHANGED: Builder demos now need to be fetched by the user - menu item opens a browser (this is slightly more effort, but means the demos aren't stored within the app which is good)
* CHANGED: loops/routines now get inserted to Flow by clicking the mouse where you want them :-)
* ADDED: you can now have multiple Builder windwos open with different experiments
* ADDED: you can now copy and paste Routines form one Builder window to another (or itself) - useful for reusing 'template' routines
* FIXED: color of window was incorrectly scaled for 'named' and 'rgb256' color spaces
* ADDED: quicktime movie output for OSX 10.6 (10.5 support was already working)
* ADDED: Mac app can now receive dropped files on the coder and builder panels (but won't check if these are sensible!!)
* ADDED: debugMode preference for the app (for development purposes)
* ADDED: working version of RatingStim

PsychoPy 1.61
------------------------------

PsychoPy 1.61.03
~~~~~~~~~~~~~~~~~~~~~~~~
Patch released July 2010

* FIXED: harmless error messages caused by trying to get the file date/time when no file is open
* CHANGED: movie file used in movie demo (the chimp had unknown copyright)
* FIXED: problem with nVidia cards under win32 being slow to render RadialStim
* FIXED bug in filters.makeGrating where gratType='sqr'
* FIXED bug in new color spaces for computers that don't support shaders
* ADDED option to Builder components to have 'advanced' parameters not shown by default (and put this to use for Patch Component)

PsychoPy 1.61.02
~~~~~~~~~~~~~~~~~~~~~~
Patch released June 2010

* ADDED: Code Component to Builder (to insert arbitrary python code into experiments)
* ADDED: visual.RatingScale 'stimulus' (thanks to JG). See ratingScale demo in Coder view
* FIXED: TrialHandler can now have dataTypes that contain underscores (thanks fuchs for the fix)
* FIXED: loading of scripts by coder on windows assumed ASCII so broke with unicode characters. Now assumes unicode (as was case with other platforms)
* FIXED: minor bugs connecting to PR650

PsychoPy 1.61.01
~~~~~~~~~~~~~~~~~~~~~~
Patch released May 2010

* FIXED: Bug in coder spitting out lots of errors about no method BeginTextColor
* FIXED: Buglet in rendering of pygame text withour shaders
* FIXED: broken link for >Help>Api (reference) menuitem

PsychoPy 1.61.00
~~~~~~~~~~~~~~~~~~~~~~
Released May 2010

* CHANGED: color handling substantially. Now supply color and colorSpace arguments and use setColor rather than setRGB etc. Previous methods still work but give deprecation warning.
* ADDED: Colors can now also be specified by name (one of the X11 or web colors, e.g. 'DarkSalmon') or hex color spec (e.g. '#E9967A')
* REMOVED: TextStimGLUT (assuming nobody uses GLUT backend anymore)
* ADDED: 'saw' and 'tri' options to specify grating textures, to give sawtooth and triangle waves
* FIXED: visual.DotStim does now update coherence based on setFieldCoherence calls
* FIXED: bug in autoupdater for installs with setuptools-style directory structure
* FIXED: bug in SimpleImageStim - when graphics card doesn't support shaders colors were incorrectly scaled
* CHANGED: console (stdout) default logging level to WARNING. More messages will appear here than before
* ADDED: additional log level called DATA for saving data info from experiments to logfiles
* ADDED: mouse component to Builder
* ADDED: checking of coder script for changes made by an external application (thanks to Jeremy Gray)
* ADDED: data.RuntimeInfo() for providing various info about the system at launch of script (thanks to Jeremy Gray)
* FIXED: problem with rush() causing trouble between XP/vista (thanks to Jeremy Gray)
* AMERICANIZATION: now consistently using 'color' not 'colour' throughout the project! ;-)
* FIXED: problem with non-numeric characters being inserted into data structures
* CHANGED: stimuli using textures now automatically clean these up, so no need for users to call .clearTextures()

PsychoPy 1.60
------------------------------

PsychoPy 1.60.04
~~~~~~~~~~~~~~~~~~~~~~
Released March 2010

* FIXED build error (OS X 10.6 only)

PsychoPy 1.60.03
~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2010

* FIXED buglet in gui.py converting 'false' to True in dialogs (thanks Michael MacAskill)
* FIXED bug in winXP version introduced by fixes to the winVista version! Now both should be fine!!

PsychoPy 1.60.02
~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2010

* CHANGED ext.rush() is no longer run by default on creation of a window. It seems to be causing more probs and providing little enhancement.
* FIXED error messages from vista/7 trying to import pywintypes.dll

PsychoPy 1.60.01
~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2010

* FIXED minor bug with the new psychophysicsStaircase demo (Builder)
* FIXED problem with importing wx.lib.agw.hyperlink (for users with wx<2.8.10)
* FIXED bug in the new win.clearBuffer() method
* CHANGED builder component variables so that the user inputs are interpretted as literal text unless preceded by $, in which case they are treated as variables/python code
* CHANGED builder handling of keyboard 'allowedKeys' parameter. Instead of `['1','2','q']` you can now simply use `12q` to indicate those three keys. If you want a key like `'right'` and `'left'` you now have to use `$['right','left']`
* TWITTER follow on http://twitter.com/psychopy
* FIXED? win32 version now compatible with Vista/7? Still compatible with XP?

PsychoPy 1.60.00
~~~~~~~~~~~~~~~~~~~~~~
Released Feb 2010

* simplified prefs:
       - no more site prefs (user prefs only)
       - changed key bindings for compileScript(F5), runScript(Ctrl+R), stopScript(Ctrl+.)
* ADDED: full implementation of staircase to Builder loops and included a demo for it to Builder
* CHANGED: builder components now have a 'startTime' and 'duration' rather than 'times'
* ADDED: QuickTime output option for movies (OSX only)
* ADDED: script is saved by coder before running (can be turned off in prefs)
* ADDED: coder checks (and prompts) for filesave before running script
* ADDED: setHeight to TextStim objects, so that character height can be set after initialisation
* ADDED: setLineRGB, setFillRGB to ShapeStim
* ADDED: ability to auto-update form PsychoPy source installer (zip files)
* ADDED: Monitor Center can be closed with Ctrl-W
* ADDED: visual.Window now has a setRGB() method
* ADDED: visual.Window now has a clearBuffer() method
* ADDED: context-specific help buttons to Builder dialogs
* ADDED: implemented of code to flip SimpleImageStim (added new methods flipHoriz() and flipVert())
* ADDED: Butterworth filters to psychopy.filters (thanks Yaroslav Halchenko)
* ADDED: options to view whitespace, EOLs and indent guides in Coder
* ADDED: auto-scaling of time axis in Routines panel
* IMPROVED: Splash screen comes up faster to show the app is loading
* FIXED: bug in RadialStim .set functions (default operation should be "" not None)
* FIXED: on mac trying to save an unchanged document no longer inserts an 's'
* FIXED: bug with SimpleImageStim not drawing to windows except #1
* FIXED: one bug preventing PsychoPy from running on vista/win7 (are there more?)
* CHANGED: psychopy.filters.makeMask() now returns a mask with values -1:1, not 0:1 (as expected by stimulus masks)
* RESTRUCTURED: the serial package is no longer a part of core psychopy and is no longer required (except when hardware is actually being connected). This should now be installed as a dependency by users, but is still included with the Standalone packages.
* RESTRUCTURED: preparing for further devices to be added, hardware is now a folder with files for each manufacturer. Now use e.g.::

    from psychopy.hardware.PR import PR650
    from psychopy.hardware.cedrus import RB730

PsychoPy 1.51.00
------------------------------
(released Nov 2009)

* CHANGED: gamma handling to handle buggy graphics drivers on certain cards - see note below
* CHANGED: coord systems for mouse events - both winTypes now provide mouse coords in the same units as the Window
* FIXED: mouse in pyglet window does now get hidden with Window allowGUI=False
* FIXED: (Builder) failed to open from Coder view menu (or cmd/ctrl L)
* FIXED: failure to load user prefs file
* ADDED: keybindings can be handled from prefs dialog (thanks to Jeremy Gray)
* ADDED: NxNx3 (ie RGB) numpy arrays can now be used as textures
* FIXED: MovieStim bug on win32 (was giving spurious avbin error if visual was imported before event)

NB. The changes to gamma handling should need no changes to your code, but could alter the gamma correction on
some machines. For setups/studies that require good gamma correction it is recommended that you recalibrate when
you install this version of PsychoPy.

PsychoPy 1.50
------------------------------

PsychoPy 1.50.04
~~~~~~~~~~~~~~~~~~~~~~
(released Sep 09)

* FIXED (Builder) bug with loading files (monitor fullScr incorrectly reloaded)
* FIXED (Coder) bug with Paste in coder
* FIXED (Builder) bug with drop-down boxes
* FIXED (Builder) bug with removed routines remaining in Flow and InsertRoutineDlg
* MOVED demos to demos/scripts and added demos/exps (for forthcoming Builder demos)
* CHANGED (Builder) creating a new file in Builder (by any means) automatically adds a 'trial' Routine
* FIXED (Builder) various bugs with the Patch component initialisation (params being ignored)
* FIXED (Builder) better default parameters for text component

PsychoPy 1.50.02
~~~~~~~~~~~~~~~~~~~~~~
(released Sep 09)

* FIXED bug loading .psydat (files component variables were being saved but not reloaded)
* removed debugging messages that were appearing in Coder output panel
* FIXED long-standing problem (OS X only) with "save unchanged" dialogs that won't go away
* FIXED bug with 'cancel' not always cancelling on "save unchanged" dialogs
* ADDED warning dialog if user adds component without having any routines
* ADDED builder now remembers its location, size and panel sizes (which can be moved around)

PsychoPy 1.50.01
~~~~~~~~~~~~~~~~~~~~~~
(released Sep 09)

* FIXED problem creating prefs file on first use
* FIXED problem with removing (identical) routines in Flow panel
* FIXED problem with avbin import (OS X standalone version)

PsychoPy 1.50.00
~~~~~~~~~~~~~~~~~~~~~~
(released Sep 09)

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
(released Jul 09)

* DotStim can have fieldShape of 'sqr', 'square' or 'circle' (the first two are equiv)
* CHANGED intepreters in all .py scripts to be the same (#!/usr/bin/env python). Use PATH env variable to choose non-default python version for your Python scripts
* CHANGED pyglet textures to use numpy->ctypes rather than numpy->string
* FIXED systemInfo assigned on Linux systems

PsychoPy 1.00.03
~~~~~~~~~~~~~~~~~~~~~~
(released Jul 09)

* FIXED initialisation bug with SimpleImageStimulus
* FIXED "useShaders" buglet for TextStim
* CHANGED IDE on win32 to run scripts as processes rather than imports (gives better error messages)
* ADDED mipmap support for textures (better antialiasing for down-scaling)
* CHANGED win32 standalone to include the whole raw python rather than using py2exe

PsychoPy 1.00.02
~~~~~~~~~~~~~~~~~~~~~~
(released Jun 09)

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
(released Feb 09)

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
* ADDED check for floats as arguments to ElementArrayStim set methods
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
* LMS colors (cone-isolating stimuli) are now tested and accurate (when calibrated)
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
