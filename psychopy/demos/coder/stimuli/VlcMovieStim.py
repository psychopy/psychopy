#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo using the new (beta) VlcMovieStim to play a video file. Path of video
needs to updated to point to a video you have. 

This requires:

1. VLC. Just install the standard VLC of the same bitness as python
    for your OS.

    http://www.videolan.org/vlc/index.html

2. pip install python-vlc
"""

from __future__ import division

from psychopy import visual, core, event
import time, os

videopath = r'./jwpIntro.mov'
videopath = os.path.join(os.getcwd(), videopath)
if not os.path.exists(videopath):
    raise RuntimeError("Video File could not be found:" + videopath)

win = visual.Window([1024, 768])

keystext = "PRESS 'q' or 'escape' to Quit.\n"
keystext += "  #     's': Stop/restart Movie.\n"
keystext += "  #     'p': Pause/Unpause Movie.\n"
keystext += "  #     '>': Seek Forward 1 Second.\n"
keystext += "  #     '<': Seek Backward 1 Second.\n"
keystext += "  #     '-': Decrease Movie Volume.\n"
keystext += "  #     '+': Increase Movie Volume."

text = visual.TextStim(win, keystext, pos=(0, -250), units = 'pix')

# Create your movie stim.
mov = visual.VlcMovieStim(win, videopath,
    size=640,
    # pos specifies the /center/ of the movie stim location
    pos=[0, 100],
    flipVert=False, flipHoriz=False,
    loop=False)

# Start the movie stim by preparing it to play
shouldflip = mov.play()
while mov.status != visual.FINISHED:
    # Only flip when a new frame should be displayed. Can significantly reduce
    # CPU usage. This only makes sense if the movie is the only /dynamic/ stim
    # displayed.
    if shouldflip:
        # Movie has already been drawn , so just draw text stim and flip
        text.draw()
        win.flip()
    else:
        # Give the OS a break if a flip is not needed
        time.sleep(0.001)
    # Drawn movie stim again. Updating of movie stim frames as necessary
    # is handled internally.
    shouldflip = mov.draw()

    # Check for action keys.....
    for key in event.getKeys():
        if key in ['escape', 'q']:
            win.close()
            core.quit()
        elif key in ['s', ]:
            if mov.status in [visual.PLAYING, visual.PAUSED]:
                # To stop the movie being played.....
                mov.stop()
                # Clear screen of last displayed frame.
                win.flip()
                # When movie stops, clear screen of last displayed frame,
                # and display text stim only....
                text.draw()
                win.flip()
            else:
                # To replay a movie that was stopped.....
                mov.loadMovie(videopath)
                shouldflip = mov.play()
        elif key in ['p', ]:
            # To pause the movie while it is playing....
            if mov.status == visual.PLAYING:
                mov.pause()
            elif mov.status == visual.PAUSED:
                # To /unpause/ the movie if pause has been called....
                mov.play()
                text.draw()
                win.flip()
        elif key == 'period':
            # To skip ahead 1 second in movie.
            ntime = min(mov.getCurrentFrameTime() + 1.0, mov.duration)
            mov.seek(ntime)
        elif key == 'comma':
            # To skip back 1 second in movie ....
            ntime = max(mov.getCurrentFrameTime() - 1.0, 0.0)
            mov.seek(ntime)
        elif key == 'minus':
            # To decrease movie sound a bit ....
            cv = max(mov.getVolume() - 5, 0)
            mov.setVolume(cv)
        elif key == 'equal':
            # To increase movie sound a bit ....
            cv = mov.getVolume()
            cv = min(mov.getVolume() + 5, 100)
            mov.setVolume(cv)

win.close()
core.quit()

# The contents of this file are in the public domain.
