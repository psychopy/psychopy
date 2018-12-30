# -*- coding: utf-8 -*-
"""
Tests for psychopy.tools.filetools

"""
import shutil
import os
import sys
import json
import pickle
import codecs
import pytest

from builtins import zip
from builtins import object
from tempfile import mkdtemp, mkstemp
from psychopy.tools.filetools import (genDelimiter, genFilenameFromDelimiter,
                                      openOutputFile, fromFile)
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
        with openOutputFile(self.baseFileName) as f:
            assert f.encoding == 'utf-8-sig'
            assert f.closed is False
            assert f.stream.mode == 'wb'

    def test_append(self):
        with openOutputFile(self.baseFileName, append=True) as f:
            assert f.encoding == 'utf-8-sig'
            assert f.closed is False
            assert f.stream.mode == 'ab'

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

    def test_json_with_encoding(self):
        _, path_0 = mkstemp(dir=self.tmp_dir, suffix='.json')
        _, path_1 = mkstemp(dir=self.tmp_dir, suffix='.json')
        encoding_0 = 'utf-8'
        encoding_1 = 'utf-8-sig'

        test_data = 'Test'

        if PY3:
            with open(path_0, 'w', encoding=encoding_0) as f:
                json.dump(test_data, f)
            with open(path_1, 'w', encoding=encoding_1) as f:
                json.dump(test_data, f)
        else:
            with codecs.open(path_0, 'w', encoding=encoding_0) as f:
                json.dump(test_data, f)
            with codecs.open(path_1, 'w', encoding=encoding_1) as f:
                json.dump(test_data, f)

        assert test_data == fromFile(path_0, encoding=encoding_0)
        assert test_data == fromFile(path_1, encoding=encoding_1)

    def test_pickle(self):
        _, path = mkstemp(dir=self.tmp_dir, suffix='.psydat')

        test_data = 'Test'
        with open(path, 'wb') as f:
            pickle.dump(test_data, f)

        assert test_data == fromFile(path)

    def test_cPickle(self):
        if PY3:
            pytest.skip('Skipping cPickle test on Python 3')
        else:
            import cPickle

        _, path = mkstemp(dir=self.tmp_dir, suffix='.psydat')

        test_data = 'Test'
        with open(path, 'wb') as f:
            cPickle.dump(test_data, f)

        assert test_data == fromFile(path)


if __name__ == '__main__':
    pytest.main()
