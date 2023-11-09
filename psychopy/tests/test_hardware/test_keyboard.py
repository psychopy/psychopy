from psychopy.hardware import keyboard


class TestKeyboard:
    def testReceiveMessage(self):
        # list of events to fake, time to fake them and state of getKeys outputs afterwards
        cases = [
            {'val': "a", 't': 0.1, 'len': 1},
            {'val': "b", 't': 0.2, 'len': 1},
        ]
        for case in cases:
            evt = keyboard.KeyPress(tDown=case['t'], code=case['val'])
            self.kb.receiveMessage(evt)
            keys = self.kb.getKeys(waitRelease=False, clear=True)
            assert len(keys) == case['len']
            assert keys[-1] is evt
            assert keys[-1].value == case['val']


class TestIohubKeyboard(TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="iohub")


class TestPtbKeyboard(TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="ptb")


class TestEventKeyboard(TestKeyboard):
    def setup_method(self):
        self.kb = keyboard.KeyboardDevice(backend="event")
