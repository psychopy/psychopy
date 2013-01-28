#!/usr/bin/env python

"""This demo illustrates using hardware.emulator.launchScan() to either start a real scan, 
or emulate sync pulses and user responses. Emulation is to allow debugging script timing
offline, without requiring either a scanner or a hardware sync pulse emulator.
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

win = visual.Window(fullscr=True)
globalClock = core.Clock()

# summary of run timing, for each key press:
output = 'vol    onset key\n'
for i in range(-1 * MR_settings['skip'], 0):
    output += '%d prescan skip (no sync)\n' % i

key_code = MR_settings['sync']
counter = visual.TextStim(win, height=.05, pos=(0,0), color=win.rgb+0.5)
output += "  0    0.000 %s start of scanning run, vol 0\n" % key_code
pause_during_delay = (MR_settings['TR'] > .4)
sync_now = False

# can simulate user responses, here 3 key presses in order 'a', 'b', 'c' (they get sorted by time):
simResponses = [(0.123, 'a'), (4.789, 'c'), (2.456, 'b')]

# launch: operator selects Scan or Test (emulate); see API documentation
vol = launchScan(win, MR_settings, globalClock=globalClock, simResponses=simResponses)

infer_missed_sync = False # best if your script timing works without this, but this might be useful sometimes
max_slippage = 0.02 # how long to allow before treating a "slow" sync as missed
    # any slippage is almost certainly due to timing issues with your script or PC, and not MR scanner

duration = MR_settings['volumes'] * MR_settings['TR']
# note: globalClock has been reset to 0.0 by launchScan()
while globalClock.getTime() < duration:
    allKeys = event.getKeys()
    for key in allKeys:
        if key != MR_settings['sync']:
            output += "%3d  %7.3f %s\n" % (vol-1, globalClock.getTime(), str(key))
    if 'escape' in allKeys:
        output += 'user cancel, '
        break
    # detect sync or infer it should have happened:
    if MR_settings['sync'] in allKeys:
        sync_now = key_code # flag
        onset = globalClock.getTime()
    if infer_missed_sync:
        expected_onset = vol * MR_settings['TR']
        now = globalClock.getTime()
        if now > expected_onset + max_slippage:
            sync_now = '(inferred onset)' # flag
            onset = expected_onset
    if sync_now:
        # do your experiment code at this point; for demo, just shows a counter & time
        counter.setText("%d volumes\n%.3f seconds" % (vol, onset))
        output += "%3d  %7.3f %s\n" % (vol, onset, sync_now)
        counter.draw()
        win.flip()
        vol += 1
        sync_now = False

output += "end of scan (vol 0..%d = %d of %s). duration = %7.3f" % (vol - 1, vol, MR_settings['volumes'], globalClock.getTime())
print output
print 'For the test, there should be 5 trials (vol 0..4, key 5), with three simulated subject responses (a, b, c)'
core.quit()