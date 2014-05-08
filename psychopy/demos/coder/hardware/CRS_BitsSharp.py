# -*- coding: utf-8 -*-
"""
Created on Thu May  8 10:46:41 2014

@author: jon.peirce
"""

from psychopy import visual, core, event
from psychopy.hardware import crs

bits = crs.BitsSharp()
print bits.getInfo()
print bits.getVideoLine(5,10)
bits.mode = 'bits'
print 'now using', bits.mode
win = visual.Window()
win.flip()

core.wait(2)