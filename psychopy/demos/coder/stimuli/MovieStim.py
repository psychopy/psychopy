#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of MovieStim

MovieStim opens a video file and displays it on a window.

"""
from psychopy import visual, core, event, constants

# window to present the video
win = visual.Window((800, 600), fullscr=False)

# create a new movie stimulus instance
mov = visual.MovieStim(
    win,
    'default.mp4',    # path to video file
    size=(256, 256),
    flipVert=False,
    flipHoriz=False,
    loop=False,
    noAudio=False,
    volume=0.1,
    autoStart=False)

# print some information about the movie
print('orig movie size={}'.format(mov.frameSize))
print('orig movie duration={}'.format(mov.duration))

# instructions
instrText = "`r` Play/Resume\n`p` Pause\n`s` Stop\n`q` Stop and Close"
instr = visual.TextStim(win, instrText, pos=(0.0, -0.75))

# main loop, exit when the status is finished
while not mov.isFinished:
    # draw the movie
    mov.draw()
    # draw the instruction text
    instr.draw()
    # flip buffers so they appear on the window
    win.flip()

    # process keyboard input
    if event.getKeys('q'):   # quit
        break
    elif event.getKeys('r'):  # play/start
        mov.play()
    elif event.getKeys('p'):  # pause
        mov.pause()
    elif event.getKeys('s'):  # stop the movie
        mov.stop()

# stop the movie, this frees resources too
mov.unload()  # unloads when `mov.status == constants.FINISHED`

# clean up and exit
win.close()
core.quit()

# The contents of this file are in the public domain.
