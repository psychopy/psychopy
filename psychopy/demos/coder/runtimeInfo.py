from psychopy import core

info = core.RuntimeInfo(author='<your experiment author>', version='<1.x>', verbose=True)

print "formatted for writing into a log file:"
print info # same as str(info)

print
print "Because its a dict, you can extract single items, based on a key:"
print "psychopy_version = %s" % (info['psychopy_version'])
infoKeys = info.keys()
infoKeys.sort()
print "Possible keys to use: \n%s" % (infoKeys)

print
print "Finally, here's the same info in python syntax (for recovering a dict)"
print "You might write this format into a data file, and later import your data file into python"
print "info = %s" % (repr(info))