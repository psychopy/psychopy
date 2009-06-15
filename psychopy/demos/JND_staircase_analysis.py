#!/usr/bin/env python

#This analysis script takes one or more staircase datafiles as input from a GUI
#It then plots the staircases on top of each other on the left 
#and a combined psychometric function from the same data
#on the right
#

from psychopy import data, gui, misc, core
import pylab, scipy

files = gui.fileOpenDlg('.')
if not files:
    core.quit()

#get the data from all the files
allIntensities, allResponses = [],[]
for thisFileName in files:
    thisDat = misc.fromFile(thisFileName)
    assert isinstance(thisDat, data.StairHandler)
    allIntensities.append( thisDat.intensities )
    allResponses.append( thisDat.data )
    
#plot each staircase
pylab.subplot(121)
colors = 'brgkcmbrgkcm'
lines, names = [],[]
for fileN, thisStair in enumerate(allIntensities):
    #lines.extend(pylab.plot(thisStair))
    #names = files[fileN]
    pylab.plot(thisStair, label=files[fileN])
#pylab.legend()

#get combined data
combinedInten, combinedResp, combinedN = \
             data.functionFromStaircase(allIntensities, allResponses, 5)
#fit curve
fit = data.FitWeibull(combinedInten, combinedResp, guess=[0.2, 0.5])
smoothInt = pylab.arange(min(combinedInten), max(combinedInten), 0.001)
smoothResp = fit.eval(smoothInt)
thresh = fit.inverse(0.8)
print thresh

#plot curve
pylab.subplot(122)
pylab.plot(smoothInt, smoothResp, 'k-')
pylab.plot([thresh, thresh],[0,0.8],'k--'); pylab.plot([0, thresh],[0.8,0.8],'k--')
pylab.title('threshold = %0.3f' %(thresh))
#plot points
pylab.plot(combinedInten, combinedResp, 'ko')
pylab.ylim([0,1])

pylab.show()
    

    