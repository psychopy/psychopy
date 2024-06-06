import sys
from psychopy.hardware import keyboard
import pytest
import time
from psychopy import logging


class _TestBaseKeyboard:
    """
    Tests for the general functionality which should exist across Keyboard backends.
    """
    def testReceiveGeneratedKeypress(self):
        """
        Test that `KeyboardDevice.receiveMessage` can receive and interpret a KeyPress object
        correctly, even when that object isn't linked to a physical keypress.
        """
        # list of events to fake, time to fake them and state of getKeys outputs afterwards
        cases = [
            {'val': "a", 't': 0.1, 'len': 1},
            {'val': "b", 't': 0.2, 'len': 1},
        ]
        for case in cases:
            evt = self.kb.makeResponse(tDown=case['t'], code=case['val'])
            keys = self.kb.getKeys(waitRelease=False, clear=True)
            assert len(keys) == case['len']
            assert keys[-1] is evt
            assert keys[-1].value == case['val']

    def testAcceptDuplicateResponses(self):
        """
        Test that KeyboardDevice can receive multiple presses of the same key without accepting
        genuine duplicates (e.g. KeyPress objects added twice, or the same object added for press
        and release)
        """
        # clear
        self.kb.clearEvents()
        # press space twice and don't release
        resp1 = self.kb.makeResponse(tDown=0.1, code="space")
        resp2 = self.kb.makeResponse(tDown=0.2, code="space")
        # make sure we only have 2 press objects
        keys = self.kb.getKeys(waitRelease=False, clear=False)
        assert len(keys) == 2
        # simulate a release
        resp1.duration = 0.2
        resp2.duration = 0.1
        self.kb.responses += [resp1, resp2]
        # we should still only have 2 press objects (as these are duplicates)
        keys = self.kb.getKeys(waitRelease=True, clear=False)
        assert len(keys) == 2
        # add the same objects again for no good reason
        self.kb.responses += [resp1, resp2]
        # we should STILL only have 2 press objects
        keys = self.kb.getKeys(waitRelease=True, clear=False)
        assert len(keys) == 2

    def testMuteOutsidePsychopyNotSlower(self):
        """
        Test that responses aren't worryingly slower when using muteOutsidePsychopy
        """
        # skip this test on Linux (as MOP *is* slower due to having to use subprocess)
        if sys.platform == "linux":
            pytest.skip()

        # array to store times
        times = {}
        # number of responses to make
        nResps = 10000

        for mop in (True, False):
            # make new keyboard with muteOutsidePsychopy set as desired
            self.kb.muteOutsidePsychopy = mop
            # start timer
            start = time.time()
            # make 10000 responses
            for n in range(nResps):
                self.kb.makeResponse(
                    code="a", tDown=0
                )
            # get time
            times[mop] = time.time() - start

        # work out average difference per-response
        avg = (times[True] - times[False]) / nResps
        # make sure average difference will still be less than a frame on high performance monitors
        assert avg < 1/240

    def teardown_method(self):
        # clear any keypresses
        self.kb.getKeys(clear=True)
        # set mute outside psychopy back to False
        self.kb.muteOutsidePsychopy = False


class _MillikeyMixin:
    """
    Mixin to add tests which use a Millikey device to generate keypresses. If no such device is
    connected, these tests will all skip.
    """
    # this attribute should be overwritten when setup_class is called
    millikey = None

    def setup_class(self):
        """
        Create a serial object to interface with a Millikey device,
        """
        from psychopy.hardware.serialdevice import SerialDevice
        from psychopy.tools import systemtools as st

        # systemtools only works on Windows so skip millikey-dependent tests on other OS's
        if sys.platform != "win32":
            return

        # use systemtools to find millikey port
        for profile in st.systemProfilerWindowsOS(classname="Ports", connected=True):
            # identify by driver name
            if "usbser.inf" not in profile['Driver Name']:
                continue
            # find "COM" in profile description
            desc = profile['Device Description']
            start = desc.find("COM") + 3
            end = desc.find(")", start)
            # if there's no reference to a COM port, skip
            if -1 in (start, end):
                continue
            # get COM port number
            num = desc[start:end]
            # if we've got this far, create device
            self.millikey = SerialDevice(f"COM{num}", baudrate=128000)
            # stop looking once we've got one
            break

    def teardown_class(self):
        """
        Close Millikey before finishing tests.
        """
        if self.millikey is not None:
            self.millikey.close()

    def assertMillikey(self):
        """
        Make sure a Millikey device is connected (and skip the current test if not)
        """
        # if we didn't find a device, skip current test
        if self.millikey is None:
            pytest.skip()

    def makeMillikeyKeypress(self, key, duration, delay=0):
        """
        Send a trigger to the Millikey device telling to to press a particular key.

        Parameters
        ----------
        key : str
            Key to press
        duration : int
            Duration (ms) of the keypress
        delay : int
            Delay (ms) before making the keypress
        """
        # make sure we have a millikey device
        self.assertMillikey()
        # construct command (see https://blog.labhackers.com/?p=285)
        cmd = "KGEN {} {} {}".format(key, duration, delay)
        # send
        self.millikey.sendMessage(cmd)
        # read any resp1
        return self.millikey.getResponse()

    def testReceivePhysicalKeypress(self):
        """
        Test that physical keypresses are detected.

        Requires a Millikey device to run.
        """
        self.makeMillikeyKeypress(key="a", duration=10, delay=10)
        # get last message
        resp = self.kb.getKeys()[-1]
        # check whether the created press was received
        assert resp.name == "a"

    def testPhysicalKeypressTiming(self):
        """
        Test that timing (tDown, rt, etc.) on KeyPress objects received via a physical key press
        are correct.

        Requires a Millikey device to run.
        """
        # define tolerance (ms) for this test
        tolerance = 4
        # try a few times to make sure times aren't cumulative
        for ans, dur, rt in [
            ("a", 123, 456),
            ("b", 456, 123),
            ("c", 123, 123),
            ("d", 456, 456),
        ]:
            # reset keyboard clock
            self.kb.clock.reset()
            # wait for rt
            time.sleep(rt / 1000)
            # store start time
            start = logging.defaultClock.getTime()
            # make a keypress
            self.makeMillikeyKeypress(key=ans, duration=dur)
            # wait for press to finish
            time.sleep(dur / 500)
            # get last message
            resp = self.kb.getKeys()[-1]
            # check correct key
            assert resp.name == ans
            # check correct rt
            assert abs(resp.rt - rt / 1000) <= tolerance / 1000
            # check correct duration
            assert abs(resp.duration - dur / 1000) <= tolerance / 1000
            # check correct start time
            assert abs(resp.tDown - start) <= tolerance / 1000


class TestIohubKeyboard(_TestBaseKeyboard, _MillikeyMixin):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="iohub", muteOutsidePsychopy=False)


class TestPtbKeyboard(_TestBaseKeyboard, _MillikeyMixin):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="ptb", muteOutsidePsychopy=False)

    def teardown_method(self):
        self.kb.getKeys(clear=True)


class TestEventKeyboard(_TestBaseKeyboard, _MillikeyMixin):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="event", muteOutsidePsychopy=False)

    def teardown_method(self):
        self.kb.getKeys(clear=True)
