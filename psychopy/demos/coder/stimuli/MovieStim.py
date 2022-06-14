#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of MovieStim

MovieStim opens a video file and displays it.

"""
from psychopy import visual, core, event, constants

# window to present the video
win = visual.Window((800, 600), fullscr=False)

# create a new movie stimulus instance
mov = visual.MovieStim(win, 'default.mp4', size=(256, 256), flipVert=False,
                       flipHoriz=False, loop=False)

# print some information about the movie
print('orig movie size={}'.format(mov.frameSize))

# instructions
instrText = "`s` Start/Resume\n`p` Pause\n`r` Restart\n`q` Stop and Close"
instr = visual.TextStim(win, instrText, pos=(0.0, -0.75))

# start playback
mov.pause()  # start paused

# main loop
while mov.status != constants.FINISHED:
    mov.draw()
    instr.draw()
    win.flip()
    if event.getKeys('q'):   # quit
        break
    elif event.getKeys('s'):  # play/start
        mov.play()
    elif event.getKeys('p'):  # pause
        mov.pause()
    elif event.getKeys('r'):  # restart/replay
        mov.replay()

mov.stop()
# clean up and exit
win.close()
core.quit()

# The contents of this file are in the public domain.
