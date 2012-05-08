# -*- coding: utf-8 -*-
"""Tests for psychopy.compatibility"""
import os
from psychopy import compatibility

fixtures_path = '../data/'

class _baseCompatibilityTest(object):
    def testFromFile(self):
        dat = compatibility.fromFile(self.test_psydat)
        assert str(dat.__class__) == self.test_class

class testOldTrialHandler(_baseCompatibilityTest):
    '''Test Old Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"

class testNewTrialHandler(_baseCompatibilityTest):
    '''Test New-styel Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle.psydat')
        self.test_class = "<class 'psychopy.data.TrialHandler'>"

class testOldStairHandler(_baseCompatibilityTest):
    '''Test Old Trial Handler'''
    def setup(self):
        self.test_psydat = os.path.join(fixtures_path, 'oldstyle_stair.psydat')
        self.test_class = "<class 'psychopy.data.StairHandler'>"
