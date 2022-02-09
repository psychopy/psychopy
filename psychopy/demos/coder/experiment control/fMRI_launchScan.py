#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo illustrates using hardware.emulator.launchScan() to either start a
real scan, or emulate sync pulses. Emulation is to allow debugging script timing
offline, without requiring a scanner (or a hardware sync pulse generator).
"""

# Author: Jeremy R. Gray

from psychopy import visual, event, core, gui
from psychopy.hardware.emulator import launchScan

# settings for launchScan:
MR_settings = {
    'TR': 2.000,     # duration (sec) per whole-brain volume
    'volumes': 5,    # number of whole-brain 3D volumes per scanning run
    'sync': 'slash', # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 0,       # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    'sound': True    # in test mode: play a tone as a reminder of scanner noise
    }
infoDlg = gui.DlgFromDict(MR_settings, title='fMRI parameters', order=['TR', 'volumes'])
if not infoDlg.OK:
    core.quit()

win = visual.Window(fullscr=False)
globalClock = core.Clock()

# summary of run timing, for each key press:
output = u'vol    onset key\n'
for i in range(-1 * MR_settings['skip'], 0):
    output += u'%d prescan skip (no sync)\n' % i

counter = visual.TextStim(win, height=.05, pos=(0, 0), color=win.rgb + 0.5)
output += u"  0    0.000 sync  [Start of scanning run, vol 0]\n"

# launch: operator selects Scan or Test (emulate); see API documentation
vol = launchScan(win, MR_settings, globalClock=globalClock)
counter.setText(u"%d volumes\n%.3f seconds" % (0, 0.0))
counter.draw()
win.flip()

duration = MR_settings['volumes'] * MR_settings['TR']
# note: globalClock has been reset to 0.0 by launchScan()
while globalClock.getTime() < duration:
    allKeys = event.getKeys()
    for key in allKeys:
        if key == MR_settings['sync']:
            onset = globalClock.getTime()
            # do your experiment code at this point if you want it sync'd to the TR
            # for demo just display a counter & time, updated at the start of each TR
            counter.setText(u"%d volumes\n%.3f seconds" % (vol, onset))
            output += u"%3d  %7.3f sync\n" % (vol, onset)
            counter.draw()
            win.flip()
            vol += 1
        else:
            # handle keys (many fiber-optic buttons become key-board key-presses)
            output += u"%3d  %7.3f %s\n" % (vol-1, globalClock.getTime(), str(key))
            if key == 'escape':
                output += u'user cancel, '
                break

t = globalClock.getTime()
win.flip()

output += u"End of scan (vol 0..%d = %d of %s). Total duration = %7.3f sec" % (vol - 1, vol, MR_settings['volumes'], t)
print(output)

win.close()
core.quit()

# The contents of this file are in the public domain.
