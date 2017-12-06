#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This analysis script takes one or more staircase datafiles as input from a GUI
It then plots the staircases on top of each other on the left
and a combined psychometric function from the same data
on the right.

The combined plot uses every unique X value form the staircase, and alters the
size of the points according to how many trials were run at that level
"""

from __future__ import absolute_import, division, print_function

from psychopy import data, gui, core
from psychopy.tools.filetools import fromFile
import pylab
import os

# set to 0.5 for Yes/No (or PSE). Set to 0.8 for a 2AFC threshold
threshVal = 0.5

# set to zero for Yes/No (or PSE). Set to 0.5 for 2AFC
expectedMin = 0.0

files = gui.fileOpenDlg('.')
if not files:
    core.quit()

# get the data from all the files
allIntensities, allResponses = [], []
for thisFileName in files:
    thisDat = fromFile(thisFileName)
    assert isinstance(thisDat, data.StairHandler)
    allIntensities.append(thisDat.intensities)
    allResponses.append(thisDat.data)
dataFolder = os.path.split(thisFileName)[0]  # just the path, not file name

# plot each staircase in left hand panel
pylab.subplot(121)
colors = 'brgkcmbrgkcm'
lines, names = [], []
for fileN, thisStair in enumerate(allIntensities):
    # lines.extend(pylab.plot(thisStair))  # uncomment for a legend for files
    # names = files[fileN]
    pylab.plot(thisStair, label=files[fileN])
# pylab.legend()

# get combined data
i, r, n = data.functionFromStaircase(allIntensities, allResponses, bins='unique')
combinedInten, combinedResp, combinedN = i, r, n
combinedN = pylab.array(combinedN)  # convert to array so we can do maths

# fit curve
fit = data.FitWeibull(combinedInten, combinedResp, expectedMin=expectedMin,
    sems=1.0 / combinedN)
smoothInt = pylab.arange(min(combinedInten), max(combinedInten), 0.001)
smoothResp = fit.eval(smoothInt)
thresh = fit.inverse(threshVal)
print(thresh)

# plot curve
pylab.subplot(122)
pylab.plot(smoothInt, smoothResp, 'k-')
pylab.plot([thresh, thresh], [0, threshVal], 'k--')  # vertical dashed line
pylab.plot([0, thresh], [threshVal, threshVal], 'k--')  # horizontal dashed line
pylab.title('threshold (%.2f) = %0.3f' %(threshVal, thresh))

# plot points
pointSizes = pylab.array(combinedN) * 5  # 5 pixels per trial at each point
points = pylab.scatter(combinedInten, combinedResp, s=pointSizes,
    edgecolors=(0, 0, 0), facecolor=(1, 1, 1), linewidths=1,
    zorder=10,  # make sure the points plot on top of the line
    )

pylab.ylim([0, 1])
pylab.xlim([0, None])
# save a vector-graphics format for future
outputFile = os.path.join(dataFolder, 'last.pdf')
pylab.savefig(outputFile)
print('saved figure to: ' + outputFile)
pylab.show()

core.quit()

# The contents of this file are in the public domain.
