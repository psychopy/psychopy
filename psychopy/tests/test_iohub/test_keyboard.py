""" Test ioHub Keyboard Device & Events
"""
from copy import copy

from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, getTime
import logging

@skip_under_travis
class TestKeyboard(object):
    """
    Keyboard Device tests. Starts iohub server, runs test set, then
    stops iohub server.

    Since there is no way to currently automate keyboard event generation in
    a way that would actually test the iohub keyboard event processing logic,
    each test simply calls one of the device methods / properties and checks
    that the return type is as expected.

    Each method is called with no args; that should be improved.
    """

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """

        # iohub_config = {}
        # Uncomment config to use iosync keyboard to test
        # iohub keyboard device. An ioSync device must be connected to
        # a USB 2.0 port on the computer running the tests.
        iohub_config = {'mcu.iosync.MCU': dict(serial_port='auto',
                                               monitor_event_types=[]
                                               )
                        }

        cls.io = startHubProcess(iohub_config)
        cls.keyboard = cls.io.devices.keyboard
        cls.iosync = cls.io.getDevice('mcu')
        assert cls.iosync is not None
        if cls.iosync and not cls.iosync.isConnected():
            #assert iosync is not None, "iosync device requested but devvice is None."
            #assert iosync.isConnected(), "iosync device requested but isConnected() == False"
            cls.iosync = None

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        stopHubProcess()
        cls.io = None
        cls.keyboard = None
        cls.iosync = None

    def get_kb_events(self, kb_get_method, loop_dur, **kbkwargs):
        stime = getTime()
        kb_events = []
        while getTime() - stime < loop_dur:
            kbes = kb_get_method(**kbkwargs)
            if kbes:
                kb_events.extend(kbes)
        return kb_events

    def validate_kb_event(self, kbe, is_press, ekey, echar, emods=[],
                          edur=None, kbpress=None):
        emods = copy(emods)

        if is_press:
            assert kbe.type == 'KEYBOARD_PRESS'
        else:
            assert kbe.type == 'KEYBOARD_RELEASE'

        assert kbe.key == ekey
        assert kbe.char == echar
        assert kbe == ekey and kbe == echar

        kbe_mods = copy(kbe.modifiers)
        if kbe_mods:
            numlock_active = len(kbe_mods) == 1 and kbe_mods[0] == 'numlock'
            if numlock_active and 'numlock' not in emods:
                emods.append('numlock')
        for m in kbe.modifiers:
            try:
                kbe_mods.remove(m)
            except:
                pass
        fail_str_ = "Unexpected modifiers found: {}. KeyboardEvent: {}"
        assert len(kbe_mods) == 0, fail_str_.format(kbe_mods, kbe)

        if kbe.type == 'KEYBOARD_RELEASE':
            dt = None
            if kbpress:
                assert kbpress.id == kbe.pressEventID
                assert kbpress.time < kbe.time
                dt = kbe.time - kbpress.time
                assert dt - kbe.duration == 0.0
            if edur is not None:
                mindur = edur-0.005
                maxdur = edur+0.005
                if dt:
                    assert mindur < dt < maxdur
                assert mindur < kbe.duration < maxdur

    def test_getEvents(self):
        evts = self.keyboard.getEvents()
        assert isinstance(evts, (list, tuple))

    def test_getKeys(self):
        # getKeys(self, keys=None, chars=None, mods=None, duration=None,
        #         etype = None, clear = True)
        if self.iosync:
            self.io.clearEvents()
            self.iosync.generateKeyboardEvent('a', [], 0.2)

            kb_events = self.get_kb_events(self.keyboard.getKeys, 0.3)

            assert len(kb_events) == 2
            kp = kb_events[0]
            kr = kb_events[1]

            self.validate_kb_event(kp, is_press=True, ekey='a', echar=u'a')
            self.validate_kb_event(kr, is_press=False, ekey='a', echar=u'a', edur=0.2, kbpress=kp)



        else:
            evts = self.keyboard.getKeys()
            assert isinstance(evts, (list, tuple))

    def test_getPresses(self):
        # getPresses(self, keys=None, chars=None, mods=None, clear=True)
        evts = self.keyboard.getPresses()
        assert isinstance(evts, (list, tuple))

    def test_getReleases(self):
        # getReleases(self, keys=None, chars=None, mods=None, duration=None,
        #             clear = True)
        evts = self.keyboard.getReleases()
        assert isinstance(evts, (list, tuple))

    def test_waitForKeys(self):
        # waitForKeys(maxWait, keys, chars, mods, duration, etype, clear,
        #             checkInterval)
        evts = self.keyboard.waitForKeys(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_waitForPresses(self):
        # waitForPresses(self, maxWait=None, keys=None, chars=None,
        #                mods = None, duration = None, clear = True,
        #                checkInterval = 0.002)
        evts = self.keyboard.waitForPresses(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_waitForReleases(self):
        # waitForReleases(self, maxWait=None, keys=None, chars=None,
        #                 mods = None, duration = None, clear = True,
        #                 checkInterval = 0.002)
        evts = self.keyboard.waitForReleases(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_clearEvents(self):
        self.keyboard.clearEvents()
        assert len(self.keyboard.getEvents()) == 0

    def test_state(self):
        kbstate = self.keyboard.state
        assert isinstance(kbstate, dict)

    def test_reporting(self):
        assert self.keyboard.reporting is True
        assert self.keyboard.isReportingEvents() is True

        self.keyboard.reporting = False

        assert self.keyboard.reporting is False
        assert self.keyboard.isReportingEvents() is False

        self.keyboard.reporting = True

        assert self.keyboard.reporting is True
        assert self.keyboard.isReportingEvents() is True


