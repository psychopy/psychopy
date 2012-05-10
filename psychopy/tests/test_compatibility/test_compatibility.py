# -*- coding: utf-8 -*-
"""Tests for psychopy.compatibility"""
import os
from psychopy import compatibility

fixtures_path = '../data/'

class _baseCompatibilityTest(object):
    def test_FromFile(self):
        dat = compatibility.fromFile(self.test_psydat)
        assert str(dat.__class__) == self.test_class

class TestOldTrialHandler(_baseCompatibilityTest):
    '''Test Old Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"

class TestNewTrialHandler(_baseCompatibilityTest):
    '''Test New-styel Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"

class TestOldStairHandler(_baseCompatibilityTest):
    '''Test Old Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle_stair.psydat')
        self.test_class = "<class 'psychopy.data.StairHandler'>"
