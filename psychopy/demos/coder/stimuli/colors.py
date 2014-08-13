#!/usr/bin/env python2
from psychopy import visual, event, core, logging

#demo color spaces

#note that for this demo to present colors properly in calibrated
#DKL space (where isoluminant stimuli have elevation=0) you need
#to calibrate your monitor with a suitable spectrophotometer. If you
#have a PR60 then you can do this automatically using MonitorCenter.py
#in the monitors package

#Note for each stimulus that the color refers to the central bar on the grating
#If there are multiple lobes (a high enough SF) then the other color is simply the
#complement of the one specified (passing through neutral gray)

myWin = visual.Window((600,600), monitor='testMonitor')

stims = []
#rgb colors
stims.append( visual.GratingStim(myWin, mask='gauss',color='red', pos=[-0.5,0.5],sf=2) )#r
stims.append( visual.GratingStim(myWin, mask='gauss',color=(-1,1,-1), colorSpace='rgb', pos=[-0.5,0],sf=2))# g
stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,0,255), colorSpace='rgb255', pos=[-0.5,-0.5],sf=2))# b

#DKL cardinal axes (see Derrington, Krauskopf and Lennie 1986)
stims.append( visual.GratingStim(myWin, mask='gauss',color=(90,0,1), colorSpace='dkl',pos=[0,0.5],sf=2) )#achrom
stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,0,1), colorSpace='dkl',pos=[0,0],sf=2))# L-M
stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,90,1), colorSpace='dkl',pos=[0,-0.5],sf=2))# S

#cone-isolating stimuli
#stims.append( visual.GratingStim(myWin, mask='gauss',color=(0.2,0,0), colorSpace='lms', pos=[0.5,0.5],sf=2))
#stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,0.2,0), colorSpace='lms', pos=[0.5,0],sf=2))
#stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,0,0.5), colorSpace='lms', pos=[0.5,-0.5],sf=2))

#HSV. This is a device-dependent space
#(i.e. it will differ on each monitor but needs no calibration)
stims.append( visual.GratingStim(myWin, mask='gauss',color=(0,1,1), colorSpace='hsv', pos=[0.5,0.5],sf=0))
stims.append( visual.GratingStim(myWin, mask='gauss',color=(45,1,1), colorSpace='hsv', pos=[0.5,0],sf=0))
stims.append( visual.GratingStim(myWin, mask='gauss',color=(90,1,1), colorSpace='hsv', pos=[0.5,-0.5],sf=0))

for thisStim in stims:
    thisStim.draw()
myWin.flip()
#quit when a key is pressed
#event.waitKeys()
core.wait(2)
myWin.close()
