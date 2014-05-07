#!/usr/bin/env python2
"""This script demonstrates the use of the ElementArrayStim, a highly optimised stimulus for generating 
arrays of similar (but not identical) elements, such as in global form arrays or random dot stimuli.

Elements must have the same basic texture and mask, but can differ in any other way (ori, sf, rgb...).

This is a more complex demo, using numpy arrays to manipulate stimulus characteristics. Don't use
for-loops for a large array of stimuli like this.

see also the starField demo
"""

from psychopy import visual, core, event
from psychopy.tools.coordinatetools import cart2pol
import numpy #for maths on arrays
from numpy.random import random, shuffle #we only need these two commands from this lib
win = visual.Window([1024,768], units='pix', monitor='testMonitor')

N=500
fieldSize = 500
elemSize = 40
coherence=0.5

#build a standard (but dynamic!) global form stimulus
globForm = visual.ElementArrayStim(win, nElements=N,sizes=elemSize,sfs=3,
                                                    xys = random([N,2])*fieldSize-fieldSize/2.0,
                                                    colors=[180,1,1],colorSpace='hsv') 
    
#calculate the orientations for global form stimulus
def makeCoherentOris(XYs, coherence, formAngle):
    nNew = XYs.shape[0]#length along the first dimension
    newOris = random(nNew)*180 #create a random array 0:180
    #select some elements to be coherent
    possibleIndices = range(nNew)#create an array of indices...
    shuffle(possibleIndices) #...shuffle it'in-place' (without creating a new array)...
    coherentIndices = possibleIndices[0:int(nNew*coherence)]#...and take first nnn elements
    #set the ori of the coherent elements
    theta, radius = cart2pol(XYs[:,0], XYs[:,1]) #get polar coordinates for elements
    newOris[coherentIndices] = formAngle-theta[coherentIndices]
    return newOris
    
globForm.oris = makeCoherentOris(globForm.xys, coherence, 45)

#let's give each element a life of 10 frames and give it a new position after that
lives = random(N)*10 #this will be the current life of each element
while True:
    #take a copy of the current xy and ori values
    newXYs = globForm.xys
    newOris = globForm.oris
    #find the dead elemnts and reset their life
    deadElements = (lives>10)
    lives[deadElements]=0
    #for the dead elements update the xy and ori
    newXYs[deadElements,:] = random(newXYs[deadElements,:].shape)*fieldSize-fieldSize/2.0#random array same shape as dead elements
    new = makeCoherentOris(newXYs[deadElements,:], coherence, 45)#for new elements we still want same % coherent
    newOris[deadElements] = new
    #update the oris and xys of the new elements
    globForm.xys = newXYs
    globForm.pris = newOris
    
    globForm.draw()
    
    win.flip() 
    lives = lives+1

    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            win.close()
            core.quit()
    event.clearEvents('mouse')#only really needed for pygame windows
    
