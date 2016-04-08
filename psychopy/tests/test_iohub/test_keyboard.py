""" Test starting and stopping iohub server
"""
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess
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

        iohub_config = {}
        # Uncomment config to use iosync keyboard to test
        # iohub keyboard device. An ioSync device must be connected to
        # a USB 2.0 port on the computer running the tests.

        cls.io = startHubProcess(iohub_config)
        cls.keyboard = cls.io.devices.keyboard
        cls.iosync = None

        if 'mcu.iosync.MCU' in iohub_config.keys():
            iosync = cls.io.getDevice('mcu')
            cls.iosync = iosync

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        stopHubProcess()
        cls.io = None
        cls.keyboard = None
        cls.iosync = None

    def test_getEvents(self):
        evts = self.keyboard.getEvents()
        assert isinstance(evts, (list, tuple))

    def test_getKeys(self):
        # getKeys(self, keys=None, chars=None, mods=None, duration=None,
        #         etype = None, clear = True)
        if self.iosync:
            self.io.clearEvents()
            self.iosync.generateKeyboardEvent('a', [], 0.2)
            self.io.wait(0.3)
            kb_events = self.keyboard.getKeys()

            assert len(kb_events)==2
            assert kb_events[0].type == 'KEYBOARD_PRESS'
            assert kb_events[1].type == 'KEYBOARD_RELEASE'

            kp = kb_events[0]
            kr = kb_events[1]

            assert kp.key == 'a'
            assert kr.key == 'a'
            assert kp.char == u'a'
            assert kr.char == u'a'
            assert kp.time < kr.time

            dt = kr.time - kp.time
            assert 0.195 < dt < 0.205
            assert 0.195 < kr.duration < 0.205
            assert dt - kr.duration == 0.0

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


