# -*- coding: utf-8 -*-
"""
Tests for psychopy.tools.filetools

"""
from builtins import zip
from builtins import object
import shutil
from tempfile import mkdtemp
import os
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
        self.f = None

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def teardown_method(self, method):
        self.f.close()

    def test_default_parameters(self):
        self.f = openOutputFile(self.baseFileName)
        assert self.f.encoding == 'utf-8'
        assert self.f.closed is False
        assert self.f.stream.mode == 'wb'

    def test_append(self):
        self.f = openOutputFile(self.baseFileName, append=True)
        assert self.f.encoding == 'utf-8'
        assert self.f.closed is False
        assert self.f.stream.mode == 'a'


if __name__ == '__main__':
    import pytest
    pytest.main()
