#!/usr/bin/env python2

"""This demo illustrates using hardware.emulator.launchScan() to either start a
real scan, or emulate sync pulses. Emulation is to allow debugging script timing
offline, without requiring a scanner (or a hardware sync pulse generator).
"""

# Author: Jeremy R. Gray

from psychopy import visual, event, core, gui
from psychopy.hardware.emulator import launchScan

# settings for launchScan:
MR_settings = { 
    'TR': 2.000, # duration (sec) per volume
    'volumes': 5, # number of whole-brain 3D volumes / frames
    'sync': '5', # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 0, # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    'sound': True # in test mode only, play a tone as a reminder of scanner noise
    }
infoDlg = gui.DlgFromDict(MR_settings, title='fMRI parameters', order=['TR','volumes'])
if not infoDlg.OK: core.quit()

win = visual.Window(fullscr=False)
globalClock = core.Clock()

# summary of run timing, for each key press:
output = u'vol    onset key\n'
for i in range(-1 * MR_settings['skip'], 0):
    output += u'%d prescan skip (no sync)\n' % i

key_code = MR_settings['sync']
counter = visual.TextStim(win, height=.05, pos=(0,0), color=win.rgb+0.5)
output += u"  0    0.000 %s  [Start of scanning run, vol 0]\n" % key_code
sync_now = False

# launch: operator selects Scan or Test (emulate); see API docuwmentation
vol = launchScan(win, MR_settings, globalClock=globalClock)

infer_missed_sync = False # best if your script timing works without this, but this might be useful sometimes
max_slippage = 0.02 # how long to allow before treating a "slow" sync as missed
    # any slippage is almost certainly due to timing issues with your script or PC, and not MR scanner

duration = MR_settings['volumes'] * MR_settings['TR']
# note: globalClock has been reset to 0.0 by launchScan()
while globalClock.getTime() < duration:
    allKeys = event.getKeys()
    for key in allKeys:
        if key != MR_settings['sync']:
            output += u"%3d  %7.3f %s\n" % (vol-1, globalClock.getTime(), unicode(key))
    if 'escape' in allKeys:
        output += u'user cancel, '
        break
    # detect sync or infer it should have happened:
    if MR_settings['sync'] in allKeys:
        sync_now = key_code # flag
        onset = globalClock.getTime()
    if infer_missed_sync:
        expected_onset = vol * MR_settings['TR']
        now = globalClock.getTime()
        if now > expected_onset + max_slippage:
            sync_now = u'(inferred onset)' # flag
            onset = expected_onset
    if sync_now:
        # do your experiment code at this point; for demo, just shows a counter & time
        counter.setText(u"%d volumes\n%.3f seconds" % (vol, onset))
        output += u"%3d  %7.3f %s\n" % (vol, onset, sync_now)
        counter.draw()
        win.flip()
        vol += 1
        sync_now = False

output += u"End of scan (vol 0..%d = %d of %s). Total duration = %7.3f sec" % (vol - 1, vol, MR_settings['volumes'], globalClock.getTime())
print output
core.quit()
