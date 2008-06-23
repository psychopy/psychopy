import os, sys
import calibTools

#create a test monitor if there isn't one already
print calibTools.__file__
if 'testMonitor' not in calibTools.getAllMonitors():
    defMon = Monitor('testMonitor',
        width=30,
        distance=57,
        gamma=1.0,
        notes='default (not very useful) monitor')
    defMon.setSizePix([1024,768])
    defMon.saveMon()
    