# runtimeInfo.py: a demo showing some use-cases for class data.RuntimeInfo(), which calls visual.getMsPerFrame()

# These are used in the demo, in the way you might in your experiment:
__author__ = 'Jeremy """R.""" Gray' ## double-quotes will be silently removed
__version__ = "v1.0.a''' "               ## single quotes will be left, eg, O'Connor

from psychopy import visual, log, data

# When creating an experiment, first define your window (& monitor):
myWin = visual.Window(fullscr=True, monitor='testMonitor')
myWin.setRecordFrameIntervals(True)
log.console.setLevel(log.DEBUG)

# Then gather run-time info. All parameters are optional:
info = data.RuntimeInfo(
        author=__author__+' <-- your name goes here, plus whatever you like, e.g., your lab or contact info',
        version=__version__+" <-- your experiment version info",
        win=myWin,    ## a psychopy.visual.Window() instance
        refreshTest='grating', ## None, True, or 'grating' (eye-candy to avoid a blank screen)
        verbose=True, ## True means report on everything 
        userProcsDetailed=True,  ## if verbose and userProcsDetailed, return (command, process-ID) of the user's processes
        randomSeed='set:time', ## a way to record, and optionally set, a random seed of type str; None -> default
            ## 'time' will use experimentRuntime.epoch as the value for the seed, different value each time the script is run
            ##'set:time' --> seed value is set to experimentRuntime.epoch, and initialized: random.seed(info['randomSeed'])
            ##'set:42' --> set & initialize to str('42'), and will give the same sequence of random.random() for all runs of the script
        )
myWin.close()

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
    info["windowRefreshTimeAvg_ms"]  # just to raise exception here if no keys
    print "or from the test of the screen refresh rate:"
    print "  %.2f ms = average refresh time" % info["windowRefreshTimeAvg_ms"]
    print "  %.2f ms = median (average of 12 at the median, best estimate of monitor refresh rate)" % info["windowRefreshTimeMedian_ms"]
    print "  %.3f ms = standard deviation" % info["windowRefreshTimeSD_ms"]

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
    myWin = visual.Window((800,600), fullscr=True, ...
and re-run the demo."""
except:
    pass
print """
(NB: The visual is not the demo! Scroll up to see the text output.)"""