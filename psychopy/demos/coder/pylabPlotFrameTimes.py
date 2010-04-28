#!/usr/bin/env python
from psychopy import visual, core, log, ext
import pylab


# demo to illustrate some plotting with pylab, with variable screen refresh times as data
#   http://matplotlib.sourceforge.net/
nFrames = 500
useFullScreen = True # False gives more interesting data for plotting; but try True as well

# get some data to plot; same as timeByFrames.py
myWin = visual.Window([600,600], screen=0, fullscr=useFullScreen, monitor='testMonitor', waitBlanking=True) #make a window
myWin.setRecordFrameIntervals(True) # myWin.frameIntervals will hold the data to plot
myStim = visual.PatchStim(myWin, tex='sin', mask='gauss', sf=3.0)
#rush(True)
for skipSomeInitialFrames in range(10): 
    #core.wait(0.015)
    myWin.flip()
myClock = core.Clock()
for frameN in range(nFrames):
    myStim.setPhase(1.0/nFrames, '+') #advance the phase (add 1.0/nFrames to prev value)
    myStim.draw()
    myWin.flip()
avg = myClock.getTime()/nFrames
#rush(False)
myWin.close() # this takes a while--do it after getting time from the clock

# plot in ms
frameTimes=pylab.array(myWin.frameIntervals[10:])*1000 #convert to ms

# horiz line at the mean
pylab.axhspan(avg*1000, avg*1000, linewidth=1, linestyle='dotted') 
pylab.plot(frameTimes, '-o')
# vertical line intersects sorted points at the median:
pylab.axvspan(len(frameTimes)/2, len(frameTimes)/2, .05, .95, linewidth=1, linestyle='dotted') 
frameTimes.sort() 
# plot sorted times on the same graph:
pylab.plot(frameTimes, '-o')

# a faint box based on the refreshThreshold, relative to the measured average: 
pylab.axhspan(myWin._refreshThreshold*1000, (2*avg - myWin._refreshThreshold)*1000, 
                linewidth=1, linestyle='dotted', alpha=.05) # transparent box above/below the mean
# invisible points help to set scale more nicely than autoscale:
pylab.plot([5+max(frameTimes)],'-o',alpha=0) 
pylab.plot([0],'-o',alpha=0) 

# add some description:
pylab.text(20,2,'upper theshold = %.2f ms' % (myWin._refreshThreshold * 1000))
if useFullScreen:
    pylab.title("window was Full-screen", color='black')
else:
    pylab.title("window was Not full-screen", color='red')
pylab.xlabel('frame')
pylab.ylabel('frame duration (ms)')
pylab.show()
