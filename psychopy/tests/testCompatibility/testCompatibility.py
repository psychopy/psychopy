# -*- coding: utf-8 -*-
"""Tests for psychopy.compatibility"""
import os
from psychopy import compatibility

class testCompatibility(object):
    def setup(self):
        self.oldPsydat = os.path.join('../data/oldstyle.psydat')
        self.newPsydat = os.path.join('../data/newstyle.psydat')
    
    def testOldTrialHandler(self):
        dat = compatibility.fromFile(self.oldPsydat)
        dat.__class__ == 'psychopy.TrialHandler'
        
    def testNewTrialHandler(self):
        dat = compatibility.fromFile(self.newPsydat)
        dat.__class__ == 'psychopy.TrialHandler'
