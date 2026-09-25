from psychopy.hardware import parallel


class _TestParallelBackend(parallel._BaseParallelBackend):
    def __init__(self, address):
        parallel._BaseParallelBackend.__init__(self, address=address)
        # use an arbitrary attribute to simulate the pin values
        self.data = int("0000000000000", 2)

    def setData(self, data):
        self.data = data

    def readData(self):
        return self.data


class TestParallelDevice:
    def setup_class(cls):
        # replace all parallel backends with a dummy class for testing
        parallel._LinuxParallelBackend = _TestParallelBackend
        parallel._DLPortIOParallelBackend = _TestParallelBackend
        parallel._InpOutParallelBackend = _TestParallelBackend

    def test_getset_pins(self):
        # make a parallel device
        obj = parallel.ParallelDevice("test")
        # for each pin...
        for i in range(2, 9):
            # try setting to True or False
            for value in (True, False):
                # set value
                obj.setPin(i, value)
                # check value
                assert obj.getPin(i) == value
