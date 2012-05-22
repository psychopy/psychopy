#!/usr/bin/env python

"""
bufferImageStim.py

illustrates using class psychopy.visual.BufferImageStim(): 
- take a snapshot of a static, multi-item screen image (eg, graphics + text)
- save as a ImageStim-like image (BufferImageStim) for later fast drawing
- report timing stats for using a fullscreen BufferImageStim()
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import os

# need a win, as always:
myWin = visual.Window(fullscr=False, monitor='testMonitor')

# first compose your screen-shot: draw as many slow, static "still-life" stim
# as you want to the back buffer
myWin.clearBuffer() # clear the back buffer for drawing

# find a couple images in the demo directory, and display
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']]
imageList = imageList[:2]
imageStim = visual.SimpleImageStim(myWin, imageList[0])
imageStim.draw()
imageStim2 = visual.SimpleImageStim(myWin, imageList[1], pos=(300,20))
imageStim2.draw()
wordStim = visual.TextStim(myWin,
            text='Press any key to quit.\n\nThis is a text stim that is kinda verbose and long, so if it ' +
            'were actually really long it would take a while to render completely.',
            pos=(0,-.3))
wordStim.draw()

rect = [-1,1,1,-1] 
    # rect is what rectangle to grab, here whole-screen (same as default).
    # rect is a list of the edges: Left Top Right Bottom, norm units; try [-.5,.5,.5,-.5]
    # No need to be symmetrical, but it works better for the demo.
    # NB. If you change the rect and there was flickering on screen during the demo,
    # it was likely due to alternating between drawing a partial screenshot
    # interleaved with drawing all stimuli that went into it (only done for timing purposes).
    # Such flicker is NOT intrinsic to BufferImageStim.
    # In general, you do need to ensure that you
    # take a snapshot of everything you want, which might not be whole-screen.

myClock = core.Clock()
t0 = myClock.getTime()

# and take a screen shot, from the back buffer by default:
screenshot = visual.BufferImageStim(myWin, rect=rect)
t1 = myClock.getTime() - t0 # record set-up time

drawTimeSingle = [] # accumulate draw times of the BufferImageStim
drawTimeMulti  = [] # draw times of the pieces, as drawn separately (slowly)
frameCounter = 0
event.clearEvents()
while True:
    if len(event.getKeys()): break
    # screenshot.draw()
    # myWin.flip()
    # the above 3 lines do a lot, the rest is just timing and moving text
    
    # just for timing: alternate what is drawn to see timing differences
    if frameCounter % 2 == 0: 
        t3 = myClock.getTime()
        screenshot.draw() # actually draw the BufferImageStim
        drawTimeSingle.append(myClock.getTime() - t3)
    else:
        t3 = myClock.getTime()
        imageStim.draw() # draw the three separate stimuli
        imageStim2.draw()
        wordStim.draw()
        drawTimeMulti.append(myClock.getTime() - t3)
    frameCounter += 1
    
    myWin.flip()
    
# report timing in ms:
first = drawTimeSingle.pop(0)
multiAvg = 1000. * sum(drawTimeMulti) / len(drawTimeMulti)
singleAvg = 1000. * sum(drawTimeSingle) / len(drawTimeSingle)
print "\nBufferImageStim\nrect=[%.2f, %.2f, %.2f, %.2f] norm units, becomes" % \
        (rect[0], rect[1], rect[2], rect[3]), screenshot.size, 'pix'
print "initial set-up: %.0fms total\n    capture time = %.1fms" % \
        (1000. * (t1 + first), 1000. * t1)
print "    first frame = %.2fms (transfer to graphics card?)" % (1000. * first)
print "draw time %d frames: %.2fms avg, %.2fms max" % \
        (len(drawTimeSingle), singleAvg, max(drawTimeSingle) * 1000.)
print "    (vs. draw as 3 non-ImageStim = %.2fms avg, %.2fms max)" % \
        ( multiAvg, max(drawTimeMulti) * 1000.)

    