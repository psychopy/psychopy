from psychopy import core

# gather system and other details as they are at execution-time, save in a dict-like object:
info = core.RuntimeInfo(
        author = 'Your Name Here (i.e., the author of your experiment script)', 
        version = '<1.0, i.e., your experiment script version>', 
        verbose = True # True means everything; which might be too much for some situations
        ) 

print """
System and other run-time conifguration is now saved in /info/, a dict-like object.
Printing it will print str(info). This format is intended to be useful for writing to a data file 
in a human readable form, including comments and a meaningful order:"""
print info
print """If that's more than you want in every data file, try verbose = False."""

print """
Because info is really a dict, you can extract single items using their keys, e.g.:
psychopy_version = """,
print info['psychopy_version']

print """
Possible keys to use:"""
print info.keys()

print """
Finally, here's the same info in python syntax, using repr(info). You could write this format into 
a data file, and its fairly readable, only slightly less than the str(info) version. Because its 
python syntax you could later simply import your data file into python:"""
print "info = %s" % (repr(info))