"""
Demo of some ways to use class psychopy.info.RunTimeInfo()
to obtain current system and other data at run-time.
"""

from psychopy import visual, logging, core
import psychopy.info

# author and version are used in the demo, in the way you might in your experiment. They are 
# expected to be at the top of the script that calls RunTimeInfo()), with a string literal 
# assigned to them (no variables). Double-quotes will be silently removed, single quotes will be 
# left, eg, O'Connor
__author__ = """Jeremy "R." Gray"""
__version__ = "v1.0.a"

# create your window (& monitor), same as any other experiment
win = visual.Window(
    fullscr=False,
    size=[200, 200], 
    monitor='testMonitor'
)

# you may not want to run hardware tests with a participant sat there, so let's limit it to only run in pilot mode
PILOTING = core.setPilotModeFromArgs()

if PILOTING:
    # tell the window to record the time between frames
    win.recordFrameIntervals = True
    # log as much to the console as possible
    logging.console.setLevel(logging.DEBUG)
    # gather some runtime info! (all parameters are optional)
    runInfo = psychopy.info.RunTimeInfo(
        # setting author and version here overrides __author__ and __version__ from earlier
        author="Jeremy R. Gray",
        version="2025.2.0",
        # a psychopy.visual.Window() instance; None = default temp window used; False = no win, no win.flips()
        win=win,
        # None, True, or 'grating' (eye-candy to avoid a blank screen)
        refreshTest='grating',
        # True means report on everything
        verbose=True,
        # if verbose and userProcsDetailed, return (command, process-ID) of the user's processes
        userProcsDetailed=True,
    )
    # print the runtime info - check your console for this output
    print(
        """
System and other run-time details are now saved in "runInfo", a dict-like object. You have 
to decide what to do with it.

"print(runInfo)" will give you the same as "print(str(runInfo))". This format is intended 
to be useful for writing to a data file in a human readable form:
        """
    )
    print(runInfo)
    print(
        """
If that's more detail than you want, try:
    runInfo = info.RunTimeInfo(..., verbose=False, ...)

To get the same info in python syntax, use "print(repr(info))". You could write this format 
into a data file, and it's fairly readable. Because its python syntax, you could later 
simply import your data file into python to reconstruct the dict.
        """
    )
    # you can also use Python string formatting to show the info in whatever format you prefer
    print(
        """
You can extract single items from info, using keys, e.g.:
    psychopyVersion = %(psychopyVersion)s
        """ % runInfo
    )
    if "windowRefreshTimeAvg_ms" in runInfo:
        print(
            """
...or from the test of the screen refresh rate:
    average refresh time = %(windowRefreshTimeAvg_ms).2f ms
    standard deviation = %(windowRefreshTimeSD_ms).3f  ms
            """ % runInfo
        )
        # once you have run-time info, you can fine-tune things with the values, prior to 
        # running your experiment.
        refreshSDwarningLevel_ms = 0.20  # ms
        if runInfo["windowRefreshTimeSD_ms"] > refreshSDwarningLevel_ms:
            print(
                """
The variability of the refresh rate is sort of high (SD > %.2f ms).
                """ % refreshSDwarningLevel_ms
            )
        # and here you could prompt the user with suggestions, possibly based on other info
        if runInfo["windowIsFullScr"]:
            print(
                """
Your window is full-screen, which is good for timing.
                """
            )
        
        else:
            print(
                """
Try defining the window as full-screen (it's not currently), i.e. at the top of the demo change to:
    win = visual.Window((800, 600), fullscr=True, ...)
and re-run the demo.
                """
            )
        print(
            """
Possible issues:
- Internet/wireless?
- Bluetooth?
- Recent startup (not finished)?
            """
        )
        if len(runInfo['systemUserProcFlagged']):
            print(
                """
- Other programs running? (command, process-ID): %(systemUserProcFlagged)s
                """ % runInfo
            )

    print(
        """
(NB: The visual is not the demo! Scroll up to see the text output.)
        """
    )

win.close()
core.quit()

# The contents of this file are in the public domain.
