""" Test starting and stopping iohub server
"""
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess

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

    Following methods are not yet tested:
            addFilter
            enableFilters
            getConfiguration
            getCurrentDeviceState
            getModifierState
            removeFilter
            resetFilter
            resetState
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
        #iohub_config = {'mcu.iosync.MCU': dict(serial_port='auto',
        #                                       monitor_event_types=[]
        #                                       )
        #                }

        cls.io = startHubProcess(iohub_config)
        cls.keyboard = cls.io.devices.keyboard

        mcu_in_config = 'mcu.iosync.MCU' in iohub_config.keys()

        if mcu_in_config:
            cls.iosync = cls.io.devices.mcu
        else:
            cls.iosync = None

        mcu_exists = mcu_in_config and cls.iosync and cls.iosync.isConnected()
        mcu_disabled = not mcu_in_config and cls.iosync is None

        assert mcu_exists or mcu_disabled

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
        evts = self.keyboard.getKeys()
        assert isinstance(evts, (list, tuple))

    def test_getPresses(self):
        evts = self.keyboard.getPresses()
        assert isinstance(evts, (list, tuple))

    def test_getReleases(self):
        evts = self.keyboard.getReleases()
        assert isinstance(evts, (list, tuple))

    def test_waitForKeys(self):
        evts = self.keyboard.waitForKeys(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_waitForPresses(self):
        evts = self.keyboard.waitForPresses(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_waitForReleases(self):
        evts = self.keyboard.waitForReleases(maxWait=0.05)
        assert isinstance(evts, (list, tuple))

    def test_clearEvents(self):
        self.keyboard.clearEvents()
        assert len(self.keyboard.getEvents()) == 0

    def test_state(self):
        kbstate = self.keyboard.state
        assert isinstance(kbstate, dict)

    def test_reporting(self):
        reporting_state = self.keyboard.reporting
        assert reporting_state is True

        self.keyboard.reporting = False

        assert self.keyboard.isReportingEvents() is False

        self.keyboard.reporting = True
        assert self.keyboard.isReportingEvents() is True


