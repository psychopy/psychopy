# runtimeInfo.py: a demo showing some use-cases for class RuntimeInfo()

__author__ = 'Jeremy "R." Gray' # these are used in the demo, like you might in your experiments
__version__ = "v1'0"

from psychopy import core, visual

# when creating an experiment, define your window (& monitor):
myWin = visual.Window((100,100),monitor='testMonitor') 
    # fullScr=True gives better timing, but is more confusing for this demo

# then gather run-time info, and save in a dict-like object (all parameters are optional):
info = core.RuntimeInfo(
        author=__author__+'; your name goes here (as author of your experiments); double-quotes are """""""silently removed"""""")', 
        version=__version__+"; your experiment version info; single quotes '''''''are unchanged''''''' ", 
        verbose=True, # True means everything; which might be too much for some situations
        win=myWin,  # default=None, which is fine
        ) 

print """
System and other run-time configuration is now saved in "info", a dict-like object. You have to decide
what to do with it--probably print some or all of it, likely into a data file or other log file.

"print info" will give you the same as "print str(info)". This format is intended to be useful 
for writing to a data file in a human readable form:
"""
print info
print """If that's more detail than you want in every data file, try verbose = False."""

print """
Here's the same info in python syntax. To get this, use "print repr(info)". You could write this format into 
a data file, and its fairly readable, only slightly less than the str(info) version. But because its 
python syntax you could later simply import your data file into python to reconstruct the dict:
"""
print "info = %s" % repr(info)

print """
Because info is a dict, you can extract single items using their keys, e.g.:
  psychopy_version = %s""" % info['psychopy_version']
print "  msPerFrame = %s" % info["msPerFrame"]

# some keys are only conditionally present, depending on how you configure your RuntimeInfo, so check if they exist:
if "win_monitor.name" in info.keys(): 
    print "  monitor = %s" % info["win_monitor.name"]