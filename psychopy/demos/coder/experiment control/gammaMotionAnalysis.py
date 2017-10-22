#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Use this script to analyze data from the gammaMotionNull.py
script.

Instructions: From the dialogue box select multiple staircases (Cmd-click
or shift-click) to plot the results
"""

from __future__ import absolute_import, division, print_function

import matplotlib
matplotlib.use('TKAgg')

from psychopy import data, gui, core
from psychopy.tools.filetools import fromFile
import pylab
import numpy as num

files = gui.fileOpenDlg('.')
if not files:
    core.quit()

# get the data from all the files
allIntensities, allResponses = [], []
for thisFileName in files:
    thisDat = fromFile(thisFileName)
    assert isinstance(thisDat, data.StairHandler)
    allIntensities.append( thisDat.intensities )
    allResponses.append( thisDat.data )

# plot each staircase
pylab.subplot(121)
lines, names = [], []
for fileN, thisStair in enumerate(allIntensities):
    # lines.extend(pylab.plot(thisStair))
    # names = files[fileN]
    pylab.plot(thisStair, label=files[fileN])
# pylab.legend()

# get combined data
i, r, n = data.functionFromStaircase(allIntensities, allResponses, 'unique')
combinedInten, combinedResp, combinedN = i, r, n

# fit curve
guess =[num.average(combinedInten), num.average(combinedInten)/5]

fit = data.FitWeibull(combinedInten, combinedResp, guess=guess, expectedMin=0.0)
smoothInt = num.arange(min(combinedInten), max(combinedInten), 0.001)
smoothResp = fit.eval(smoothInt)
thresh = fit.inverse(0.5)
print(thresh)

# plot curve
pylab.subplot(122)
pylab.plot(smoothInt, smoothResp, '-')
pylab.plot([thresh, thresh], [0, 0.5], '--')
pylab.plot([0, thresh], [0.5, 0.5], '--')
pylab.title('threshold = %0.3f' %(thresh))

# plot points
pylab.plot(combinedInten, combinedResp, 'o')
pylab.ylim([0, 1])

pylab.show()
core.quit()

# The contents of this file are in the public domain.
