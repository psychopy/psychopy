"""Tests for psychopy.hardware.emulator"""

# covers most lines of code but does not test all possible logic

# py.test -k emulator --cov-report term-missing --cov hardware/emulator.py tests/test_hardware

import os, sys
import pytest

from psychopy import visual, core, event
from psychopy.hardware import emulator
from psychopy.hardware.emulator import *

# launchScan sound is not tested, nor included coverage

travis = bool("{}".format(os.environ.get('TRAVIS')).lower() == 'true')

BASE_MR_SETTINGS = {
    'TR': 0.5,    # duration (sec) per volume
    'volumes': 3, # number of whole-brain 3D volumes / frames
    'sync': '5',  # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 1     # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    }

@pytest.mark.emulator
class TestLaunchScan():
    '''A base class to test launchScan with different MR_settings'''
    def setup(self):
        self.win = visual.Window(fullscr=False, autoLog=False)
        self.globalClock = core.Clock()
        self.MR_settings = BASE_MR_SETTINGS.copy()

    def test_launch_scan(self):
        '''Test that launchScan successfully adds sync keys to the buffer.'''
        MR_settings = self.MR_settings

        # Initialize onsets with 0; the first onset is used to 0 the clock and is not reported by launchScan
        onsets = [0.0]
        sync_key = MR_settings['sync']

        # Call launchScan with MR Settings from test classes, in 'Test' mode with a short timeout.
        vol = launchScan(self.win, MR_settings, globalClock=self.globalClock,
                         mode='Test', wait_timeout=5, log=False)
        assert 0 < self.globalClock.getTime() < .05  # should get zeroed upon launch

        duration = MR_settings['volumes'] * MR_settings['TR']
        while self.globalClock.getTime() < duration:
            allKeys = event.getKeys(timeStamped=True)
            # detect sync or infer it should have happened:
            for key_tuple in allKeys:
                if key_tuple[0] == sync_key:
                    vol += 1
                    onsets.append(key_tuple[1])
        assert vol == MR_settings['volumes'] == len(onsets)

    def test_no_mode(self):
        #pytest.skip()
        event.clearEvents()
        ResponseEmulator(simResponses=[(0.5, 'escape')]).run()
        vol = launchScan(self.win, BASE_MR_SETTINGS.copy(), globalClock=self.globalClock,
                         wait_timeout=1, log=False)
        # no mode, so a RatingScale will be displayed; return to select value
        # the key event is not being detected here
        core.wait(1, 0)
        #event._onPygletKey(symbol='escape', modifiers=None, emulated=True)
        #core.wait(1, 0)

    def test_sync_generator(self):
        with pytest.raises(ValueError):
            s = SyncGenerator(TR=0.01)
        s = SyncGenerator(TR=0.1)
        s.start()
        s.stop()

    def test_response_emulator(self):
        # logs error but does not raise:
        ResponseEmulator(simResponses=[(.1, 0.123)]).run()

        r = ResponseEmulator()
        r.start()
        r.stop()
        core.wait(.1, 0)

    def test_misc(self):
        if travis:
            pytest.skip()
        MR_settings = BASE_MR_SETTINGS.copy()
        MR_settings.update({'sync': 'equal'})
        vol = launchScan(self.win, MR_settings, globalClock=self.globalClock,
                         simResponses=[(0.1,'a'), (.2, 1)],
                         mode='Test', log=False)
        # test replace missing defaults:
        min_MR_settings = {
            'TR': 0.2,    # duration (sec) per volume
            'volumes': 3}
        vol = launchScan(self.win, min_MR_settings, globalClock=self.globalClock,
                         mode='Test', log=False)
        core.wait(1, 0)


    def test_wait_timeout(self):
        '''Ensure that the wait_timeout happily rejects bad values.'''
        with pytest.raises(RuntimeError):
            vol = launchScan(self.win, BASE_MR_SETTINGS, wait_timeout=.1,
                             mode='Scan', log=False)
        with pytest.raises(ValueError):
            vol = launchScan(self.win, self.MR_settings, wait_timeout='cant_coerce_me!',
                             mode='Test', log=False)
