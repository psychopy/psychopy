import os
import sys
import glob
import uuid
from psychopy.monitors.calibTools import Monitor
import numpy as np
import pytest


@pytest.mark.monitors
class TestMonitorCalibration():
    def setup_class(self):
        self.monitor_name = str(uuid.uuid4().hex)  # random monitor name
        if sys.platform == 'win32':
            self.monitor_folder = os.path.join(os.environ['APPDATA'],
                                               'psychopy3', 'monitors')
        else:
            self.monitor_folder = os.path.join(os.environ['HOME'],
                                               '.psychopy3', 'monitors')
        self.fullname = os.path.join(self.monitor_folder, self.monitor_name)
        self.mon = Monitor(self.monitor_name,
                           width=40,
                           distance=57,
                           gamma=1.0,
                           notes='Here are notes')

    def teardown_class(self):
        """Remove leftover monitor calibration files (if they exist)"""
        for f in glob.glob(self.fullname + '.*'):
            os.remove(f)

    def test_save(self):
        """See if the monitor calibration file ended up in the correct
        location"""
        self.mon.save()
        assert os.path.isfile(self.fullname + '.json')

    def test_saveMon(self):
        """See if the monitor calibration file ended up in the correct
        location"""
        self.mon.save()
        assert os.path.isfile(self.fullname + '.json')

    def test_reload_monitor(self):
        """Reload the monitor and verify that all elements in each object
        match"""
        mon2 = Monitor(self.monitor_name)
        # test that all values in the reloaded monitor match the original
        # instance
        for key1 in self.mon.calibs.keys():
            for key2 in self.mon.calibs[key1].keys():
                if isinstance(self.mon.calibs[key1][key2],
                              (np.ndarray, np.generic)):
                    assert (self.mon.calibs[key1][key2] ==
                            mon2.calibs[key1][key2]).all()
                else:
                    assert (self.mon.calibs[key1][key2] ==
                            mon2.calibs[key1][key2])


@pytest.mark.monitors
def test_linearizeLums_method_1():
    m = Monitor(name='foo')
    m.currentCalib['gamma'] = 1
    m.currentCalib['linearizeMethod'] = 1

    desired_lums = np.array([0.1, 0.2, 0.3])

    r = m.linearizeLums(desiredLums=desired_lums)
    assert np.allclose(r, desired_lums)


@pytest.mark.monitors
def test_lineariseLums_method_1():
    m = Monitor(name='foo')
    m.currentCalib['gamma'] = 1
    m.currentCalib['linearizeMethod'] = 1

    desired_lums = np.array([0.1, 0.2, 0.3])

    # American spelling
    r = m.linearizeLums(desiredLums=desired_lums)
    assert np.allclose(r, desired_lums)

    # British spelling
    r = m.lineariseLums(desiredLums=desired_lums)
    assert np.allclose(r, desired_lums)


if __name__ == '__main__':
    pytest.main()
