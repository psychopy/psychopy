# -*- coding: utf-8 -*-
"""
Tests for psychopy.tools.filetools

"""
import shutil
import os
import sys
from builtins import zip
from builtins import object
from tempfile import mkdtemp
from psychopy.tools.filetools import (genDelimiter, handleFileCollision,
                                      genFilenameFromDelimiter, openOutputFile)


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


if __name__ == '__main__':
    import pytest
    pytest.main()
