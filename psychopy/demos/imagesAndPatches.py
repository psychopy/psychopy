#! /usr/local/bin/python2.5
from psychopy import core, visual, event

#create a window to draw in
myWin = visual.Window((600,600), monitor='testMonitor',allowGUI=False, rgb=(-1,-1,-1))

"""There are two options for drawing image-based stimuli in PsychoPy:
    
    SimpleImageStim is ideal if you don't need to draw a large number of 
    stimuli and want them to have exactly the pixels.
    
    PatchStim is more versatile - it uses opengl textures which allow for alpha 
    masks, arbitrary transforms of the image data in space (multiple cycles, 
    scale, rotation...) but for this you must specify the size in each dimension 
    (or it may well appear stretched).
"""
#INITIALISE SOME STIMULI
beach = visual.SimpleImageStim(myWin, 'beach.jpg', pos=(0,1.50), units='deg')
faceRGB = visual.PatchStim(myWin,tex='face.jpg', mask=None,
    pos=(0.5,-0.4), size=(1.0,1.0), sf=(1.0, 1.0))
faceALPHA = visual.PatchStim(myWin,pos=(-0.7,-0.2),
    tex="sin",mask="face.jpg",
    rgb=[1.0,1.0,-1.0],
    size=(0.5,0.5), sf=1.0, units="norm")
    
message = visual.TextStim(myWin,pos=(-0.95,-0.95),
    text='[Esc] to quit', rgb=1, alignHoriz='left', alignVert='bottom')

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
