# runtimeInfo.py: a demo showing some use-cases for class core.RuntimeInfo() and core.msPerFrame()

## these are used in the demo, in the way you might in your experiment:
__author__ = 'Jeremy "R." Gray' # double-quotes will be silently removed
__version__ = "v1.0.a' "               # single quotes are left, eg, O'Connor 

from psychopy import core, visual

# when creating an experiment, first define your window (& monitor):
myWin = visual.Window((300,300), fullscr=False, monitor='testMonitor', allowGUI=False, units='norm')

# then gather run-time info. All parameters are optional:
info = core.RuntimeInfo(
        author=__author__+' <-- your name goes here, plus whatever you like, e.g., your lab or contact info',
        version=__version__+" <-- your experiment version info",
        verbose=True, ## True means report on everything
        win=myWin,    ## a psychopy.visual.Window() instance
        progressBar=True, ## some eye-candy to avoid a blank screen
        userProcsDetailed=False, ## if verbose and userProcsDetailed, return details of the current user's other processes
        )

print """
System and other run-time configuration is now saved in "info", a dict-like object. You have to decide
what to do with it--probably print some or all of it, likely into a data file or other log file.

"print info" will give you the same as "print str(info)". This format is intended to be useful 
for writing to a data file in a human readable form:"""
print info

#print info
print """If that's more detail than you want, try: info = core.RuntimeInfo(...,verbose=False,...)."""

# To get the same info in python syntax, use "print repr(info)". You could write this format into 
# a data file, and its fairly readable. And because its python syntax you could later simply 
# import your data file into python to reconstruct the dict.
# d = eval(repr(info))
# type(d) == type({})

print """
You can extract single items from info, using keys, e.g.:
  psychopyVersion = %s""" % info['psychopyVersion']
print """Test of the screen refresh (60 samples):
  %s = average refresh time""" % info["windowMsPerFrameAvg"]
print "  %s = median (average of the 6 times nearest the median time)" % info["windowMsPerFrameMed6"]
print "  %s = standard deviation" % info["windowMsPerFrameSD"]

# Once you have run-time info, you can fine-tune things with the values, prior to running your experiment.
refreshSDwarningLevel = 0.10 ##ms
if info["windowMsPerFrameSD"] > refreshSDwarningLevel:
    print "\nThe variability of the refresh rate is unusually high (SD > %.2f)" % (refreshSDwarningLevel)
    ## and here you could prompt the user with suggestions, possibly based on:
    if info["windowIsFullScr"]: 
        print "(your window is full-screen, which is good for timing. maybe there are other programs running?)"
    else: 
        print """-> Try defining the window as full-screen (its not currently), i.e. at the top of the demo change to:
           myWin = visual.Window((200,200), fullscr=True, ...
    and re-run the demo."""

print """
(The progress-bar is not the demo! Scroll up to see the full text output.)"""
