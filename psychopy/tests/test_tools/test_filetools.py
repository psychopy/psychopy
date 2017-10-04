# -*- coding: utf-8 -*-
"""
Tests for psychopy.tools.filetools

"""
import shutil
import os
import sys
import json
import pickle
import pytest

from builtins import zip
from builtins import object
from tempfile import mkdtemp, mkstemp
from psychopy.tools.filetools import (genDelimiter, genFilenameFromDelimiter,
                                      openOutputFile)
from psychopy.constants import PY3


def test_genDelimiter():
    baseName = 'testfile'
    extensions = ['.csv', '.CSV', '.tsv', '.txt', '.unknown', '']
    correctDelimiters = [',', ',', '\t', '\t', '\t', '\t']

    for extension, correctDelimiter in zip(extensions, correctDelimiters):
        fileName = baseName + extension
        delimiter = genDelimiter(fileName)
        assert delimiter == correctDelimiter


def test_genFilenameFromDelimiter():
    base_name = 'testfile'
    delims = [',', '\t', None]
    correct_extensions = ['.csv', '.tsv', '.txt']

    for delim, correct_extension in zip(delims, correct_extensions):
        filename = genFilenameFromDelimiter(base_name, delim)
        extension = os.path.splitext(filename)[1]
        assert extension == correct_extension


class TestOpenOutputFile(object):
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'
        self.baseFileName = os.path.join(self.temp_dir, self.rootName)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_default_parameters(self):
        f = openOutputFile(self.baseFileName)
        assert f.encoding == 'utf-8'
        assert f.closed is False
        assert f.stream.mode == 'wb'
        f.close()

    def test_append(self):
        f = openOutputFile(self.baseFileName, append=True)
        assert f.encoding == 'utf-8'
        assert f.closed is False
        assert f.stream.mode == 'ab'
        f.close()

    def test_stdout(self):
        f = openOutputFile(None)
        assert f is sys.stdout

        f = openOutputFile('stdout')
        assert f is sys.stdout


class TestFromFile(object):
    def setup(self):
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-%s' %
                                      type(self).__name__)

    def teardown(self):
        shutil.rmtree(self.tmp_dir)

    def test_text(self):
        _, path = mkstemp(dir=self.tmp_dir, suffix='.txt')

        test_data = 'Test'
        with open(path, 'w') as f:
            f.write(test_data)

        with open(path, 'r') as f:
            loaded_data = f.read()

        assert test_data == loaded_data

    def test_json(self):
        _, path = mkstemp(dir=self.tmp_dir, suffix='.json')

        test_data = 'Test'
        with open(path, 'w') as f:
            json.dump(test_data, f)

        with open(path, 'r') as f:
            loaded_data = json.load(f)

        assert test_data == loaded_data

    def test_pickle(self):
        _, path = mkstemp(dir=self.tmp_dir, suffix='.psydat')

        test_data = 'Test'
        with open(path, 'wb') as f:
            pickle.dump(test_data, f)

        with open(path, 'rb') as f:
            loaded_data = pickle.load(f)

        assert test_data == loaded_data

    def test_cPickle(self):
        if PY3:
            pytest.skip('Skipping cPickle test on Python 3')
        else:
            import cPickle

        _, path = mkstemp(dir=self.tmp_dir, suffix='.psydat')

        test_data = 'Test'
        with open(path, 'wb') as f:
            cPickle.dump(test_data, f)

        with open(path, 'rb') as f:
            loaded_data = cPickle.load(f)

        assert test_data == loaded_data


if __name__ == '__main__':
    pytest.main()
