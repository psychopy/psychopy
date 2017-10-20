#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo allows for automated testing of the sound latency on your system.
To use it you need a labjack (or adapt for a similar device) and a cable to
connect the earphones jack to the AIN0 (and GND) pins of the labjack.

(The PsychoPy team would be interested to hear how your measurements go)
"""

from __future__ import absolute_import, division, print_function

import psychopy
from psychopy import visual, core, event, sound
from labjack import u3
import numpy, sys, platform

# setup window (can use for visual pulses)
win = visual.Window([800, 800], monitor='testMonitor')
win.recordFrameIntervals = False
stim = visual.GratingStim(win, color=-1, sf=0)

sound.init(rate=48000, buffer=48)
print('Using %s(with %s) for sounds' %(sound.audioLib, sound.audioDriver))
timeWithLabjack = True
maxReps = 100

# setup labjack U3
ports = u3.U3()
ports.__del__ = ports.close  # try to autoclose the ports if script crashes

# get zero value of FIO6
startVal = ports.getFIOState(6)  # is FIO6 high or low?
print('FIO6 is at', startVal, end='')
print('AIN0 is at', ports.getAIN(0))
if timeWithLabjack:
    print('OS\tOSver\taudioAPI\tPsychoPy\trate\tbuffer\tmean\tsd\tmin\tmax')

snd = sound.Sound(1000, secs=0.1)
core.wait(2)  # give the system time to settle?
delays = []
nReps = 0
while True:  # run the repeats for this sound server
    if event.getKeys('q'):
        core.quit()
    nReps += 1
    # do this repeatedly for timing tests
    ports.setFIOState(4, 0)  # start FIO4 low

    # draw black square
    stim.draw()
    win.flip()

    if not timeWithLabjack:
        # wait for a key press
        if 'q' in event.waitKeys():
            break

    # set to white, flip window and raise level port FIO4
    stim.setColor(1)
    stim.draw()
    win.flip()

    startVal=ports.getAIN(0)
    # print('AIN0 is at', startVal)
    ports.setFIOState(4, 1)

    timer=core.Clock()
    snd.play()

    if timeWithLabjack:
        while abs(ports.getAIN(0)-startVal) < 0.1 and timer.getTime() < 1.0:
            pass
        t1 = timer.getTime() * 1000
        if timer.getTime() > 1.0:
            print('failed to detect sound on FIO6 (either inconsistent sound or needs to be louder)')
        # for n in range(5):
        #    core.wait(0.001)
        #    print('AIN0 now', ports.getAIN(0))
        sys.stdout.flush()
        delays.append(t1)
        core.wait(0.5)  # ensure sound has finished
    # set color back to black and set FIO4 to low again
    stim.setColor(-1)
    stim.draw()
    win.flip()
    ports.setFIOState(4, 0)  # set FIO4 to low again
    if nReps >= maxReps:
        break

if sys.platform == 'darwin':
    sysName = 'OSX'
    sysVer = platform.mac_ver()[0]
elif sys.platform == 'win32':
    sysName = 'win'
    sysVer = platform.win32_ver()[0]
elif sys.platform.startswith('linux'):
    sysName = 'linux_' + platform.dist()
    sysVer = platform.release()
else:
    sysName = sysVer = 'n/a'

audioLib = sound.audioLib
if audioLib == 'pyo':
    # for pyo we also want the undrelying driver (ASIO, windows etc)
    audioLib = "%s_%s" % (sound.audioLib, sound.audioDriver)
    rate = sound.pyoSndServer.getSamplingRate()
    buff_size = sound.pyoSndServer.getBufferSize()
else:
    rate = sound.pygame.mixer.get_init()[0]
    buff_size = 0

# print('OS\tOSver\tPsychoPy\trate\tbuffer\tmean\tsd\tmin\tmax')
if timeWithLabjack:
    print("%s\t%s\t%s\t%s" % (sysName, sysVer, audioLib, psychopy.__version__), end='')
    print("\t%i\t%i" % (rate, buff_size), end='')
    print("\t%.3f\t%.3f" % (numpy.mean(delays), numpy.std(delays)), end='')
    print("\t%.3f\t%.3f" % (numpy.min(delays), numpy.max(delays)), end='')

import pylab
pylab.plot(delays, 'o')
pylab.show()

win.close()
core.quit()

# The contents of this file are in the public domain.
