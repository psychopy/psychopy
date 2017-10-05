from psychopy.monitors.calibTools import Monitor
import pytest


@pytest.mark.monitors
class TestMonitorCalibration(object):
    def setup(self):
        pass

    def teardown(self):
        pass

    def test_reload_monitor(self):
        self.mon = Monitor('test',
                           width=40,
                           distance=57,
                           gamma=1.0,
                           notes='Here are notes')
        self.mon.saveMon()
        self.mon2 = Monitor('test')
        assert all([[self.mon.calibs[key][key2] is self.mon2.calibs[key][key2]
                     for key2 in self.mon.calibs[key]]
                    for key in self.mon.calibs])


if __name__ == '__main__':
    cls = TestMonitorCalibration()
    cls.setup()
    cls.test_reload_monitor()
    cls.teardown()
