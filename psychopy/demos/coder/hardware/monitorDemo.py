#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Often you can control monitors simply from the Monitor Center in the
PsychoPy application, but you can also create/control them using scripts.

This allow you to override certain values for the current run: :

    mon = monitors.Monitor('testMonitor')  # load the testMonitor
    mon.setDistance(120)  # change distance in this run (don't save)

Or you can load a specific calibration of that monitor:

    mon.setCurrent(-1) is the last (alphabetical) calibration
    mon.setCurrent('2015_05_21 11:42')  # use a specific named calibration

More info is available at http: //www.psychopy.org/api/monitors.html
"""

from __future__ import absolute_import, division, print_function

from psychopy import monitors

names = monitors.getAllMonitors()
for thisName in names:
    thisMon = monitors.Monitor(thisName)
    print(thisMon.getDistance())

# The contents of this file are in the public domain.
