#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo using the new (beta) VlcMovieStim to play a video file. Path of video
needs to updated to point to a video you have. 

This requires:

1. VLC. Just install the standard VLC of the same bitness as Python for your OS.

    http://www.videolan.org/vlc/index.html

2. pip install python-vlc

"""

from __future__ import division

from psychopy import visual, core, event, constants
import time, os

videopath = r'./jwpIntro.mov'
videopath = os.path.join(os.getcwd(), videopath)
if not os.path.exists(videopath):
    raise RuntimeError("Video File could not be found:" + videopath)

win = visual.Window([800, 800], fullscr=False)

keystext = "PRESS 'q' or 'escape' to Quit.\n"
keystext += "'s': Stop and restart\n"
keystext += "'p': Pause/unpause\n"
keystext += "'>': Seek forward 1 second\n"
keystext += "'<': Seek backward 1 second\n"
keystext += "'-': Decrease volume.\n"
keystext += "'+': Increase volume"

text = visual.TextStim(win, keystext, pos=(0, -250), units='pix')

# Create your movie stim.
mov = visual.VlcMovieStim(win, videopath,
    size=600,
    # pos specifies the /center/ of the movie stim location
    pos=[0, 0],
    flipVert=False, flipHoriz=False,
    loop=False, autoStart=True)


while not mov.isFinished:
    # Check for action keys.....
    for key in event.getKeys():
        if key in ['escape', 'q']:
            mov.stop()
            core.quit()
        elif key in ['s', ]:
            mov.replay()
        elif key in ['p', ]:
            # To pause the movie while it is playing....
            if mov.isNotStarted or mov.isPaused:
                mov.play()
            elif mov.isPlaying:
                mov.pause()
        elif key == 'period':
            # To skip ahead 1 second in movie.
            mov.fastForward(1.0)
        elif key == 'comma':
            # To skip back 1 second in movie ....
            mov.rewind(1.0)
        elif key == 'minus':
            # To decrease movie sound a bit ....
            mov.decreaseVolume(5)
        elif key == 'equal':
            # To increase movie sound a bit ....
            mov.increaseVolume(5)

    # Only flip when a new frame should be displayed. Can significantly reduce
    # CPU usage. This only makes sense if the movie is the only /dynamic/ stim
    # displayed.
    mov.draw()
    text.draw()
    win.flip()


win.close()
core.quit()

# The contents of this file are in the public domain.
