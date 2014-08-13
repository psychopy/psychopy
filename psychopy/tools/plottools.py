#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to plotting'''


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
