#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo using the new (beta) VlcMovieStim to play a video file. Path of video
needs to updated to point to a video you have. The demo closes automatically at
the end of the stream.

This requires:

1. VLC. Just install the standard VLC of the same bitness as Python for your OS.

    https://www.videolan.org/vlc/index.html

2. pip install python-vlc

"""

import os
from psychopy import visual, core, event

# get the video from the demo resources directory
videopath = r'jwpIntro.mp4'
videopath = os.path.join(os.getcwd(), videopath)
if not os.path.exists(videopath):
    raise RuntimeError("Video File could not be found:" + videopath)

# open a window to display the video
win = visual.Window([800, 800], fullscr=False)

# create text stim for instructions
keystext = "PRESS 'q' or 'escape' to Quit.\n"
keystext += "'s': Stop and restart\n"
keystext += "'p': Pause/unpause\n"
keystext += "'>': Seek forward 1 second\n"
keystext += "'<': Seek backward 1 second\n"
keystext += "'-': Decrease volume\n"
keystext += "'+': Increase volume"
text = visual.TextStim(win, keystext, pos=(0, -250), units='pix')

# Create your movie stim
mov = visual.VlcMovieStim(win, videopath,
    size=600,  # set as `None` to use the native video size
    pos=[0, 0],  # pos specifies the /center/ of the movie stim location
    flipVert=False,  # flip the video picture vertically
    flipHoriz=False,  # flip the video picture horizontally
    loop=False,  # replay the video when it reaches the end
    autoStart=True)  # start the video automatically when first drawn

# main loop, will exit automatically when the movie is finished
while not mov.isFinished:
    # Check for action keys.....
    for key in event.getKeys():
        if key in ['escape', 'q']:
            mov.stop()
            core.quit()
        elif key in ['s', ]:
            mov.replay()
        elif key in ['p', ]:
            # To pause the movie while it is playing ...
            if mov.isNotStarted or mov.isPaused:
                mov.play()
            elif mov.isPlaying:
                mov.pause()
        elif key == 'period':
            # To skip ahead 1 second in movie ...
            mov.fastForward(1.0)
        elif key == 'comma':
            # To skip back 1 second in movie ...
            mov.rewind(1.0)
        elif key == 'minus':
            # To decrease movie sound a bit (5%) ...
            mov.decreaseVolume(5)
        elif key == 'equal':
            # To increase movie sound a bit (5%) ...
            mov.increaseVolume(5)

    # draw elements
    mov.draw()  # movie frame
    text.draw()  # instruction text overlay
    win.flip()  # flip buffers to draw the content to the window

win.close()
core.quit()

# The contents of this file are in the public domain.
