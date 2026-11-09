#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of MovieStim

MovieStim opens a video file and displays it on a window. A slider below the
movie shows the current playback position. Click or drag the slider to seek to
a different position in the movie.

"""
from psychopy import visual, core, event, constants
from psychopy.hardware import keyboard


def formatTime(seconds):
    """Format a time in seconds as `m:ss`."""
    minutes, seconds = divmod(int(max(0.0, seconds)), 60)
    return '{}:{:02d}'.format(minutes, seconds)


# window to present the video
win = visual.Window((800, 600), fullscr=False)

# keyboard to listen for keys
kb = keyboard.Keyboard()

# mouse to check if the button is held down on the slider
mouse = event.Mouse(win=win)

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

# slider to show the playback position, it spans the duration of the movie
seekBar = visual.Slider(
    win,
    ticks=(0.0, mov.duration),
    labels=(formatTime(0.0), formatTime(mov.duration)),
    startValue=0.0,
    pos=(0.0, -0.6),
    size=(1.2, 0.05),
    units='norm',
    style='slider',
    granularity=0,  # continuous, so we can seek to any position
    labelHeight=0.06)

# text showing the current playback position
timeText = visual.TextStim(
    win, '', pos=(0.8, -0.6), height=0.06, units='norm')

# instructions
instrText = ("`r` Play/Resume\n`p` Pause\n`s` Stop\n`q` Stop and Close\n"
             "Click or drag the slider to seek")
instr = visual.TextStim(
    win, instrText, pos=(0.0, 0.7), height=0.06, units='norm')

# The slider records a rating when the mouse button is released after clicking
# or dragging the marker. Track how many it has recorded so we know when the
# user has picked a new position to seek to.
nRatings = len(seekBar.getHistory())
wasPressed = False

# main loop, exit when the user presses `q`
while True:
    pressed = mouse.getPressed()[0]

    # Move the marker to the current playback position, but not while the mouse
    # button is down (or on the frame it's released), as the user may be
    # dragging the marker and the slider needs the position they dropped it at.
    if not pressed and not wasPressed:
        seekBar.markerPos = mov.movieTime
    wasPressed = pressed

    # draw the movie
    mov.draw()
    # draw the slider, this also checks for mouse responses on it
    seekBar.draw()
    # show the current position, or where the marker is while dragging it
    timeText.text = '{} / {}'.format(
        formatTime(seekBar.markerPos), formatTime(mov.duration))
    timeText.draw()
    # draw the instruction text
    instr.draw()
    # flip buffers so they appear on the window
    win.flip()

    # seek if the user has picked a new position on the slider
    history = seekBar.getHistory()
    if len(history) > nRatings:
        nRatings = len(history)
        mov.seek(seekBar.getRating())

    # process keyboard input
    if kb.getKeys('q'):   # quit
        break
    elif kb.getKeys('r'):  # play/start
        mov.play()
    elif kb.getKeys('p'):  # pause
        mov.pause()
    elif kb.getKeys('s'):  # stop the movie
        mov.stop()

# stop the movie, this frees resources too
mov.unload()  # unloads when `mov.status == constants.FINISHED`

# clean up and exit
win.close()
core.quit()

# The contents of this file are in the public domain.
