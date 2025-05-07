#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core
"""
Text rendering has changed a lot (for the better) under pyglet. This
script shows you the new way to specify fonts.
"""
#create a window to draw in
myWin = visual.Window((800.0,800.0),allowGUI=False,winType='pyglet',
            monitor='testMonitor', units ='deg', screen=0)
myWin.setRecordFrameIntervals()
#choose some fonts. If a list is provided, the first font found will be used.
fancy = ['Monotype Corsiva', 'Palace Script MT', 'Edwardian Script ITC']
sans = ['Gill Sans MT', 'Arial','Helvetica','Verdana'] #use the first font found on this list
serif = ['Times','Times New Roman'] #use the first font found on this list
comic = 'Comic Sans MS' #note the full name of the font - the short name won't work

#INITIALISE SOME STIMULI
rotating = visual.TextStim(myWin,text="Fonts \nrotate!",pos=(-5, -5),#and can have line breaks
                        color=[-1.0,-1,1],
                        units='deg',
                        ori=0, height = 2.0,
                        font=comic)
unicodeStuff = visual.TextStim(myWin,
                        text = u"unicode (eg \u03A8 \u040A \u03A3)",#you can find the unicode character value from MS Word 'insert symbol'
                        color='black',  font=serif,pos=(0,3), wrapWidth=20.0,
                        height = 2)
psychopyTxt = visual.TextStim(myWin, color='#FFFFFF',
                        text = u"PsychoPy \u00A9Jon Peirce",
                        units='norm', height=0.2,
                        pos=[0.95, 0.95],
                        alignText='right', anchorHoriz='right',
                        alignTextVert='top', anchorVert='top',
                        font=fancy)
longSentence = visual.TextStim(myWin,
                        text = u"Very long sentences can wrap", wrapWidth=0.8,
                        units='norm', height=0.15,color='DarkSlateBlue',
                        pos=[0.95, -0.95],
                        alignText='left', anchorHoriz='right',
                        anchorVert='bottom')
trialClock = core.Clock()
t=lastFPSupdate=0;
while t<20:#quits after 20 secs
    t=trialClock.getTime()

    rotating.setOri(1,"+")
    rotating.draw()

    unicodeStuff.draw()
    longSentence.draw()

    psychopyTxt.draw()

    myWin.flip()
