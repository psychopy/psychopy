# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.versionchooser"""
from builtins import object
import os
from psychopy.tools.versionchooser import useVersion
import psychopy

class _baseVersionChooser(object):
    def test_currentVersion():
        vers = useVersion(requested)
        assert vers == requested

class _testSameVersion(_baseVersionChooser):
    def setup(self):
        requested = psychopy.__version__

class _testOlderVersion(_baseVersionChooser):
    def setup(self):
        requested = '1.80.02'

"""
TODO: Tests to write:

* Fail if git isn't there
* Fail if git can't download repo

"""
