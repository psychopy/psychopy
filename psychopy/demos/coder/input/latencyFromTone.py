#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
demo to illustrate and test microphone.AdvAudioCapture, and also permit
external latency testing (e.g., BlackBox Toolkit) by providing visual-tone synchrony

key lines: 29, 50, 61: mic = microphone.AdvAudioCapture(), mic.record(), mic.getOnset()
"""

from __future__ import absolute_import, division, print_function

from builtins import range
from psychopy import microphone, sound, core, visual, event
from matplotlib import pyplot
import numpy as np
import os

buffer_size = 128  # smaller = short play latency, but higher chance of choppy sound playback
rate = 48000  # needs to be 40000 or higher
sound.init(buffer=buffer_size, rate=rate)

def plotYX(yaxis, xaxis, description=''):
    pyplot.plot(xaxis, yaxis)
    pyplot.grid(True)
    pyplot.title(description)
    pyplot.ylabel('[std %.1f]' % np.std(yaxis))
    pyplot.draw()
    pyplot.show()

# initial set up:
win = visual.Window(fullscr=False, units='height')
circle = visual.Circle(win, 0.25, fillColor=1, edges=64)
microphone.switchOn()
mic = microphone.AdvAudioCapture()

# identify the hardware microphone in use:
names, idx = sound.backend.get_input_devices()
inp = sound.backend.pyo.pa_get_default_input()
msg = 'Speaker vol > 0\nAny key to start...\n\n"%s"' % names[idx.index(inp)]

instr = visual.TextStim(win, msg, color=-1, height=0.05)
text = visual.TextStim(win, "Any key to see\nthe recording", color=-1, height=0.05)
msg2 = visual.TextStim(win, "Close plot window to continue", color=-1, height=0.05)
circle.draw()
instr.draw()
win.flip()
if 'escape' in event.waitKeys():
    core.quit()
win.flip()

onsets = []
rec_duration = 0.5
print('marker start, offset (within the saved recording):')
for i in range(10):
    core.wait(0.5, 0)

    filename = mic.record(rec_duration)  # start recording and return immediately
    # at this point, python thinks ~1ms has elapsed since the recording started
    # but the file contains more

    # wait for the recording to finish:
    circle.draw()
    text.draw()
    win.flip()
    while mic.recorder.running:
        core.wait(.01, 0)

    # When in the file did the onset tone start and stop?
    onset, offset = mic.getMarkerOnset(chunk=64, secs=0.2)  # increase secs if miss the markers
    onsets.append(onset)

    # display options:
    text.draw()
    win.flip()
    print("%.3f %.3f" % (onset, offset))
    if len(event.getKeys(['escape'])):
        core.quit()
    if len(event.getKeys()):
        msg2.draw()
        win.flip()
        data, sampleRate = microphone.readWavFile(filename)
        plotYX(data, list(range(len(data))), "time domain @ %iHz" % sampleRate)
        mag, freqV = microphone.getDft(data, sampleRate)
        plotYX(mag, freqV, "frequency domain (marker at %i Hz)" % mic.getMarkerInfo()[0])

    # no need to keep the recorded file:
    os.unlink(filename)

print("\nmarker onset = %.3fs %.3f (mean SD), relative to start of file" % (np.mean(onsets), np.std(onsets)))

win.close()
core.quit()

# The contents of this file are in the public domain.
