#!/usr/bin/env python2

"""Demo of class psychopy.visual.BufferImageStim():
    - take a snapshot of a multi-item screen image
    - save and draw as a BufferImageStim
    - report speed of BufferImageStim to speed of drawing each item separately
"""

from psychopy import visual, event, core
import os

# need a window and clock:
win = visual.Window(fullscr=False, monitor='testMonitor')
myClock = core.Clock()

# first define a list of various slow, static stim
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']]
imageList = imageList[:2]
imageStim = visual.SimpleImageStim(win, imageList[0])
imageStim2 = visual.SimpleImageStim(win, imageList[1], pos=(300,20))
wordStim = visual.TextStim(win,
            text='Press <escape> to quit.\n\nThere should be no change after 3 seconds.\n\n' +
            'This is a text stim that is kinda verbose and long, so if it ' +
            'were actually really long it would take a while to render completely.',
            pos=(0,-.2))

# Get and save a "screen shot" of everything in stimlist:
stimlist = [imageStim, imageStim2, wordStim]
t0 = myClock.getTime()
rect=(-1,1,1,-1)
screenshot = visual.BufferImageStim(win, stim=stimlist, rect=rect)
    # rect is the screen rectangle to grab, (-1,1,1,-1) is whole-screen
    # as a list of the edges: Left Top Right Bottom, in norm units.
captureTime = myClock.getTime() - t0

instr_buffer = visual.TextStim(win, text='This is a BufferImageStim', pos=(0,.7))
drawTimeBuffer = [] # accumulate draw times of the screenshot / BufferImageStim
for frameCounter in xrange(200):
    t3 = myClock.getTime()
    screenshot.draw()  # draw the BufferImageStim, fast
    drawTimeBuffer.append(myClock.getTime() - t3)
    instr_buffer.draw()
    win.flip()
    if len(event.getKeys(['escape'])): core.quit()

# Just for the demo: Time things when drawn individually:
instr_multi = visual.TextStim(win, text='This is multiple TextStim and ImageStim',pos=(0,.7))
drawTimeMulti  = [] # draw times of the pieces, as drawn separately
for frameCounter in xrange(200):
    t3 = myClock.getTime()
    [s.draw() for s in stimlist]  # draw all individual stim, slow
    drawTimeMulti.append(myClock.getTime() - t3)
    instr_multi.draw()
    win.flip()
    if len(event.getKeys(['escape'])): core.quit()

# Report timing:
firstFrameTime = drawTimeBuffer.pop(0)
bufferAvg = 1000. * sum(drawTimeBuffer) / len(drawTimeBuffer)
multiAvg = 1000. * sum(drawTimeMulti) / len(drawTimeMulti)
print "\nBufferImageStim\nrect=%s norm units, becomes %s pix" % \
        (str(rect), str(screenshot.size))
print "initial set-up: %.0fms total" % (1000. * captureTime)
print "first frame:     %.2fms (transfer to graphics card?)" % (1000. * firstFrameTime)
print "BufferImage:    %.2fms avg, %.2fms max draw-time (%d frames)" % \
        (bufferAvg, max(drawTimeBuffer) * 1000., len(drawTimeBuffer))
print "individual:       %.2fms avg, %.2fms max draw-time" % \
        (multiAvg, max(drawTimeMulti) * 1000.)
