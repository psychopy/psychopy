"""Tests for psychopy.hardware.emulator"""
import os, sys

from psychopy import visual, core
from psychopy.hardware.emulator import *

BASE_MR_SETTINGS = {
    'TR': 1.000,    # duration (sec) per volume
    'volumes': 3,   # number of whole-brain 3D volumes / frames
    # 'sync': '5',  # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 0       # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    }

class _baseEmulatorTest:
    '''A base class to test launchScan with different MR_settings'''
    def setup(self):
        self.win = visual.Window(fullscr=False)
        self.globalClock = core.Clock()

    def test_launch_scan(self):
        '''Test that launchScan successfully adds sync keys to the buffer.'''
        win = self.win
        globalClock = self.globalClock
        MR_settings = self.MR_settings

        # Initialize onsets with 0; the first onset is used to 0 the clock and is not reported by launchScan
        onsets = [0.0]
        sync_key = MR_settings['sync']

        # Call launchScan with MR Settings from test classes, in 'Test' mode with a short timeout.
        vol = launchScan(win, MR_settings, globalClock=globalClock, mode='Test', wait_timeout= 5)

        duration = MR_settings['volumes'] * MR_settings['TR']
        while globalClock.getTime() < duration:
            allKeys = event.getKeys(timeStamped=True)
            # detect sync or infer it should have happened:
            for key_tuple in allKeys:
                if key_tuple[0] == sync_key:
                    vol += 1
                    onsets.append(key_tuple[1])
        assert vol == MR_settings['volumes'] == len(onsets)

    def test_wait_timeout_type(self):
        '''Ensure that the wait_timeout happily rejects bad values.'''
        win = self.win
        MR_settings = self.MR_settings
        try:
            vol = launchScan(win, MR_settings, wait_timeout = 'cant_coerce_me!', mode='Test')
        except StandardError as e:
            assert e.__class__ == ValueError

class TestShortSync(_baseEmulatorTest):
    '''Test MR settings where the sync key is of length 1 (eg '5').'''
    def setup_class(self):
        MR_settings = BASE_MR_SETTINGS.copy()
        MR_settings.update({'sync': '5'})
        self.MR_settings = MR_settings

class TestLongSync(_baseEmulatorTest):
    '''Test MR settings where the sync key is a 'named' key (eg 'equal').'''
    def setup_class(self):
        MR_settings = BASE_MR_SETTINGS.copy()
        MR_settings.update({'sync': 'equal'})
        self.MR_settings = MR_settings
