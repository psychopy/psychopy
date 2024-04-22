#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import locale_setup, visual, core
import numpy as np
from psychopy.hardware import keyboard
from psychopy import misc


def createPalette(size):
    """
    Creates the color palette array in HSV and returns as RGB
    """
    # Create array 
    hsv = np.ones([size,size,3], dtype=float)
    
    # Set hue
    hsv[:,:,0] = np.linspace(0,360, size, endpoint=False)
    
    # Set saturation
    for i in range(size):
        hsv[:,i, 1] = np.linspace(0, 1, size, endpoint=False)
    
    # Convert to RGB
    rgb = misc.hsv2rgb(hsv)

    # Make in range 0:1 for image stim
    rgb[:][:][:] = (rgb[:][:][:] + 1) / 2
    return rgb
 
def createValue(size):
    """
    Creates the value palette array in HSV and returns as RGB
    """
    # Create array 
    hsv = np.zeros([20,size,3], dtype=float)
    # Set value
    hsv[:,:,2] = np.linspace(0,1, size, endpoint=False)
    # Convert to RGB
    rgb = misc.hsv2rgb(hsv)

    # Make in range 0:1 for image stim
    rgb[:][:][:] =  (rgb[:][:][:] + 1) / 2
    return rgb
    

# Setup the Window
win = visual.Window(size=[1920, 1080], fullscr=False, units='height')

colorPalette = visual.ImageStim(win=win,name='colorPalette', units='pix', 
                                image=None, mask=None,
                                texRes=64, depth=0.0)
    
valuePalette = visual.ImageStim(win=win, name='valuePalette', units='pix', 
                                pos=(0, -250), depth=-1.0)
    
hueSlider = visual.Slider(win=win, name='hueSlider',
                          size=(.37, .02), pos=(0, 0.2),
                          labels=None, ticks=(0, 360), style=['rating'])
    
satSlider = visual.Slider(win=win, name='satSlider',
                          size=(.02, .37), pos=(0.2, 0),
                          labels=None, ticks=(0, 1), style=['rating'])
    
valSlider = visual.Slider(win=win, name='valSlider',
                          size=(.37, .02), pos=(0, -0.25),
                          labels=None, ticks=(0,1), style=['rating'])
    
visualFeedback = visual.Rect(win=win, name='visualFeedback',
                             width=(0.15, 0.15)[0], height=(0.15, 0.15)[1],
                             pos=(0, 0.35),fillColor=[0,0,0], colorSpace='hsv',
                             depth=-6.0)

hsvText = visual.TextStim(win=win, name='hsvText',
                          text=None, font='Arial',
                          pos=(.4, 0), height=0.03)

instText = visual.TextStim(win=win, name='instText',
                           text=("Use the sliders to change:\n---hue (top)\n---"
                                "saturation (right)\n---value (bottom)"),
                           font='Arial',
                           pos=(-.3, 0), height=0.03, wrapWidth=.4,
                           alignText='left', anchorHoriz='right')

quitText = visual.TextStim(win=win, name='quitText',
                           text='Press escape to quit to continue',
                           font='Arial',
                           pos=(0, -.35), height=0.025, depth=-8.0,
                           wrapWidth=.4)


paletteSize = 400  # in pixels
valRGB = createValue(paletteSize) 
colPalRGB = createPalette(paletteSize)

hueSlider.reset()
satSlider.reset()
valSlider.reset()

colorPalette.setSize([paletteSize,paletteSize])
colorPalette.setImage(colPalRGB)
valuePalette.setSize((paletteSize, 20))
valuePalette.setImage(valRGB)

key_resp = keyboard.Keyboard()

while True:
    
    h = hueSlider.getRating() or 0
    s = satSlider.getRating() or 0
    v = valSlider.getRating() or 0.5
    visualFeedback.fillColor = [h,s,v]
    hsvText.text = "Hue: {h:.0f}\nSat: {s:.2f}\nVal: {v:.2f}".format(h=h, s=s, v=v)

    colorPalette.draw()
    valuePalette.draw() 
    hueSlider.draw()
    satSlider.draw()
    valSlider.draw()
    visualFeedback.draw()
    instText.draw()
    hsvText.draw()
    quitText.draw()
    
    theseKeys = key_resp.getKeys(keyList=['escape'], waitRelease=False)
    if len(theseKeys):
        theseKeys = theseKeys[0]  # at least one key was pressed
        
        # check for quit:
        if "escape" == theseKeys:
            win.close()
            core.quit()
            
    win.flip()
