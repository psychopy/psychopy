#demo color spaces
from psychopy import *

#note that for this demo to present colours properly in calibrated
#DKL space (where isoluminant stimuli have elevation=0) you need
#to calibrate your monitor with a suitable spectrophotometer. If you
#have a PR60 then you can do this automatically using MonitorCenter.py
#in the monitors package

myWin = visual.Window((600,600), monitor='laptop')
stims = []
#rgb colors
stims.append( visual.PatchStim(myWin, mask='gauss',rgb=[1,0,0], pos=[-0.5,0.5],sf=2) )#r
stims.append( visual.PatchStim(myWin, mask='gauss',rgb=(0,1,0), pos=[-0.5,0],sf=2))# g
stims.append( visual.PatchStim(myWin, mask='gauss',rgb=(0,0,1), pos=[-0.5,-0.5],sf=2))# b

#DKL cardinal axes (see Derrington, Krauskopf and Lennie 1986)
stims.append( visual.PatchStim(myWin, mask='gauss',dkl=(90,0,1), pos=[0,0.5],sf=2) )#achrom
stims.append( visual.PatchStim(myWin, mask='gauss',dkl=(0,0,1), pos=[0,0],sf=2))# L-M
stims.append( visual.PatchStim(myWin, mask='gauss',dkl=(0,90,1), pos=[0,-0.5],sf=2))# S

#cone-isolating stimuli
stims.append( visual.PatchStim(myWin, mask='gauss',lms=(0.2,0,0), pos=[0.5,0.5],sf=2))
stims.append( visual.PatchStim(myWin, mask='gauss',lms=(0,0.2,0), pos=[0.5,0],sf=2))
stims.append( visual.PatchStim(myWin, mask='gauss',lms=(0,0,0.5), pos=[0.5,-0.5],sf=2))

for thisStim in stims:
    thisStim.draw()
myWin.update()
#quit when a key is pressed
event.waitKeys()
core.quit()