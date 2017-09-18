#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of class psychopy.visual.BufferImageStim()

- take a snapshot of a multi-item screen image
- save and draw as a BufferImageStim
- report speed of BufferImageStim to speed of drawing each item separately
"""

from __future__ import division
from __future__ import print_function

from builtins import str
from builtins import range
from psychopy import visual, event, core

# need a window and clock:
win = visual.Window(fullscr=False, monitor='testMonitor')
clock = core.Clock()

# first define a list of various slow, static stim
imageList = ['face.jpg', 'beach.jpg']
imageStim = visual.SimpleImageStim(win, imageList[0])
imageStim2 = visual.SimpleImageStim(win, imageList[1], pos=(.300, .20))
wordStim = visual.TextStim(win,
            text='Press < escape > to quit.\n\nThere should be no change after 3 seconds.\n\n' +
            'This is a text stim that is kinda verbose and long, so if it ' +
            'were actually really long it would take a while to render completely.',
            pos=(0, -.2))
stimlist = [imageStim, imageStim2, wordStim]

# Get and save a "screen shot" of everything in stimlist:
rect = (-1, 1, 1, -1)
t0 = clock.getTime()
screenshot = visual.BufferImageStim(win, stim=stimlist, rect=rect)
# rect is the screen rectangle to grab, (-1, 1, 1, -1) is whole-screen
# as a list of the edges: Left Top Right Bottom, in norm units.

captureTime = clock.getTime() - t0

instr_buffer = visual.TextStim(win, text='BufferImageStim', pos=(0, .8))
drawTimeBuffer = []  # accumulate draw times of the screenshot
for frameCounter in range(200):
    t0 = clock.getTime()
    screenshot.draw()  # draw the BufferImageStim, fast
    drawTimeBuffer.append(clock.getTime() - t0)
    instr_buffer.draw()
    win.flip()
    if len(event.getKeys(['escape'])):
        core.quit()

# Just for the demo: Time things when drawn individually:
instr_multi = visual.TextStim(win, text='TextStim and ImageStim', pos=(0, .8))
drawTimeMulti  = []  # draw times of the pieces, as drawn separately
for frameCounter in range(200):
    t0 = clock.getTime()
    for s in stimlist:
        s.draw()  # draw all individual stim, slow
    drawTimeMulti.append(clock.getTime() - t0)
    instr_multi.draw()
    win.flip()
    if len(event.getKeys(['escape'])):
        core.quit()

# Report timing:
firstFrameTime = drawTimeBuffer.pop(0)
bufferAvg = 1000. * sum(drawTimeBuffer) / len(drawTimeBuffer)
multiAvg = 1000. * sum(drawTimeMulti) / len(drawTimeMulti)
msg = "\nBufferImageStim\nrect=%s norm units, becomes %s pix"
print(msg % (str(rect), str(screenshot.size)))
print("initial set-up / screen capture: %.0fms total" % (1000. * captureTime))
print("first frame:    %.2fms (typically slow)" % (1000. * firstFrameTime))
msg = "BufferImage:    %.2fms avg, %.2fms max draw-time (%d frames)"
print(msg % (bufferAvg, max(drawTimeBuffer) * 1000., len(drawTimeBuffer)))
msg = "Text & Image:   %.2fms avg, %.2fms max draw-time"
print(msg % (multiAvg, max(drawTimeMulti) * 1000.))

win.close()
core.quit()

# The contents of this file are in the public domain.
