# -*- coding: utf-8 -*-
"""
Tests for psychopy.tools.filetools

"""
from builtins import zip
from builtins import object
import shutil
from tempfile import mkdtemp
from os.path import join as pjoin
from psychopy.tools.filetools import genDelimiter, handleFileCollision, \
                                     openOutputFile


def test_genDelimiter():
    baseName = 'testfile'
    extensions = ['.csv', '.CSV', '.tsv', '.txt', '.unknown', '']
    correctDelimiters = [',', ',', '\t', '\t', '\t', '\t']

    for extension, correctDelimiter in zip(extensions, correctDelimiters):
        fileName = baseName + extension
        delimiter = genDelimiter(fileName)
        assert delimiter == correctDelimiter


class TestOpenOutputFile(object):
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'
        self.baseFileName = pjoin(self.temp_dir, self.rootName)
        self.f = None

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def teardown_method(self, method):
        self.f.close()

    def test_default_parameters(self):
        self.f = openOutputFile(self.baseFileName)

    def test_append(self):
        self.f = openOutputFile(self.baseFileName, append=True)

    def test_delim_comma(self):
        self.f = openOutputFile(self.baseFileName, delim=',')

    def test_delim_tab(self):
        self.f = openOutputFile(self.baseFileName, delim='\t')

    def test_delim_delim_empty(self):
        self.f = openOutputFile(self.baseFileName, delim='')

    def test_append_and_delim(self):
        self.f = openOutputFile(self.baseFileName, append=True,
                                delim=',')

if __name__=='__main__':
    import pytest
    pytest.main()
