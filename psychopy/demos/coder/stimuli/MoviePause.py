#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of pausing during playback of MovieStim3

Different systems have different sets of codecs.
avbin (which PsychoPy uses to load movies) seems not to load compressed audio on all systems.
To create a movie that will play on all systems I would recommend using the format:
    video: H.264 compressed,
    audio: Linear PCM
"""

from __future__ import division
from __future__ import print_function

from builtins import str
from builtins import range
from psychopy import visual, core

win = visual.Window((800, 600))
mov = visual.MovieStim3(win, 'jwpIntro.mov', size=(320, 240),
    flipVert=False, flipHoriz=False)

print('orig movie size=' + str(mov.size))
print('duration=%.2fs' % mov.duration)
globalClock = core.Clock()

# play 100 frames normally
for frameN in range(100):
    mov.draw()
    win.flip()

# pause stops sound and prevents frame from advancing
mov.pause()
for frameN in range(100):
    mov.draw()
    win.flip()

# frame advance and audio continue
mov.play()
while globalClock.getTime() < (mov.duration + 1.0):
    mov.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
