"""Tests for psychopy.data.DataHandler"""
import os
import shutil
import tempfile

from psychopy import data


class TestTrialHandler:
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp('psychopy_testtrialhandler')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names(self):
        trials = data.TrialHandler([], 1)
        trials.data.addDataType('with_underscore')
        base_data_filename = os.path.join(self.temp_dir, 'test_data_file')
        trials.saveAsText(base_data_filename, delim=',')

        # Make sure the file is there
        data_filename = base_data_filename + '.dlm'
        assert os.path.exists(data_filename)

        # Make sure the header line is correct
        f = open(data_filename, 'rb')
        header = f.readline()
        f.close()
        expected_header = "n,with_underscore_mean,with_underscore_raw,with_underscore_std," +os.linesep
        if expected_header != header:
            print expected_header,type(expected_header),len(expected_header)
            print header, type(header), len(header)
        assert expected_header == unicode(header)
