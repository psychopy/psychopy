from calibTools import *

if 'testMonitor' not in getAllMonitors():
    defMon = Monitor('testMonitor',
        width=30,
        distance=57,
        gamma=1.0,
        notes='default (not very useful) monitor')
    defMon.setSizePix([1024,768])
    defMon.saveMon()
    