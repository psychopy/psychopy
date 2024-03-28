import sys
from psychopy.hardware import keyboard
from pytest import skip
import time


class _TestKeyboard:
    def testMakeAndReceiveMessage(self):
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

    def testMuteOutsidePsychopyNotSlower(self):
        """
        Test that responses aren't worryingly slower when using muteOutsidePsychopy
        """
        # skip this test on Linux (as MOP *is* slower due to having to use subprocess)
        if sys.platform == "linux":
            skip()
        # delete test kb
        backend = self.kb._backend
        del self.kb

        # array to store times
        times = {}
        # number of responses to make
        nResps = 10000

        for mop in (True, False):
            # make new keyboard with muteOutsidePsychopy set as desired
            kb = keyboard.KeyboardDevice(muteOutsidePsychopy=mop)
            # start timer
            start = time.time()
            # make 10000 responses
            for n in range(nResps):
                kb.makeResponse(
                    code="a", tDown=0
                )
            # get time
            times[mop] = time.time() - start
            # delete keyboard
            del kb

        # work out average difference per-response
        avg = (times[True] - times[False]) / nResps
        # make sure average difference will still be less than a frame on high performance monitors
        assert avg < 1/240

        # recreate test kb
        self.kb = keyboard.KeyboardDevice


class TestIohubKeyboard(_TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="iohub", muteOutsidePsychopy=False)


class TestPtbKeyboard(_TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="ptb", muteOutsidePsychopy=False)


class TestEventKeyboard(_TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="event", muteOutsidePsychopy=False)
