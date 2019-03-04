#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to plotting
"""

from __future__ import absolute_import, print_function


def plotFrameIntervals(intervals):
    """Plot a histogram of the frame intervals.

    Where `intervals` is either a filename to a file, saved by
    Window.saveFrameIntervals, or simply a list (or array) of frame intervals

    """
    from pylab import hist, show, plot

    if type(intervals) == str:
        f = open(intervals, 'r')
        intervals = eval("[%s]" % (f.readline()))
    #    hist(intervals, int(len(intervals)/10))
    plot(intervals)
    show()
