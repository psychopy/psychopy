#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for playing videos in PsychoPy using FFMPEG as the backend.
"""

import os
from psychopy import visual, core, event

# get the video from the demo resources directory
videopath = r'/Users/mdc/Desktop/jwpIntro.mp4'
videopath = os.path.join(os.getcwd(), videopath)
if not os.path.exists(videopath):
    raise RuntimeError("Video File could not be found:" + videopath)

# open a window to display the video
win = visual.Window([800, 800])

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
mov = visual.FFMovieStim(
    win,
    videopath,
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
        # elif key == 'period':
        #     # To skip ahead 1 second in movie ...
        #     mov.fastForward(1.0)
        # elif key == 'comma':
        #     # To skip back 1 second in movie ...
        #     mov.rewind(1.0)
        # elif key == 'minus':
        #     # To decrease movie sound a bit (5%) ...
        #     mov.decreaseVolume(5)
        # elif key == 'equal':
        #     # To increase movie sound a bit (5%) ...
        #     mov.increaseVolume(5)

    # draw elements
    mov.draw()  # movie frame
    text.draw()  # instruction text overlay
    win.flip()  # flip buffers to draw the content to the window

win.close()
core.quit()

# The contents of this file are in the public domain.
