#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo using the new (beta) MovieStim2 to play a video file. Path of video
needs to updated to point to a video you have. MovieStim2 does /not/ require
avbin to be installed.

Movie2 does require:
1. Python OpenCV package (so openCV libs and the cv2 python interface).
    * For Windows, a binary installer is available at
        http: //www.lfd.uci.edu/~gohlke/pythonlibs/  # opencv
    * For Linux, it is available via whatever package manager you use.
    * For OSX, ..... ?
2. VLC application. The architeceture of this needs to match your psychopy/python installation 64/32 bit
    whether or not your *operating system* is 64/32 bit
    http: //www.videolan.org/vlc/index.html
"""

from psychopy import visual, core, event, constants
import time, os

videopath = r'./jwpIntro.mp4'
videopath = os.path.join(os.getcwd(), videopath)
if not os.path.exists(videopath):
    raise RuntimeError("Video File could not be found:" + videopath)

win = visual.Window([1024, 768])

# Create your movie stim.
mov = visual.MovieStim2(win, videopath,
    size=640,
    # pos specifies the /center/ of the movie stim location
    pos=[0, 100],
    flipVert=False, flipHoriz=False,
    loop=False)

keystext = "PRESS 'q' or 'escape' to Quit.\n"
keystext += "  #     's': Stop/restart Movie.\n"
keystext += "  #     'p': Pause/Unpause Movie.\n"
keystext += "  #     '>': Seek Forward 1 Second.\n"
keystext += "  #     '<': Seek Backward 1 Second.\n"
keystext += "  #     '-': Decrease Movie Volume.\n"
keystext += "  #     '+': Increase Movie Volume."
text = visual.TextStim(win, keystext, pos=(0, -250), units = 'pix')

# Start the movie stim by preparing it to play
shouldflip = mov.play()
while mov.status != constants.FINISHED:
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
            if mov.status in [constants.PLAYING, constants.PAUSED]:
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
            if mov.status == constants.PLAYING:
                mov.pause()
            elif mov.status == constants.PAUSED:
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
