#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of MovieStim

MovieStim opens a video file and displays it.

"""
from psychopy import visual, core, event, constants

# window to present the video
win = visual.Window((800, 600))

# create a new movie stimulus instance
mov = visual.MovieStim(win, 'default.mp4', size=(800, 600), flipVert=False,
                       flipHoriz=False, loop=False)
mov.play()
# print('orig movie size=%s' % mov.size)
# print('duration=%.2fs' % mov.duration)

# main loop
while mov.status != constants.FINISHED:
    mov.draw()
    win.flip()
    if event.getKeys('q'):
        break
    if event.getKeys('m'):
        mov.play()
        print('play')
    if event.getKeys('n'):
        mov.pause()
        print('pause')

    print(mov.status, constants.FINISHED)

mov.stop()
# clean up and exit
win.close()
core.quit()

# The contents of this file are in the public domain.
