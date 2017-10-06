import os
import sys
import glob
import uuid
from psychopy.monitors.calibTools import Monitor
import numpy as np
import pytest


@pytest.mark.monitors
class TestMonitorCalibration(object):
    def setup_class(self):
        self.monitor_name = str(uuid.uuid4().hex)  # generate a random monitor name
        if sys.platform == 'win32':
            self.monitor_folder = os.path.join(os.environ['APPDATA'], 'psychopy2', 'monitors')
        else:
            self.monitor_folder = os.path.join(os.environ['HOME'], '.psychopy2', 'monitors')
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

    def test_save_monitor(self):
        """See if the monitor calibration file ended up in the correct location"""
        self.mon.saveMon()
        assert os.path.isfile(self.fullname + '.json')
        if sys.version_info[0] == 2:
            #  additionally, we should have a .calib file in python 2
            assert os.path.isfile(self.fullname + '.calib')

    def test_reload_monitor(self):
        """Reload the monitor and verify that all elements in each object match"""
        mon2 = Monitor(self.monitor_name)
        # test that all values in the reloaded monitor match the original instance
        for key1 in self.mon.calibs.keys():
            for key2 in self.mon.calibs[key1].keys():
                if isinstance(self.mon.calibs[key1][key2], (np.ndarray, np.generic)):
                    assert (self.mon.calibs[key1][key2] == mon2.calibs[key1][key2]).all()
                else:
                    assert self.mon.calibs[key1][key2] == mon2.calibs[key1][key2]


if __name__ == '__main__':
    pytest.main()
