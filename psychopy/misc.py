#!/usr/bin/env python

"""Tools, nothing to do with psychophysics or experiments
- just handy things like conversion functions etc...
"""

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy  # this is imported by psychopy.core
import random
from psychopy import logging, monitors

import os
import shutil
import glob
import cPickle
try:
    from PIL import Image
except ImportError:
    import Image






#---color conversions---#000000#FFFFFF------------------------------------------

#--- coordinate transforms ---------------------------------------------



def plotFrameIntervals(intervals):
    """Plot a histogram of the frame intervals.

    Where `intervals` is either a filename to a file, saved by Window.saveFrameIntervals
    or simply a list (or array) of frame intervals

    """
    from pylab import hist, show, plot

    if type(intervals)==str:
        f = open(intervals, 'r')
        exec("intervals = [%s]" %(f.readline()))
    #    hist(intervals, int(len(intervals)/10))
    plot(intervals)
    show()

