#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo for using labjack DAC devices

See also
    http: //labjack.com/support/labjackpython
but note that the version shipped with standalone PsychoPy
has u3 (and others below an umbrella called labjack) so the import
line is slightly different to the documentation on LabJack's website
"""

from psychopy import visual, core, event, sound
try:
    from labjack import u3
except ImportError:
    import u3

# sound.setAudioAPI('pyaudio')

win = visual.Window([800, 800])
stim = visual.GratingStim(win, color=-1, sf=0)
snd = sound.Sound(880)
print(snd)
# setup labjack U3
ports = u3.U3()
FIO4 = 6004  # the address of line FIO4

while True:
    # do this repeatedly for timing tests
    ports.writeRegister(FIO4, 0)  # start low

    # draw black square
    stim.draw()
    win.flip()

    # wait for a key press
    if 'q' in event.waitKeys():
        break

    # set to white, flip window and raise level port FIO4
    stim.setColor(1)
    stim.draw()
    win.flip()
    ports.writeRegister(FIO4, 1)
    snd.play()
    for frameN in range(4):
        stim.draw()
        win.flip()

    # set color back to black and set FIO4 to low again
    stim.setColor(-1)
    stim.draw()
    win.flip()
    ports.writeRegister(FIO4, 0)

win.close()
core.quit()

# The contents of this file are in the public domain.
