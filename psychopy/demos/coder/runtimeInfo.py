from psychopy import core

# gather system and other details as they are at execution-time, save in a dict-like object:
info = core.RuntimeInfo(
        author = 'Jeremy Gray (you would put the author of your experiment script here)', 
        version = '1.0 (replace with your experiment script version, if you like)', 
        verbose = True, # True means everything; which might be too much for some situations
        frameSamples = 120 # how many frames to use for estimating the refresh rate
        ) 

print """
System and other run-time configuration is now saved in /info/, a dict-like object.
Printing it will print str(info). This format is intended to be useful for writing to a data file 
in a human readable form, including comments and a meaningful order:"""
print info
print """If that's more than you want in every data file, try verbose = False."""

print """
Because info is a dict, you can extract single items using their keys, e.g.:
psychopy_version = %s""" % info['psychopy_version']

print """
Possible keys to use:"""
print info.keys()

print """
Finally, here's the same info in python syntax, using repr(info). You could write this format into 
a data file, and its fairly readable, only slightly less than the str(info) version. But because its 
python syntax you could later simply import your data file into python to reconstruct the dict:"""
print "info = %s" % (repr(info))

print
print "framesPerSecond = %s" % info['framesPerSecond']
print "msPerFrame = %s" % info["msPerFrame"]