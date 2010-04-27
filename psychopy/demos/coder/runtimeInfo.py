# runtimeInfo.py: a demo showing some use-cases for class core.RuntimeInfo() and core.msPerFrame()

## these are used in the demo, in the way you might in your experiment:
__author__ = 'Jeremy "R." Gray' # double-quotes will be silently removed 
__version__ = "v1.0.a' "               # single quotes are left, eg, O'Connor 

from psychopy import core, visual

## when creating an experiment, first define your window (& monitor):
myWin = visual.Window((300,300), fullscr=False, monitor='testMonitor', allowGUI=False, units='norm', waitBlanking=True)

## then gather run-time info. All parameters are optional:
info = core.RuntimeInfo(
        author=__author__+' <-- your name goes here, plus whatever you like, e.g., your lab or contact info',
        version=__version__+" <-- your experiment version info",
        verbose=True, # True means report on everything
        win=myWin,    # a psychopy.visual.Window() instance
        refreshTest='progressBar', # None, True, or 'progressBar' (eye-candy to avoid a blank screen)
        userProcsDetailed=False  # if verbose and userProcsDetailed, return (command, process-ID) of the user's processes
        )

print """
System and other run-time details are now saved in "info", a dict-like object. You have to decide
what to do with it.

"print info" will give you the same as "print str(info)". This format is intended to be useful 
for writing to a data file in a human readable form:"""
print info
print """If that's more detail than you want, try: info = core.RuntimeInfo(...,verbose=False,...)."""

# To get the same info in python syntax, use "print repr(info)". You could write this format into 
# a data file, and its fairly readable. And because its python syntax you could later simply 
# import your data file into python to reconstruct the dict.


print "\nYou can extract single items from info, using keys, e.g.:"
print "  psychopyVersion = %s" % info['psychopyVersion']
try:
    info["windowRefreshTimeAvg_ms"]  # just to raise exception here if no key
    print "Test of the screen refresh rate (60 samples):"
    print "  %.2f ms = average refresh time" % info["windowRefreshTimeAvg_ms"]
    print "  %.2f ms = median (average of the 6 times nearest the median time)" % info["windowRefreshTimeMedian_ms"]
    print "  %.3f ms = standard deviation" % info["windowRefreshTimeSD_ms"]
    print "  %.2f ms = median + 3 SD" % (info["windowRefreshTimeMedian_ms"] +3*info["windowRefreshTimeSD_ms"])
    print "  %.2f ms = current refresh threshold" % (info["windowRefreshThreshold_sec"] * 1000)

    ## Once you have run-time info, you can fine-tune things with the values, prior to running your experiment.
    refreshSDwarningLevel_ms = 0.20 ##ms
    if info["windowRefreshTimeSD_ms"] > refreshSDwarningLevel_ms:
        print "\nThe variability of the refresh rate is sort of high (SD > %.2f ms)." % (refreshSDwarningLevel_ms)
        ## and here you could prompt the user with suggestions, possibly based on other info:
        if info["windowIsFullScr"]: 
            print "Your window is full-screen, which is good for timing."
            print 'Possible issues: internet / wireless? bluetooth? recent startup (not finished)?'
            if len(info['systemUserProcFlagged']):
                print 'other programs running? (command, process-ID):',info['systemUserProcFlagged']
        else: 
            print """Try defining the window as full-screen (its not currently), i.e. at the top of the demo change to:
    myWin = visual.Window((200,200), fullscr=True, ...
and re-run the demo."""
except:
    pass
print """
(NB: The progress-bar is not the demo! Scroll up to see the text output.)"""


