#!/usr/bin/env python
from psychopy import core, visual, event

"""There are two options for drawing image-based stimuli in PsychoPy:
    
    SimpleImageStim is ideal if you don't need to draw a large number of 
    stimuli and want them to have exactly the pixels you created (with no scaling).
    Unfortunately it is slower to draw than PatchStim and can lead to dropped frames.
    (to test this on your system try commenting out the beach.draw() command)
    
    PatchStim is more versatile - it uses opengl textures which allow for alpha 
    masks, arbitrary transforms of the image data in space (multiple cycles, 
    scale, rotation...) but for this you must specify the size in each dimension 
    (or it may well appear stretched).
"""

#create a window to draw in
myWin = visual.Window((800,800), monitor='testMonitor',allowGUI=False, color=(-1,-1,-1))

#INITIALISE SOME STIMULI
beach = visual.SimpleImageStim(myWin, 'beach.jpg', flipHoriz=True, pos=(0,1.50), units='deg')
faceRGB = visual.PatchStim(myWin,tex='face.jpg', mask=None,
    pos=(50,-20), 
    size=None,#will be the size of the original image in pixels
    units='pix', interpolate=True,
    autoLog=False)#this stim changes too much for autologging to be useful
print "original image size:", faceRGB.origSize
faceALPHA = visual.PatchStim(myWin,pos=(-0.7,-0.2),
    tex="sin",mask="face.jpg",
    color=[1.0,1.0,-1.0],
    size=(0.5,0.5), units="norm",
    autoLog=False)#this stim changes too much for autologging to be useful
    
message = visual.TextStim(myWin,pos=(-0.95,-0.95),
    text='[Esc] to quit', color='white', alignHoriz='left', alignVert='bottom')

trialClock = core.Clock()
t=lastFPSupdate=0
myWin.setRecordFrameIntervals()
while True:
    t=trialClock.getTime()
    beach.draw()
    #Patch stimuli can be manipulated on the fly
    faceRGB.setOri(1,'+')#advance ori by 1 degree
    faceRGB.draw()
    faceALPHA.setPhase(0.01,"+")#advance phase by 1/100th of a cycle
    faceALPHA.draw()
    
    #update fps every second
    if t-lastFPSupdate>1.0:
        lastFPS = myWin.fps()
        lastFPSupdate=t
        message.setText("%ifps, [Esc] to quit" %lastFPS)
    message.draw()

    myWin.flip()

    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
    event.clearEvents()
