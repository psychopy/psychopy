#!/usr/bin/env python2

"""This stores variables that are needed globally through the visual package

It needs to be imported by anything that uses those variables as:

    from psychopy.visual import glob_vars
    print glob_vars.currWindow  #read it
    glob_vars.currentWindow = newWin #change it

Note that if you import using::

    from psychopy.visual.glob_vars import currWindow

then if the variable changes your copy won't!

"""

currWindow = None
nImageResizes = 0 #for logging purposes, how many times have we resized an image