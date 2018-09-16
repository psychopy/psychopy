# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.versionchooser"""
from builtins import object
import os
import psychopy
import pytest
from psychopy.tools.versionchooser import useVersion
from psychopy import prefs
from psychopy import constants

USERDIR = prefs.paths['userPrefsDir']
VER_SUBDIR = 'versions'
VERSIONSDIR = os.path.join(USERDIR, VER_SUBDIR)


class _baseVersionChooser(object):
    def test_currentVersion(self):
        vers = useVersion('1.90.0')
        assert(vers == '1.90.0')

    def test_version_folder(self):
        assert(os.path.isdir(VERSIONSDIR))


class Test_Same_Version(_baseVersionChooser):
    def setup(self):
        self.requested = '1.90.0'
        useVersion(self.requested)

    def test_same_version(self):
        assert(psychopy.__version__ == self.requested)


class Test_Older_Version(_baseVersionChooser):
    def setup(self):
        self.requested = '1.90.0'

    def test_older_version(self):
        assert(useVersion(self.requested))


class Test_Incompatible_Version(_baseVersionChooser):
    "Test for incompatibility with PY3"
    def test_raise_error(self):
        if constants.PY3:
            with pytest.raises(RuntimeError):
                useVersion('1.80.0')

    def test_compatible(self):
        assert (useVersion('1.90.0'))



"""

TODO: Tests to write:

* Fail if git isn't there
* Fail if git can't download repo

"""
