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
    autoStart=False,
    replayOnStop=True)

# print some information about the movie
print('orig movie size={}'.format(mov.frameSize))
print('orig movie duration={}'.format(mov.duration))

# instructions
instrText = "`z` Start/Resume\n`x` Pause\n`b` Restart\n`q` Stop and Close"
instr = visual.TextStim(win, instrText, pos=(0.0, -0.75))

# main loop
while mov.status != constants.FINISHED:
    # draw the movie
    mov.draw()
    # draw the instruction text
    instr.draw()
    # flip buffers so they appear on the window
    win.flip()

    # process keyboard input
    if event.getKeys('q'):   # quit
        break
    elif event.getKeys('z'):  # play/start
        mov.play()
    elif event.getKeys('x'):  # pause
        mov.pause()
    elif event.getKeys('b'):  # replay
        mov.replay()
    elif event.getKeys('n'):  # rewind 1 second
        mov.rewind(1)
    elif event.getKeys('m'):  # forward 1 second
        mov.fastForward(1)
    elif event.getKeys('a'):  # volume up 5%
        mov.volumeUp()
    elif event.getKeys('s'):  # volume down 5%
        mov.volumeDown()

# stop the movie, this frees resources too
mov.unload()  # unloads when `mov.status == constants.FINISHED`

# clean up and exit
win.close()
core.quit()

# The contents of this file are in the public domain.
