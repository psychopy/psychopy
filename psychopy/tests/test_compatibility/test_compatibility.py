# -*- coding: utf-8 -*-
"""Tests for psychopy.compatibility"""

import os
from psychopy import constants, compatibility
import pytest

pytest.mark.skip()  # previously skipped only if on Py2: this doesn't run on Py3

thisPath = os.path.split(__file__)[0]
fixtures_path = os.path.join(thisPath, '..', 'data')

class _baseCompatibilityTest():
    def test_FromFile(self):
        dat = compatibility.fromFile(self.test_psydat)


class TestOldTrialHandler(_baseCompatibilityTest):
    """Test Old Trial Handler"""
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"


class TestNewTrialHandler(_baseCompatibilityTest):
    """Test New-styel Trial Handler"""
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"


class TestOldStairHandler(_baseCompatibilityTest):
    """Test Old Trial Handler"""
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle_stair.psydat')
        self.test_class = "<class 'psychopy.data.StairHandler'>"
